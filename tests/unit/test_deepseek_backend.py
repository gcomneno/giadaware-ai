import io
import json
import unittest
import urllib.error
from copy import deepcopy
from unittest.mock import patch

from giadaware_ai.backends import DeepSeekBackend
from giadaware_ai.errors import (
    AIConfigurationError,
    AIInvalidResponseError,
    AITimeoutError,
    AIUnavailableError,
)


class DeepSeekBackendTests(unittest.TestCase):
    def _response(self, model_content: object) -> io.StringIO:
        return io.StringIO(
            json.dumps(
                {
                    "status": "completed",
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": model_content,
                                }
                            ],
                        }
                    ],
                }
            )
        )

    def test_generate_json_without_schema_uses_json_object_mode(self):
        backend = DeepSeekBackend(api_key="secret")

        with patch(
            "urllib.request.urlopen",
            return_value=self._response('{"ok": true}'),
        ) as urlopen:
            result = backend.generate_json(
                system_prompt="system",
                user_prompt="user",
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "deepseek-v4-flash")
        self.assertEqual(payload["instructions"], "system")
        self.assertEqual(payload["input"], "user")
        self.assertFalse(payload["stream"])
        self.assertEqual(
            payload["text"]["format"],
            {"type": "json_object"},
        )
        self.assertEqual(
            request.headers["Authorization"],
            "Bearer secret",
        )
        self.assertEqual(result, {"ok": True})

    def test_generate_json_with_schema_uses_structured_output(self):
        backend = DeepSeekBackend(api_key="secret")
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["name", "count"],
            "additionalProperties": False,
        }
        original_schema = deepcopy(schema)

        with patch(
            "urllib.request.urlopen",
            return_value=self._response(
                '{"name": "widget", "count": 3}'
            ),
        ) as urlopen:
            result = backend.generate_json(
                system_prompt="system",
                user_prompt="user",
                response_schema=schema,
            )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        response_format = payload["text"]["format"]

        self.assertEqual(response_format["type"], "json_schema")
        self.assertEqual(
            response_format["name"],
            "giadaware_ai_response",
        )
        self.assertEqual(response_format["schema"], schema)
        self.assertEqual(schema, original_schema)
        self.assertEqual(result, {"name": "widget", "count": 3})

    def test_reasoning_items_are_ignored(self):
        backend = DeepSeekBackend(api_key="secret")
        response = io.StringIO(
            json.dumps(
                {
                    "status": "completed",
                    "output": [
                        {
                            "type": "reasoning",
                            "content": [
                                {
                                    "type": "reasoning_text",
                                    "text": "private reasoning",
                                }
                            ],
                        },
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": '{"ok": true}',
                                }
                            ],
                        },
                    ],
                }
            )
        )

        with patch(
            "urllib.request.urlopen",
            return_value=response,
        ):
            result = backend.generate_json(
                system_prompt="system",
                user_prompt="user",
            )

        self.assertEqual(result, {"ok": True})

    def test_invalid_configuration_fails_before_network(self):
        with self.assertRaises(AIConfigurationError):
            DeepSeekBackend(api_key="   ")

        with self.assertRaises(AIConfigurationError):
            DeepSeekBackend(api_key="secret", model="   ")

        with self.assertRaises(AIConfigurationError):
            DeepSeekBackend(api_key="secret", timeout=0)

    def test_malformed_model_json_is_invalid_response(self):
        backend = DeepSeekBackend(api_key="secret")

        with patch(
            "urllib.request.urlopen",
            return_value=self._response("not-json"),
        ):
            with self.assertRaises(AIInvalidResponseError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                )

    def test_non_object_model_json_is_invalid_response(self):
        backend = DeepSeekBackend(api_key="secret")

        with patch(
            "urllib.request.urlopen",
            return_value=self._response("[]"),
        ):
            with self.assertRaises(AIInvalidResponseError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                )

    def test_incomplete_response_is_invalid_response(self):
        backend = DeepSeekBackend(api_key="secret")
        response = io.StringIO(
            json.dumps(
                {
                    "status": "incomplete",
                    "output": [],
                }
            )
        )

        with patch(
            "urllib.request.urlopen",
            return_value=response,
        ):
            with self.assertRaises(AIInvalidResponseError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                )

    def test_timeout_maps_to_existing_timeout_error(self):
        backend = DeepSeekBackend(api_key="secret")

        with patch(
            "urllib.request.urlopen",
            side_effect=TimeoutError,
        ):
            with self.assertRaises(AITimeoutError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                )

    def test_network_failure_maps_to_existing_unavailable_error(self):
        backend = DeepSeekBackend(api_key="secret")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("offline"),
        ):
            with self.assertRaises(AIUnavailableError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                )


if __name__ == "__main__":
    unittest.main()
