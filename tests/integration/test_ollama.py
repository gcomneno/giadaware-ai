import os
import unittest

from giadaware_ai import AICapabilities, LogAnalysis
from giadaware_ai.backends import OllamaBackend


@unittest.skipUnless(
    os.environ.get("GIADAWARE_AI_RUN_INTEGRATION") == "1",
    "real AI integration test disabled",
)
class OllamaIntegrationTests(unittest.TestCase):
    def _backend(self) -> OllamaBackend:
        return OllamaBackend(
            model="qwen2.5:1.5b-instruct",
        )

    def test_analyze_log_against_local_ollama(self):
        ai = AICapabilities(self._backend())

        result = ai.analyze_log(
            """
2026-08-23 INFO Starting worker
2026-08-23 ERROR Connection refused: database unavailable
2026-08-23 WARN Retry 1/3
2026-08-23 ERROR Worker stopped after database connection failure
""".strip()
        )

        self.assertIsInstance(result, LogAnalysis)
        self.assertTrue(result.summary)
        self.assertIsInstance(
            result.possible_causes,
            tuple,
        )
        self.assertIsInstance(
            result.suggested_next_steps,
            tuple,
        )

    def test_schema_constrained_json_against_local_ollama(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
            "required": ["name", "count"],
            "additionalProperties": False,
        }

        result = self._backend().generate_json(
            system_prompt=(
                "Return only the requested structured data. "
                "Do not add fields."
            ),
            user_prompt="The name is widget and the count is 3.",
            response_schema=schema,
        )

        self.assertEqual(set(result), {"name", "count"})
        self.assertIsInstance(result["name"], str)
        self.assertIsInstance(result["count"], int)


if __name__ == "__main__":
    unittest.main()
