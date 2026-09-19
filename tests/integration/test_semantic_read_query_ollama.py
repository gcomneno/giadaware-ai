from __future__ import annotations

import os
import unittest

from giadaware_ai import (
    ReadQueryStatus,
    SemanticQueryColumn,
    SemanticQueryContext,
    SemanticQueryLimits,
    SemanticQueryRelation,
    SemanticReadQueryInterpreter,
    SemanticReadQueryRequest,
)
from giadaware_ai.backends import OllamaBackend
from unittest.mock import patch


def _qualification_think() -> bool | None:
    value = os.environ.get(
        "GIADAWARE_AI_QUALIFICATION_THINK"
    )
    if value is None:
        return None
    if value == "0":
        return False
    if value == "1":
        return True
    raise ValueError(
        "GIADAWARE_AI_QUALIFICATION_THINK must be 0 or 1"
    )


class QualificationThinkConfigurationTests(unittest.TestCase):
    def test_absent_override_preserves_backend_default(self):
        with patch.dict(
            os.environ,
            {},
            clear=True,
        ):
            self.assertIsNone(_qualification_think())

    def test_zero_disables_thinking(self):
        with patch.dict(
            os.environ,
            {"GIADAWARE_AI_QUALIFICATION_THINK": "0"},
            clear=True,
        ):
            self.assertIs(_qualification_think(), False)

    def test_one_enables_thinking(self):
        with patch.dict(
            os.environ,
            {"GIADAWARE_AI_QUALIFICATION_THINK": "1"},
            clear=True,
        ):
            self.assertIs(_qualification_think(), True)

    def test_invalid_override_fails_closed(self):
        with patch.dict(
            os.environ,
            {"GIADAWARE_AI_QUALIFICATION_THINK": "false"},
            clear=True,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "GIADAWARE_AI_QUALIFICATION_THINK must be 0 or 1",
            ):
                _qualification_think()


@unittest.skipUnless(
    os.environ.get(
        "GIADAWARE_AI_RUN_READ_QUERY_QUALIFICATION"
    )
    == "1",
    "semantic read-query qualification disabled",
)
class SemanticReadQueryOllamaQualificationTests(unittest.TestCase):
    """Opt-in semantic evaluation, not deterministic CI."""

    @classmethod
    def setUpClass(cls):
        context = SemanticQueryContext(
            context_id="qualification.observations",
            revision="1",
            dialect="sqlite",
            languages=("it", "en"),
            domain_description=(
                "Historical observations in categories alpha and beta."
            ),
            relations=(
                SemanticQueryRelation(
                    name="observations",
                    kind="view",
                    description=(
                        "Read-only historical observations."
                    ),
                    columns=(
                        SemanticQueryColumn(
                            name="observed_at",
                            data_type="date",
                            description="Civil observation date.",
                        ),
                        SemanticQueryColumn(
                            name="category",
                            data_type="text",
                            description=(
                                "Observation category: alpha or beta."
                            ),
                        ),
                        SemanticQueryColumn(
                            name="value",
                            data_type="integer",
                            description="Observed integer value.",
                        ),
                    ),
                ),
            ),
            concepts=(),
            relationships=(),
            limits=SemanticQueryLimits(
                max_result_rows=500,
                max_relations=1,
            ),
            semantic_rules=(
                "an observation request without category or temporal "
                "selectors means all observations",
                "boolean expressions with unclear operator scope are "
                "ambiguous",
                "latest means the latest available observation",
                "requests for future values are predictive and unsupported",
            ),
            accepted_examples=(
                "Show all observations.",
                "Show the observation.",
                "Mostra tutte le osservazioni.",
            ),
            rejected_examples=(
                "Write a poem about alpha.",
                "Delete all observations.",
                "Predict the next value.",
            ),
            allowed_query_features=(
                "select",
                "filter",
                "order",
                "limit",
                "aggregate",
                "group",
            ),
        )
        backend = OllamaBackend(
            model=os.environ.get(
                "GIADAWARE_AI_QUALIFICATION_MODEL",
                "qwen2.5:1.5b-instruct",
            ),
            base_url=os.environ.get(
                "GIADAWARE_AI_QUALIFICATION_BASE_URL",
                "http://localhost:11434",
            ),
            think=_qualification_think(),
        )
        cls.interpreter = SemanticReadQueryInterpreter(
            backend,
            context,
        )

    def interpret(self, text: str, language: str):
        return self.interpreter.execute(
            SemanticReadQueryRequest(
                text=text,
                language=language,
            )
        )

    def test_accepts_english_read_request(self):
        result = self.interpret(
            "Show all observations.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.ACCEPTED,
        )
        self.assertTrue(result.normalized_interpretation)
        self.assertTrue(result.candidate_query)

    def test_accepts_italian_read_request(self):
        result = self.interpret(
            "Mostra tutte le osservazioni.",
            "it",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.ACCEPTED,
        )
        self.assertTrue(result.normalized_interpretation)
        self.assertTrue(result.candidate_query)

    def test_accepts_declared_unfiltered_default(self):
        result = self.interpret(
            "Show the observation.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.ACCEPTED,
        )
        self.assertTrue(result.normalized_interpretation)
        self.assertTrue(result.candidate_query)

    def test_rejects_outside_domain_request(self):
        result = self.interpret(
            "Write a poem about alpha.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.UNSUPPORTED,
        )
        self.assertIsNone(result.candidate_query)

    def test_surfaces_material_ambiguity(self):
        result = self.interpret(
            "Show observations for category alpha or category beta "
            "with value 18.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.AMBIGUOUS,
        )
        self.assertIsNone(result.candidate_query)

    def test_rejects_mutation_request(self):
        result = self.interpret(
            "Delete all observations.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.UNSUPPORTED,
        )
        self.assertIsNone(result.candidate_query)

    def test_rejects_predictive_request(self):
        result = self.interpret(
            "Predict the next observed value.",
            "en",
        )

        self.assertEqual(
            result.status,
            ReadQueryStatus.UNSUPPORTED,
        )
        self.assertIsNone(result.candidate_query)


if __name__ == "__main__":
    unittest.main()
