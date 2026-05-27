"""Unit tests for `NutrientClient.parse()`.

These tests stub `send_request` so they exercise the request-shape and
response-handling logic of `parse()` without making a real HTTP call.
"""

import json
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock, patch

import pytest

from nutrient_dws import (
    APIError,
    AuthenticationError,
    NutrientClient,
    ValidationError,
)
from nutrient_dws.errors import NutrientError
from nutrient_dws.http import prepare_request_body

if TYPE_CHECKING:
    from nutrient_dws import ParseResponse, TableElement
    from nutrient_dws.types.parse import ParseOutputElements, ParseOutputMarkdown


def _make_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "data": payload,
        "status": 200,
        "statusText": "OK",
        "headers": {},
    }


@pytest.fixture
def parse_client() -> NutrientClient:
    return NutrientClient(api_key="pdf_test_unit", base_url="https://api.test.example")


class TestParseRequestShape:
    """Verify the request the client constructs against `/extraction/parse`."""

    @pytest.mark.asyncio
    async def test_default_mode_and_output(
        self, parse_client: NutrientClient, tmp_path
    ) -> None:
        pdf = tmp_path / "sample.pdf"
        pdf.write_bytes(b"%PDF-1.7\n%minimal")

        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(
                {
                    "status": 200,
                    "requestId": "req_default",
                    "output": {"elements": []},
                }
            )

            await parse_client.parse(pdf)

            sent_config = send.call_args[0][0]

        assert sent_config["method"] == "POST"
        assert sent_config["endpoint"] == "/extraction/parse"
        instructions = sent_config["data"]["instructions"]
        assert instructions == {"mode": "structure", "output": {"format": "spatial"}}
        # file field is a (bytes, filename) tuple
        file_part = sent_config["data"]["file"]
        assert isinstance(file_part[0], bytes)
        assert file_part[1] == "sample.pdf"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("mode", "output_format"),
        [
            ("text", "markdown"),
            ("structure", "spatial"),
            ("understand", "spatial"),
            ("agentic", "spatial"),
            ("understand", "markdown"),
        ],
    )
    async def test_mode_and_output_combinations(
        self,
        parse_client: NutrientClient,
        tmp_path,
        mode: str,
        output_format: str,
    ) -> None:
        pdf = tmp_path / "doc.pdf"
        pdf.write_bytes(b"%PDF-1.7\nmini")

        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(
                {"status": 200, "requestId": "r", "output": {"elements": []}}
            )

            await parse_client.parse(pdf, mode=mode, output_format=output_format)

            sent_config = send.call_args[0][0]

        assert sent_config["data"]["instructions"] == {
            "mode": mode,
            "output": {"format": output_format},
        }

    @pytest.mark.asyncio
    async def test_accepts_bytes_input(self, parse_client: NutrientClient) -> None:
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(
                {"status": 200, "requestId": "r", "output": {"markdown": "# Hi"}}
            )

            await parse_client.parse(
                b"%PDF-1.7\nbytes", mode="text", output_format="markdown"
            )

            sent_config = send.call_args[0][0]

        file_part = sent_config["data"]["file"]
        assert file_part[0] == b"%PDF-1.7\nbytes"
        # Anonymous-bytes inputs land with the conventional "document" filename
        assert file_part[1] == "document"

    def test_prepare_request_body_serializes_instructions(self) -> None:
        """`prepare_request_body` must emit `instructions` as a JSON string in
        the multipart form, alongside the file in `files`.
        """
        request_config: dict[str, Any] = {}
        config = {
            "method": "POST",
            "endpoint": "/extraction/parse",
            "data": {
                "file": (b"%PDF-1.7", "doc.pdf"),
                "instructions": {
                    "mode": "agentic",
                    "output": {"format": "spatial"},
                },
            },
            "headers": None,
        }

        prepared = prepare_request_body(request_config, config)  # type: ignore[arg-type]

        assert "files" in prepared
        assert "file" in prepared["files"]
        # Multipart `data` carries the JSON-stringified instructions
        assert json.loads(prepared["data"]["instructions"]) == {
            "mode": "agentic",
            "output": {"format": "spatial"},
        }

    def test_prepare_request_body_omits_instructions_when_absent(self) -> None:
        request_config: dict[str, Any] = {}
        config = {
            "method": "POST",
            "endpoint": "/extraction/parse",
            "data": {"file": (b"%PDF-1.7", "doc.pdf")},
            "headers": None,
        }

        prepared = prepare_request_body(request_config, config)  # type: ignore[arg-type]

        assert "files" in prepared
        # When instructions are omitted, no multipart `data` field is sent
        assert "data" not in prepared


class TestParseResponseHandling:
    """Verify the client returns the raw response envelope to the caller."""

    @pytest.mark.asyncio
    async def test_returns_markdown_envelope(
        self, parse_client: NutrientClient
    ) -> None:
        payload: ParseResponse = {
            "status": 200,
            "requestId": "req_md",
            "output": {"markdown": "# Title\n\nBody."},
            "metrics": {"processingTimeMs": 312, "pagesProcessed": 1},
            "usage": {
                "data_extraction_credits": {"cost": 1, "remainingCredits": 850},
            },
            "configuration": {"mode": "text", "outputFormat": "markdown"},
        }
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(dict(payload))

            response = await parse_client.parse(
                b"%PDF-1.7\nmini", mode="text", output_format="markdown"
            )

        assert response["status"] == 200
        assert response["requestId"] == "req_md"
        markdown_out = cast("ParseOutputMarkdown", response["output"])
        assert markdown_out["markdown"].startswith("# Title")
        assert response["usage"]["data_extraction_credits"]["cost"] == 1

    @pytest.mark.asyncio
    async def test_returns_spatial_envelope_with_discriminated_elements(
        self, parse_client: NutrientClient
    ) -> None:
        payload = {
            "status": 200,
            "requestId": "req_sp",
            "output": {
                "elements": [
                    {
                        "id": "e1",
                        "type": "paragraph",
                        "text": "Hello",
                        "role": "Text",
                        "confidence": 0.95,
                        "readingOrder": 0,
                        "bounds": {"x": 0, "y": 0, "width": 50, "height": 10},
                        "page": {
                            "pageIndex": 0,
                            "pageNumber": "1",
                            "width": 612,
                            "height": 792,
                        },
                    },
                    {
                        "id": "e2",
                        "type": "table",
                        "rowCount": 2,
                        "columnCount": 2,
                        "cells": [
                            {
                                "id": "c1",
                                "row": 0,
                                "column": 0,
                                "rowSpan": 1,
                                "colSpan": 1,
                                "text": "h1",
                            }
                        ],
                        "confidence": 0.9,
                        "readingOrder": 1,
                        "bounds": {"x": 0, "y": 20, "width": 100, "height": 50},
                        "page": {
                            "pageIndex": 0,
                            "pageNumber": "1",
                            "width": 612,
                            "height": 792,
                        },
                    },
                ],
            },
            "metrics": {"processingTimeMs": 4200, "pagesProcessed": 1},
            "usage": {
                "data_extraction_credits": {"cost": 9, "remainingCredits": 991},
            },
            "configuration": {"mode": "understand", "outputFormat": "spatial"},
        }
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(payload)

            response = await parse_client.parse(
                b"%PDF-1.7\nmini", mode="understand"
            )

        spatial_out = cast("ParseOutputElements", response["output"])
        elements = spatial_out["elements"]
        assert len(elements) == 2
        # Discriminated narrowing on the `type` literal
        first, second = elements[0], elements[1]
        assert first["type"] == "paragraph"
        assert second["type"] == "table"
        # second is narrowed to TableElement by the discriminator check above
        table: TableElement = second  # type: ignore[assignment]
        assert table["rowCount"] == 2

    @pytest.mark.asyncio
    async def test_full_extraction_credit_accounting_surface(
        self, parse_client: NutrientClient
    ) -> None:
        """The client must surface the wire's snake_case `data_extraction_credits`
        key verbatim — it's the operator's primary signal that the request was
        billed against extraction credits, not processor credits.
        """
        payload = {
            "status": 200,
            "requestId": "r",
            "output": {"markdown": "x"},
            "usage": {
                "data_extraction_credits": {"cost": 18, "remainingCredits": 100},
            },
        }
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.return_value = _make_response(payload)

            response = await parse_client.parse(b"%PDF-1.7", mode="agentic")

        usage = response["usage"]["data_extraction_credits"]
        assert usage["cost"] == 18
        assert usage["remainingCredits"] == 100


class TestParseErrorPaths:
    """`send_request` raises the same `NutrientError` hierarchy as every other
    endpoint; we just verify the errors propagate out of `parse()` unchanged.
    """

    @pytest.mark.asyncio
    async def test_authentication_error_propagates(
        self, parse_client: NutrientClient
    ) -> None:
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.side_effect = AuthenticationError(
                "Missing, invalid, or expired API token",
                {"requestId": "req_e_401"},
                401,
            )

            with pytest.raises(AuthenticationError) as exc_info:
                await parse_client.parse(b"%PDF-1.7", mode="text")

        assert exc_info.value.status_code == 401
        assert (exc_info.value.details or {}).get("requestId") == "req_e_401"

    @pytest.mark.asyncio
    async def test_validation_error_propagates(
        self, parse_client: NutrientClient
    ) -> None:
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.side_effect = ValidationError(
                "The request is malformed",
                {
                    "requestId": "req_e_400",
                    "errorDetails": {
                        "source": "request",
                        "code": "invalid_request",
                        "failingPaths": [
                            {"path": "$.mode", "details": "invalid mode: 'turbo'"}
                        ],
                    },
                },
                400,
            )

            with pytest.raises(ValidationError) as exc_info:
                await parse_client.parse(
                    b"%PDF-1.7", mode="text"  # mode is fine; server-side fail
                )

        details = exc_info.value.details or {}
        failing = details.get("errorDetails", {}).get("failingPaths", [])
        assert failing and failing[0]["path"] == "$.mode"

    @pytest.mark.asyncio
    async def test_payment_required_propagates_as_api_error(
        self, parse_client: NutrientClient
    ) -> None:
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.side_effect = APIError(
                "Insufficient credits. This request requires 18 credits, 0 remaining.",
                402,
                {"requestId": "req_e_402"},
            )

            with pytest.raises(APIError) as exc_info:
                await parse_client.parse(b"%PDF-1.7", mode="agentic")

        assert exc_info.value.status_code == 402
        assert "Insufficient credits" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_server_error_propagates(
        self, parse_client: NutrientClient
    ) -> None:
        with patch("nutrient_dws.client.send_request", new_callable=AsyncMock) as send:
            send.side_effect = APIError(
                "Processing failed. Please retry or contact support with the requestId.",
                500,
                {
                    "requestId": "req_e_500",
                    "errorDetails": {"source": "maestro", "code": "maestro_error"},
                },
            )

            with pytest.raises(NutrientError) as exc_info:
                await parse_client.parse(b"%PDF-1.7", mode="structure")

        assert exc_info.value.status_code == 500
