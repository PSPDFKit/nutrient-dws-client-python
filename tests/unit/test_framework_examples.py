"""Optional-framework smoke tests: real tools, controlled DWS I/O, no model runs."""

import asyncio
import importlib.util
import json
import socket
from ipaddress import ip_address
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import dotenv.main
import pytest

import nutrient_dws

EXAMPLES = Path(__file__).resolve().parents[2] / "examples" / "src"
FRAMEWORKS = {
    "openai_agents": ("agents",),
    "langchain": ("langchain_core", "langchain_openai", "langgraph"),
    "crewai": ("crewai",),
}


def is_local_socket_address(family, address):
    if family == getattr(socket, "AF_UNIX", -1):
        return True
    if family not in (socket.AF_INET, socket.AF_INET6) or not isinstance(
        address, tuple
    ):
        return False
    try:
        return ip_address(address[0]).is_loopback
    except (IndexError, TypeError, ValueError):
        return False


def local_only_connect(original_connect):
    def guarded_connect(connection, address):
        if not is_local_socket_address(connection.family, address):
            raise AssertionError(
                "Framework smoke tests must not use nonlocal connections"
            )
        return original_connect(connection, address)

    return guarded_connect


@pytest.fixture
def example_environment(monkeypatch, tmp_path):
    for key in ("NUTRIENT_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_AGENTS_DISABLE_TRACING", "1")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    monkeypatch.setenv("CREWAI_TELEMETRY_DISABLED", "true")
    monkeypatch.setenv("CREWAI_STORAGE_DIR", str(tmp_path / "crewai"))
    if importlib.util.find_spec("crewai_core") is not None:
        from crewai_core.token_manager import TokenManager

        token_directory = tmp_path / "crewai-tokens"
        token_directory.mkdir(mode=0o700)
        monkeypatch.setattr(
            TokenManager,
            "_get_secure_storage_path",
            staticmethod(lambda: token_directory),
        )
    monkeypatch.setattr(
        dotenv.main, "find_dotenv", lambda *args, **kwargs: str(tmp_path / ".env")
    )
    monkeypatch.chdir(tmp_path)
    client = SimpleNamespace(
        extract_text=AsyncMock(
            return_value={"data": {"pages": [{"plainText": "Owned fixture text"}]}}
        ),
        create_redactions_ai=AsyncMock(
            return_value={
                "buffer": b"%PDF-owned-fixture",
                "mimeType": "application/pdf",
                "filename": "../../untrusted.pdf",
            }
        ),
    )
    constructor = Mock(return_value=client)
    monkeypatch.setattr(nutrient_dws, "NutrientClient", constructor)

    monkeypatch.setattr(
        socket.socket, "connect", local_only_connect(socket.socket.connect)
    )
    return client, constructor


def test_network_guard_allows_socketpair(example_environment):
    left, right = socket.socketpair()
    with left, right:
        left.settimeout(2)
        right.settimeout(2)
        left.sendall(b"owned socketpair")
        assert right.recv(32) == b"owned socketpair"


def test_network_guard_allows_numeric_loopback_pair(example_environment):
    # Exercise the TCP connection used by Windows' socketpair fallback on every OS.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.settimeout(2)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(2)
            client.connect(listener.getsockname())
            peer, _ = listener.accept()
            with peer:
                peer.settimeout(2)
                client.sendall(b"owned loopback")
                assert peer.recv(32) == b"owned loopback"


@pytest.mark.parametrize(
    ("family", "address"),
    [
        (socket.AF_INET, ("192.0.2.1", 443)),
        (socket.AF_INET, ("provider.example", 443)),
        (socket.AF_INET6, ("2001:db8::1", 443, 0, 0)),
    ],
)
def test_network_guard_rejects_nonlocal_without_connecting(family, address):
    original_connect = Mock()
    guarded_connect = local_only_connect(original_connect)
    with pytest.raises(AssertionError, match="nonlocal"):
        guarded_connect(SimpleNamespace(family=family), address)
    original_connect.assert_not_called()


def load_example(framework):
    for dependency in FRAMEWORKS[framework]:
        pytest.importorskip(dependency)
    spec = importlib.util.spec_from_file_location(
        f"framework_{framework}", EXAMPLES / f"framework_{framework}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("framework", FRAMEWORKS)
@pytest.mark.parametrize("missing_key", ["NUTRIENT_API_KEY", "OPENAI_API_KEY"])
def test_missing_keys_fail_before_client_construction(
    framework, missing_key, example_environment, monkeypatch
):
    _, constructor = example_environment
    other_key = (
        "OPENAI_API_KEY" if missing_key == "NUTRIENT_API_KEY" else "NUTRIENT_API_KEY"
    )
    monkeypatch.setenv(other_key, "owned-fixture-key")
    with pytest.raises(SystemExit, match=missing_key):
        load_example(framework)
    constructor.assert_not_called()


@pytest.mark.parametrize("framework", FRAMEWORKS)
def test_dotenv_loaded_before_client_construction(
    framework, example_environment, tmp_path
):
    _, constructor = example_environment
    (tmp_path / ".env").write_text(
        "NUTRIENT_API_KEY=owned-dws-key\nOPENAI_API_KEY=owned-openai-key\n"
    )
    load_example(framework)
    constructor.assert_called_once_with(api_key="owned-dws-key")


@pytest.mark.parametrize("framework", FRAMEWORKS)
async def test_registered_framework_tools_call_dws(
    framework, example_environment, monkeypatch, tmp_path
):
    client, _ = example_environment
    monkeypatch.setenv("NUTRIENT_API_KEY", "owned-dws-key")
    monkeypatch.setenv("OPENAI_API_KEY", "owned-openai-key")
    module = load_example(framework)
    if framework == "openai_agents":
        from agents.tool_context import ToolContext

        registered = module.assistant.tools[0]
        arguments = json.dumps({"input_path": "./assets/sample.pdf"})
        context = ToolContext(
            context=None,
            tool_name=registered.name,
            tool_call_id="owned-fixture-call",
            tool_arguments=arguments,
        )
        result = await registered.on_invoke_tool(context, arguments)
        client.extract_text.assert_awaited_once_with("./assets/sample.pdf")
        assert "Owned fixture text" in result
    elif framework == "langchain":
        result = await module.tool.ainvoke({"path": "./assets/sample.pdf"})
        client.create_redactions_ai.assert_awaited_once_with(
            "./assets/sample.pdf",
            criteria="Redact all email addresses.",
            redaction_state="apply",
        )
        assert (
            tmp_path / "output" / "redacted.pdf"
        ).read_bytes() == b"%PDF-owned-fixture"
        assert "redacted.pdf" in result
        assert "%PDF" not in result
        assert len(result) < 500
        assert not (tmp_path.parent / "untrusted.pdf").exists()
    else:
        registered = module.document_planner.tools[0]
        result = await asyncio.to_thread(
            registered.run, input_path="./assets/sample.pdf"
        )
        assert isinstance(result, str), (
            "CrewAI must resolve the async DWS call, not return a coroutine"
        )
        client.extract_text.assert_awaited_once_with("./assets/sample.pdf")
        assert "Owned fixture text" in result
        assert "./examples/assets/" not in module.plan_task.description
