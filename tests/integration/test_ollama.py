import os
import unittest

from giadaware_ai import AICapabilities, LogAnalysis
from giadaware_ai.backends import OllamaBackend


@unittest.skipUnless(
    os.environ.get("GIADAWARE_AI_RUN_INTEGRATION") == "1",
    "real AI integration test disabled",
)
class OllamaIntegrationTests(unittest.TestCase):
    def test_analyze_log_against_local_ollama(self):
        backend = OllamaBackend(
            model="qwen2.5:1.5b-instruct",
        )

        ai = AICapabilities(backend)

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


if __name__ == "__main__":
    unittest.main()
