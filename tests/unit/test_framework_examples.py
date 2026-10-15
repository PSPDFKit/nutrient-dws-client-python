"""Optional-framework smoke tests: real tools, controlled DWS I/O, no model runs."""

import asyncio
import importlib.util
import json
import socket
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

    def reject_network(*args, **kwargs):
        raise AssertionError("Framework smoke tests must not use the network")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    return client, constructor


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
