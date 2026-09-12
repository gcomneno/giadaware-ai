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


class DeepSeekBackend:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "deepseek-v4-flash",
        base_url: str = "https://api.deepseek.com",
        timeout: float = 120.0,
    ) -> None:
        if not api_key.strip():
            raise AIConfigurationError(
                "DeepSeek API key must not be empty"
            )

        if not model.strip():
            raise AIConfigurationError(
                "DeepSeek model must not be empty"
            )

        if timeout <= 0:
            raise AIConfigurationError(
                "timeout must be greater than zero"
            )

        self._api_key = api_key
        self._model = model
        self._url = base_url.rstrip("/") + "/responses"
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

        if response_schema is None:
            response_format: dict[str, object] = {
                "type": "json_object",
            }
        else:
            response_format = {
                "type": "json_schema",
                "name": "giadaware_ai_response",
                "schema": dict(response_schema),
            }

        payload = {
            "model": self._model,
            "instructions": system_prompt,
            "input": user_prompt,
            "stream": False,
            "text": {
                "format": response_format,
            },
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
                "Authorization": f"Bearer {self._api_key}",
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
                "DeepSeek request timed out"
            ) from exc

        except urllib.error.HTTPError as exc:
            raise AIUnavailableError(
                f"DeepSeek request failed with HTTP {exc.code}"
            ) from exc

        except urllib.error.URLError as exc:
            raise AIUnavailableError(
                f"DeepSeek is unavailable: {exc.reason}"
            ) from exc

        except json.JSONDecodeError as exc:
            raise AIInvalidResponseError(
                "DeepSeek returned invalid JSON"
            ) from exc

        if not isinstance(envelope, dict):
            raise AIInvalidResponseError(
                "DeepSeek response envelope must be a JSON object"
            )

        if envelope.get("status") != "completed":
            raise AIInvalidResponseError(
                "DeepSeek response did not complete successfully"
            )

        output = envelope.get("output")
        if not isinstance(output, list):
            raise AIInvalidResponseError(
                "DeepSeek response has no output list"
            )

        text_parts: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            if item.get("type") != "message":
                continue
            if item.get("role") != "assistant":
                continue

            content = item.get("content")
            if not isinstance(content, list):
                continue

            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") != "output_text":
                    continue

                text = part.get("text")
                if not isinstance(text, str):
                    raise AIInvalidResponseError(
                        "DeepSeek output_text.text is not a string"
                    )
                text_parts.append(text)

        if not text_parts:
            raise AIInvalidResponseError(
                "DeepSeek response has no assistant output_text"
            )

        try:
            result = json.loads("".join(text_parts))
        except json.JSONDecodeError as exc:
            raise AIInvalidResponseError(
                "model output is not valid JSON"
            ) from exc

        if not isinstance(result, dict):
            raise AIInvalidResponseError(
                "model output must be a JSON object"
            )

        return result
