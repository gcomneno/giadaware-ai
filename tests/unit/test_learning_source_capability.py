import unittest

from giadaware_ai import (
    AICapabilities,
    AIInvalidResponseError,
    AITimeoutError,
    AIUnavailableError,
    AnalyzeLearningSourceCapability,
    CapabilityFamily,
    ClaimSupport,
    LearningSourceAnalysis,
    SourceClaim,
)


VALID_RESPONSE = {
    "central_thesis": "The source explains controlled semantic AI capabilities.",
    "key_concepts": ["semantic capability", "provider independence"],
    "source_claims": [
        {
            "claim": "Consumers should depend on semantic capabilities.",
            "support": "explicit",
        },
        {
            "claim": "The design may reduce provider churn for consumers.",
            "support": "inferred",
        },
    ],
    "practical_applications": ["Use a stable capability API in consumer code."],
    "limitations": ["The source does not independently verify model output."],
    "review_questions": ["Which invariants belong to the consumer?"],
}


class FakeBackend:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def generate_json(self, *, system_prompt, user_prompt):
        self.calls += 1
        return self.response


class UnavailableBackend:
    def generate_json(self, *, system_prompt, user_prompt):
        raise AIUnavailableError("offline")


class TimeoutBackend:
    def generate_json(self, *, system_prompt, user_prompt):
        raise AITimeoutError("timed out")


class AnalyzeLearningSourceTests(unittest.TestCase):
    def test_returns_typed_learning_source_analysis(self):
        capability = AnalyzeLearningSourceCapability(FakeBackend(VALID_RESPONSE))

        result = capability.execute("A learning source")

        self.assertEqual(capability.family, CapabilityFamily.ANALYZE)
        self.assertIsInstance(result, LearningSourceAnalysis)
        self.assertEqual(
            result.source_claims[0],
            SourceClaim(
                claim="Consumers should depend on semantic capabilities.",
                support=ClaimSupport.EXPLICIT,
            ),
        )
        self.assertEqual(result.source_claims[1].support, ClaimSupport.INFERRED)

    def test_facade_exposes_learning_source_analysis(self):
        result = AICapabilities(FakeBackend(VALID_RESPONSE)).analyze_learning_source(
            "A learning source"
        )

        self.assertIsInstance(result, LearningSourceAnalysis)

    def test_empty_input_is_rejected_before_inference(self):
        backend = FakeBackend(VALID_RESPONSE)
        capability = AnalyzeLearningSourceCapability(backend)

        with self.assertRaises(ValueError):
            capability.execute("   ")

        self.assertEqual(backend.calls, 0)

    def test_non_string_input_is_rejected_before_inference(self):
        backend = FakeBackend(VALID_RESPONSE)
        capability = AnalyzeLearningSourceCapability(backend)

        with self.assertRaises(TypeError):
            capability.execute(None)  # type: ignore[arg-type]

        self.assertEqual(backend.calls, 0)

    def test_rejects_invalid_claim_support(self):
        response = dict(VALID_RESPONSE)
        response["source_claims"] = [
            {"claim": "A claim", "support": "verified"}
        ]

        with self.assertRaises(AIInvalidResponseError):
            AnalyzeLearningSourceCapability(FakeBackend(response)).execute("source")

    def test_rejects_missing_required_field(self):
        response = dict(VALID_RESPONSE)
        del response["limitations"]

        with self.assertRaises(AIInvalidResponseError):
            AnalyzeLearningSourceCapability(FakeBackend(response)).execute("source")

    def test_rejects_malformed_claim_entry(self):
        response = dict(VALID_RESPONSE)
        response["source_claims"] = ["not an object"]

        with self.assertRaises(AIInvalidResponseError):
            AnalyzeLearningSourceCapability(FakeBackend(response)).execute("source")

    def test_rejects_claim_missing_support(self):
        response = dict(VALID_RESPONSE)
        response["source_claims"] = [{"claim": "A claim"}]

        with self.assertRaises(AIInvalidResponseError):
            AnalyzeLearningSourceCapability(FakeBackend(response)).execute("source")

    def test_backend_unavailable_is_not_hidden(self):
        with self.assertRaises(AIUnavailableError):
            AnalyzeLearningSourceCapability(UnavailableBackend()).execute("source")

    def test_backend_timeout_is_not_hidden(self):
        with self.assertRaises(AITimeoutError):
            AnalyzeLearningSourceCapability(TimeoutBackend()).execute("source")

    def test_provider_metadata_cannot_enter_semantic_result(self):
        response = dict(VALID_RESPONSE)
        response.update(
            {
                "backend": "model-asserted-backend",
                "model": "model-asserted-model",
                "authority": "approved",
                "sha256": "model-asserted-digest",
            }
        )

        result = AnalyzeLearningSourceCapability(FakeBackend(response)).execute("source")

        self.assertFalse(hasattr(result, "backend"))
        self.assertFalse(hasattr(result, "model"))
        self.assertFalse(hasattr(result, "authority"))
        self.assertFalse(hasattr(result, "sha256"))


if __name__ == "__main__":
    unittest.main()
