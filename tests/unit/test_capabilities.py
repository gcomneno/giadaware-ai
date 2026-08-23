import unittest

from giadaware_ai import (
    AICapabilities,
    AIInvalidResponseError,
    AIUnavailableError,
    LogAnalysis,
    Severity,
)


class FakeBackend:
    def __init__(self, response):
        self.response = response

    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
    ):
        return self.response


class UnavailableBackend:
    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
    ):
        raise AIUnavailableError("offline")


class AnalyzeLogTests(unittest.TestCase):
    def test_returns_typed_log_analysis(self):
        backend = FakeBackend(
            {
                "summary": "Database connection failed.",
                "severity": "high",
                "possible_causes": [
                    "Database unavailable",
                ],
                "suggested_next_steps": [
                    "Check database availability",
                ],
            }
        )

        ai = AICapabilities(backend)

        result = ai.analyze_log(
            "ERROR database connection refused"
        )

        self.assertIsInstance(result, LogAnalysis)
        self.assertEqual(result.severity, Severity.HIGH)
        self.assertEqual(
            result.possible_causes,
            ("Database unavailable",),
        )

    def test_rejects_invalid_severity(self):
        backend = FakeBackend(
            {
                "summary": "Something happened.",
                "severity": "critical",
                "possible_causes": [],
                "suggested_next_steps": [],
            }
        )

        ai = AICapabilities(backend)

        with self.assertRaises(AIInvalidResponseError):
            ai.analyze_log("ERROR something")

    def test_rejects_missing_required_field(self):
        backend = FakeBackend(
            {
                "summary": "Something happened.",
                "severity": "unknown",
                "possible_causes": [],
            }
        )

        ai = AICapabilities(backend)

        with self.assertRaises(AIInvalidResponseError):
            ai.analyze_log("ERROR something")

    def test_backend_failure_is_not_hidden(self):
        ai = AICapabilities(UnavailableBackend())

        with self.assertRaises(AIUnavailableError):
            ai.analyze_log("ERROR something")

    def test_empty_input_is_rejected_before_ai_call(self):
        backend = FakeBackend({})

        ai = AICapabilities(backend)

        with self.assertRaises(ValueError):
            ai.analyze_log("   ")


if __name__ == "__main__":
    unittest.main()
