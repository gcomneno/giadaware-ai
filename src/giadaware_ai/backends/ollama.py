import json
import socket
import urllib.error
import urllib.request
from collections.abc import Mapping

from ..errors import (
    AIConfigurationError,
    AIInvalidResponseError,
    AITimeoutError,
    AIUnavailableError,
)


class OllamaBackend:
    def __init__(
        self,
        *,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
    ) -> None:
        if not model.strip():
            raise AIConfigurationError(
                "Ollama model must not be empty"
            )

        if timeout <= 0:
            raise AIConfigurationError(
                "timeout must be greater than zero"
            )

        self._model = model
        self._url = base_url.rstrip("/") + "/api/chat"
        self._timeout = timeout

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        if response_schema is not None and not isinstance(
            response_schema,
            Mapping,
        ):
            raise AIConfigurationError(
                "response_schema must be a mapping"
            )

        response_format: str | dict[str, object]
        if response_schema is None:
            response_format = "json"
        else:
            response_format = dict(response_schema)

        payload = {
            "model": self._model,
            "stream": False,
            "format": response_format,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }

        try:
            request_data = json.dumps(payload).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise AIConfigurationError(
                "response_schema must be JSON-serializable"
            ) from exc

        request = urllib.request.Request(
            self._url,
            data=request_data,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self._timeout,
            ) as response:
                envelope = json.load(response)

        except (TimeoutError, socket.timeout) as exc:
            raise AITimeoutError(
                "Ollama request timed out"
            ) from exc

        except urllib.error.URLError as exc:
            raise AIUnavailableError(
                f"Ollama is unavailable: {exc.reason}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise AIInvalidResponseError(
                "Ollama returned invalid JSON"
            ) from exc

        try:
            content = envelope["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise AIInvalidResponseError(
                "Ollama response has no message.content"
            ) from exc

        if not isinstance(content, str):
            raise AIInvalidResponseError(
                "Ollama message.content is not a string"
            )

        try:
            result = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIInvalidResponseError(
                "model output is not valid JSON"
            ) from exc

        if not isinstance(result, dict):
            raise AIInvalidResponseError(
                "model output must be a JSON object"
            )

        return result
