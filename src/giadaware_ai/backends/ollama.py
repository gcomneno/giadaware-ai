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
        base_url: str = "http://ollama:11434",
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
    ) -> Mapping[str, object]:
        payload = {
            "model": self._model,
            "stream": False,
            "format": "json",
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

        request = urllib.request.Request(
            self._url,
            data=json.dumps(payload).encode("utf-8"),
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
