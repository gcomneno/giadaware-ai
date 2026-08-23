import unittest
from dataclasses import dataclass

from giadaware_ai import (
    AICapabilities,
    AnalyzeCapability,
    AnalyzeLogCapability,
    CapabilityFamily,
    LogAnalysis,
    SemanticCapability,
    Severity,
)
from giadaware_ai.errors import AIInvalidResponseError


class FakeBackend:
    def __init__(self, response):
        self.response = response

    def generate_json(self, *, system_prompt, user_prompt):
        return self.response


@dataclass(frozen=True, slots=True)
class InvoiceAnalysis:
    reference: str


class AnalyzeInvoiceCapability(AnalyzeCapability[str, InvoiceAnalysis]):
    """Synthetic consumer-owned specialization used only for contract tests."""

    def execute(self, value: str) -> InvoiceAnalysis:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("invoice text must not be empty")

        raw = self._backend.generate_json(
            system_prompt=(
                "Read the supplied invoice text and return JSON containing "
                "only a string field named reference."
            ),
            user_prompt=value,
        )
        reference = raw.get("reference")
        if not isinstance(reference, str) or not reference.strip():
            raise AIInvalidResponseError("reference must be a non-empty string")
        return InvoiceAnalysis(reference=reference)


class SemanticExtensionAPITests(unittest.TestCase):
    def test_semantic_capability_is_abstract(self):
        with self.assertRaises(TypeError):
            SemanticCapability(FakeBackend({}))

    def test_all_twelve_families_have_stable_identity(self):
        self.assertEqual(
            {family.value for family in CapabilityFamily},
            {
                "analyze",
                "summarize",
                "classify",
                "extract",
                "compare",
                "explain",
                "identify",
                "generate",
                "propose",
                "transform",
                "synthesize",
                "detect",
            },
        )

    def test_core_log_capability_conforms_to_analyze_family(self):
        backend = FakeBackend(
            {
                "summary": "Database connection failed.",
                "severity": "high",
                "possible_causes": ["Database unavailable"],
                "suggested_next_steps": ["Check database availability"],
            }
        )
        capability = AnalyzeLogCapability(backend)

        result = capability.execute("ERROR database connection refused")

        self.assertEqual(capability.family, CapabilityFamily.ANALYZE)
        self.assertIsInstance(result, LogAnalysis)
        self.assertEqual(result.severity, Severity.HIGH)

    def test_existing_facade_remains_backwards_compatible(self):
        backend = FakeBackend(
            {
                "summary": "Database connection failed.",
                "severity": "high",
                "possible_causes": [],
                "suggested_next_steps": [],
            }
        )

        result = AICapabilities(backend).analyze_log("ERROR database offline")

        self.assertEqual(result.summary, "Database connection failed.")

    def test_consumer_can_specialize_family_without_provider_coupling(self):
        backend = FakeBackend({"reference": "INV-2026-0042"})
        capability = AnalyzeInvoiceCapability(backend)

        result = capability.execute("Invoice reference INV-2026-0042")

        self.assertEqual(capability.family, CapabilityFamily.ANALYZE)
        self.assertEqual(result, InvoiceAnalysis(reference="INV-2026-0042"))


if __name__ == "__main__":
    unittest.main()
