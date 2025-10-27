"""Custom MarkItDown tool integration for AG2 agents."""
from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any, Dict

from markitdown import MarkItDown

try:  # pragma: no cover - optional dependency typing for ag2
    from ag2.tools import BaseTool
except ImportError:  # pragma: no cover - allows type checking without ag2 installed
    BaseTool = object  # type: ignore[misc,assignment]


@dataclass
class MarkItDownTool(BaseTool):
    """AG2 tool wrapper that exposes MarkItDown conversions."""

    name: str = "markitdown_convert"
    description: str = (
        "Convert a file or blob of bytes into Markdown using the markitdown library. "
        "Provide either a path to a file on disk or raw bytes encoded as base64." 
    )

    def __post_init__(self) -> None:
        self._converter = MarkItDown()

    async def _arun(self, *args: Any, **kwargs: Any) -> str:  # pragma: no cover - async entrypoint
        return self._run(*args, **kwargs)

    def _run(self, *, path: str | None = None, data: bytes | str | None = None) -> str:
        """Convert provided input to Markdown text."""
        if bool(path) == bool(data):
            raise ValueError("Provide exactly one of 'path' or 'data' to markitdown_convert")

        if path:
            result = self._converter.convert(path)
        else:
            if data is None:
                raise ValueError("'data' cannot be None when 'path' is not provided")

            payload: bytes
            if isinstance(data, str):
                try:
                    payload = base64.b64decode(data, validate=True)
                except binascii.Error as exc:  # pragma: no cover - defensive path
                    raise ValueError("'data' must be a valid base64 string") from exc
            else:
                payload = data

            result = self._converter.convert(payload)

        return result.text if hasattr(result, "text") else str(result)

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to a local file that should be converted to Markdown.",
                },
                "data": {
                    "type": "string",
                    "description": "Raw data (as base64 string) to convert when a file path is unavailable.",
                },
            },
            "required": [],
        }
