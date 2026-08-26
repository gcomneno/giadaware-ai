import io
import json
import unittest
from copy import deepcopy
from unittest.mock import patch

from giadaware_ai.backends import OllamaBackend
from giadaware_ai.errors import AIInvalidResponseError


class OllamaBackendStructuredOutputTests(unittest.TestCase):
    def _response(self, model_content: object) -> io.StringIO:
        return io.StringIO(
            json.dumps(
                {
                    "message": {
                        "content": model_content,
                    }
                }
            )
        )

    def test_generate_json_without_schema_preserves_json_mode(self):
        backend = OllamaBackend(model="test-model")

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

        self.assertEqual(payload["format"], "json")
        self.assertEqual(result, {"ok": True})

    def test_generate_json_with_schema_uses_structured_output(self):
        backend = OllamaBackend(model="test-model")
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

        self.assertEqual(payload["format"], schema)
        self.assertEqual(schema, original_schema)
        self.assertEqual(result, {"name": "widget", "count": 3})

    def test_malformed_model_json_preserves_invalid_response_error(self):
        backend = OllamaBackend(model="test-model")

        with patch(
            "urllib.request.urlopen",
            return_value=self._response("not-json"),
        ):
            with self.assertRaises(AIInvalidResponseError):
                backend.generate_json(
                    system_prompt="system",
                    user_prompt="user",
                    response_schema={"type": "object"},
                )


if __name__ == "__main__":
    unittest.main()
