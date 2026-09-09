from __future__ import annotations

import unittest

from giadaware_ai import (
    AIConfigurationError,
    AIInvalidResponseError,
    ReadQueryGrounding,
    ReadQueryGroundingSource,
    ReadQueryInterpretation,
    ReadQueryParameter,
    ReadQueryStatus,
    SemanticQueryColumn,
    SemanticQueryConcept,
    SemanticQueryLimits,
    SemanticQueryRelationship,
    SemanticQueryContext,
    SemanticQueryRelation,
    SemanticReadQueryInterpreter,
    SemanticReadQueryRequest,
    TransformCapability,
    semantic_query_context_from_mapping,
)


class RecordingBackend:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
        response_schema=None,
    ):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response_schema": response_schema,
            }
        )
        return self.response


def query_context() -> SemanticQueryContext:
    return SemanticQueryContext(
        context_id="example.read_query",
        revision="1",
        dialect="sqlite",
        languages=("it", "en"),
        domain_description="Historical observations stored by the consumer.",
        relations=(
            SemanticQueryRelation(
                name="observations",
                kind="view",
                description="Read-only historical observations.",
                columns=(
                    SemanticQueryColumn(
                        name="observed_at",
                        data_type="date",
                        description="Civil observation date.",
                    ),
                    SemanticQueryColumn(
                        name="category",
                        data_type="text",
                        description="Consumer-defined category.",
                    ),
                    SemanticQueryColumn(
                        name="value",
                        data_type="integer",
                        description="Observed integer value.",
                    ),
                ),
            ),
        ),
        concepts=(
            SemanticQueryConcept(
                name="measurement",
                description="A numeric historical observation.",
                synonyms=("value", "amount"),
            ),
        ),
        relationships=(),
        limits=SemanticQueryLimits(
            max_result_rows=500,
            max_relations=1,
        ),
        semantic_rules=(
            "latest means the latest available observation",
            "yesterday means the previous civil date",
        ),
        accepted_examples=(
            "Show the latest observation for category alpha.",
        ),
        rejected_examples=(
            "Delete the latest observation.",
        ),
        allowed_query_features=(
            "filter",
            "order",
            "limit",
            "aggregate",
            "group",
        ),
    )


def accepted_response():
    return {
        "status": "accepted",
        "normalized_interpretation": (
            "Return observations for category alpha with value 18."
        ),
        "candidate_query": (
            "SELECT observed_at, value FROM observations "
            "WHERE category = :category AND value = :value "
            "ORDER BY observed_at DESC LIMIT 500"
        ),
        "parameters": [
            {"name": "category", "value": "alpha"},
            {"name": "value", "value": 18},
        ],
        "grounding": [
            {
                "query_fragment": "category = :category",
                "field": "category",
                "source_kind": "request",
                "source_reference": "category alpha",
            },
            {
                "query_fragment": "value = :value",
                "field": "value",
                "source_kind": "request",
                "source_reference": "18",
            },
        ],
        "reason": None,
    }


class SemanticReadQueryContractTests(unittest.TestCase):
    def test_semantic_context_support_models_are_typed_and_immutable(self):
        concept = SemanticQueryConcept(
            name="amount",
            description="A numeric observed amount.",
            synonyms=("value", "measurement"),
        )
        relationship = SemanticQueryRelationship(
            name="observation_category",
            left_relation="observations",
            left_column="category",
            right_relation="categories",
            right_column="name",
            description=(
                "Each observation belongs to one declared category."
            ),
        )
        limits = SemanticQueryLimits(
            max_result_rows=500,
            max_relations=2,
        )

        self.assertEqual(concept.synonyms, ("value", "measurement"))
        self.assertEqual(
            relationship.left_relation,
            "observations",
        )
        self.assertEqual(limits.max_result_rows, 500)

        for value, attribute, replacement in (
            (concept, "name", "changed"),
            (relationship, "description", "changed"),
            (limits, "max_relations", 99),
        ):
            with self.subTest(value=value):
                with self.assertRaises((AttributeError, TypeError)):
                    setattr(value, attribute, replacement)

    def test_grounding_source_is_a_closed_public_enum(self):
        self.assertEqual(
            {item.value for item in ReadQueryGroundingSource},
            {"request", "context_rule"},
        )
        self.assertIs(
            ReadQueryGroundingSource("request"),
            ReadQueryGroundingSource.REQUEST,
        )
        self.assertIs(
            ReadQueryGroundingSource("context_rule"),
            ReadQueryGroundingSource.CONTEXT_RULE,
        )
        with self.assertRaises(ValueError):
            ReadQueryGroundingSource("model")

    def test_interpreter_is_transform_capability(self):
        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(accepted_response()),
            query_context(),
        )
        self.assertIsInstance(interpreter, TransformCapability)

    def test_accepted_result_is_typed_with_trusted_context_identity(self):
        backend = RecordingBackend(accepted_response())
        result = SemanticReadQueryInterpreter(
            backend,
            query_context(),
        ).execute(
            SemanticReadQueryRequest(
                text="Show observations for category alpha with value 18.",
                language="en",
            )
        )

        self.assertEqual(result.status, ReadQueryStatus.ACCEPTED)
        self.assertEqual(result.context_id, "example.read_query")
        self.assertEqual(result.context_revision, "1")
        self.assertEqual(result.language, "en")
        self.assertEqual(
            result.parameters,
            (
                ReadQueryParameter(name="category", value="alpha"),
                ReadQueryParameter(name="value", value=18),
            ),
        )
        self.assertEqual(
            result.grounding,
            (
                ReadQueryGrounding(
                    query_fragment="category = :category",
                    field="category",
                    source_kind=ReadQueryGroundingSource.REQUEST,
                    source_reference="category alpha",
                ),
                ReadQueryGrounding(
                    query_fragment="value = :value",
                    field="value",
                    source_kind=ReadQueryGroundingSource.REQUEST,
                    source_reference="18",
                ),
            ),
        )
        self.assertIsNone(result.reason)

        call = backend.calls[0]
        self.assertIn("example.read_query", call["user_prompt"])
        self.assertIn("observations", call["user_prompt"])
        self.assertIn('"concepts"', call["user_prompt"])
        self.assertIn('"measurement"', call["user_prompt"])
        self.assertIn('"relationships"', call["user_prompt"])
        self.assertIn('"limits"', call["user_prompt"])
        self.assertIn('"max_result_rows": 500', call["user_prompt"])
        self.assertIn('"max_relations": 1', call["user_prompt"])
        self.assertNotIn("ollama", repr(call["response_schema"]).lower())
        self.assertNotIn("format", call["response_schema"])

    def test_rejects_parameter_value_not_supported_by_request_grounding(self):
        response = accepted_response()
        response["parameters"][1]["value"] = 81

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        )

        with self.assertRaises(AIInvalidResponseError):
            interpreter.execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_rejects_parameter_placeholder_prefix_collision(self):
        response = accepted_response()
        response["parameters"][1]["name"] = "id"
        response["candidate_query"] = response[
            "candidate_query"
        ].replace(":value", ":identifier")
        response["grounding"][1]["field"] = "id"
        response["grounding"][1]["query_fragment"] = (
            "value = :identifier"
        )

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        )

        with self.assertRaises(AIInvalidResponseError):
            interpreter.execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_rejects_parameter_value_substring_collision(self):
        response = accepted_response()
        response["parameters"][1]["value"] = 1

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        )

        with self.assertRaises(AIInvalidResponseError):
            interpreter.execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_rejects_result_limit_above_context_maximum(self):
        response = accepted_response()
        response["candidate_query"] = response[
            "candidate_query"
        ].replace("LIMIT 500", "LIMIT 501")

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        )

        with self.assertRaises(AIInvalidResponseError):
            interpreter.execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_rejects_candidate_above_max_relations(self):
        response = accepted_response()
        response["candidate_query"] = response[
            "candidate_query"
        ].replace(
            "FROM observations ",
            (
                "FROM observations "
                "JOIN observations AS duplicate "
                "ON duplicate.category = observations.category "
            ),
        )

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        )

        with self.assertRaises(AIInvalidResponseError):
            interpreter.execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_exact_grounding_rejects_case_mismatches(self):
        mutations = (
            (
                "query_fragment",
                "CATEGORY = :category",
            ),
            (
                "source_reference",
                "CATEGORY ALPHA",
            ),
        )

        for field, replacement in mutations:
            with self.subTest(field=field):
                response = accepted_response()
                response["grounding"][0][field] = replacement

                interpreter = SemanticReadQueryInterpreter(
                    RecordingBackend(response),
                    query_context(),
                )

                with self.assertRaises(AIInvalidResponseError):
                    interpreter.execute(
                        SemanticReadQueryRequest(
                            text=(
                                "Show observations for category alpha "
                                "with value 18."
                            ),
                            language="en",
                        )
                    )

    def test_response_schema_encodes_status_invariants(self):
        backend = RecordingBackend(accepted_response())
        SemanticReadQueryInterpreter(
            backend,
            query_context(),
        ).execute(
            SemanticReadQueryRequest(
                text=(
                    "Show observations for category alpha "
                    "with value 18."
                ),
                language="en",
            )
        )

        schema = backend.calls[0]["response_schema"]
        self.assertIn("oneOf", schema)
        variants = schema["oneOf"]
        self.assertEqual(len(variants), 3)

        by_status = {
            variant["properties"]["status"]["const"]: variant
            for variant in variants
        }
        self.assertEqual(
            set(by_status),
            {"accepted", "unsupported", "ambiguous"},
        )
        self.assertEqual(
            by_status["accepted"]["properties"]["reason"],
            {"type": "null"},
        )
        for status in ("unsupported", "ambiguous"):
            properties = by_status[status]["properties"]
            self.assertEqual(
                properties["candidate_query"],
                {"type": "null"},
            )
            self.assertEqual(
                properties["parameters"]["maxItems"],
                0,
            )
            self.assertEqual(
                properties["grounding"]["maxItems"],
                0,
            )

    def test_unsupported_and_ambiguous_are_explicit(self):
        for status in ("unsupported", "ambiguous"):
            with self.subTest(status=status):
                backend = RecordingBackend(
                    {
                        "status": status,
                        "normalized_interpretation": "",
                        "candidate_query": None,
                        "parameters": [],
                        "grounding": [],
                        "reason": "The request cannot be accepted.",
                    }
                )
                result = SemanticReadQueryInterpreter(
                    backend,
                    query_context(),
                ).execute(
                    SemanticReadQueryRequest(
                        text="Tell me something about alpha.",
                        language="en",
                    )
                )

                self.assertEqual(result.status, ReadQueryStatus(status))
                self.assertIsNone(result.candidate_query)
                self.assertEqual(result.parameters, ())
                self.assertEqual(result.grounding, ())
                self.assertTrue(result.reason)

    def test_request_preconditions_fail_before_backend(self):
        requests = (
            SemanticReadQueryRequest(text="", language="en"),
            SemanticReadQueryRequest(text="Show observations.", language="fr"),
        )

        for request in requests:
            with self.subTest(request=request):
                backend = RecordingBackend(accepted_response())
                interpreter = SemanticReadQueryInterpreter(
                    backend,
                    query_context(),
                )
                with self.assertRaises((ValueError, AIConfigurationError)):
                    interpreter.execute(request)
                self.assertEqual(backend.calls, [])

    def test_context_rejects_column_lookalike_objects(self):
        class ColumnLookalike:
            name = "value"
            data_type = "integer"
            description = "Not a typed semantic column."

        valid = query_context()
        invalid_relation = SemanticQueryRelation(
            name="observations",
            kind="view",
            description="Read-only historical observations.",
            columns=(ColumnLookalike(),),
        )
        invalid = SemanticQueryContext(
            context_id=valid.context_id,
            revision=valid.revision,
            dialect=valid.dialect,
            languages=valid.languages,
            domain_description=valid.domain_description,
            relations=(invalid_relation,),
            concepts=valid.concepts,
            relationships=valid.relationships,
            limits=valid.limits,
            semantic_rules=valid.semantic_rules,
            accepted_examples=valid.accepted_examples,
            rejected_examples=valid.rejected_examples,
            allowed_query_features=valid.allowed_query_features,
        )
        backend = RecordingBackend(accepted_response())

        with self.assertRaises(AIConfigurationError):
            SemanticReadQueryInterpreter(backend, invalid)
        self.assertEqual(backend.calls, [])

    def test_direct_context_normalizes_column_values(self):
        base = query_context()
        relation = base.relations[0]
        column = relation.columns[0]

        context = SemanticQueryContext(
            context_id=base.context_id,
            revision=base.revision,
            dialect=base.dialect,
            languages=base.languages,
            domain_description=base.domain_description,
            relations=(
                SemanticQueryRelation(
                    name=relation.name,
                    kind=relation.kind,
                    description=relation.description,
                    columns=(
                        SemanticQueryColumn(
                            name=f"  {column.name}  ",
                            data_type=f"  {column.data_type}  ",
                            description=f"  {column.description}  ",
                        ),
                    ),
                ),
            ),
            concepts=base.concepts,
            relationships=base.relationships,
            limits=base.limits,
            semantic_rules=base.semantic_rules,
            accepted_examples=base.accepted_examples,
            rejected_examples=base.rejected_examples,
            allowed_query_features=base.allowed_query_features,
        )

        interpreter = SemanticReadQueryInterpreter(
            RecordingBackend(accepted_response()),
            context,
        )
        normalized = interpreter.context.relations[0].columns[0]

        self.assertEqual(normalized.name, column.name)
        self.assertEqual(normalized.data_type, column.data_type)
        self.assertEqual(normalized.description, column.description)

    def test_invalid_context_fails_before_backend(self):
        backend = RecordingBackend(accepted_response())
        invalid = SemanticQueryContext(
            context_id="",
            revision="1",
            dialect="sqlite",
            languages=("en",),
            domain_description="Example.",
            relations=(),
            concepts=(),
            relationships=(),
            limits=SemanticQueryLimits(
                max_result_rows=1,
                max_relations=1,
            ),
            semantic_rules=(),
            accepted_examples=(),
            rejected_examples=(),
            allowed_query_features=(),
        )

        with self.assertRaises(AIConfigurationError):
            SemanticReadQueryInterpreter(backend, invalid)
        self.assertEqual(backend.calls, [])

    def test_extra_or_missing_model_fields_are_rejected(self):
        extra = accepted_response()
        extra["safe_to_execute"] = True
        missing = accepted_response()
        del missing["grounding"]

        for response in (extra, missing):
            with self.subTest(response=response):
                with self.assertRaises(AIInvalidResponseError):
                    SemanticReadQueryInterpreter(
                        RecordingBackend(response),
                        query_context(),
                    ).execute(
                        SemanticReadQueryRequest(
                            text=(
                                "Show observations for category alpha "
                                "with value 18."
                            ),
                            language="en",
                        )
                    )

    def test_status_query_and_reason_invariants_are_enforced(self):
        invalid_responses = (
            {**accepted_response(), "candidate_query": None},
            {**accepted_response(), "reason": "The model says this is safe."},
            {**accepted_response(), "status": "unsupported"},
        )

        for response in invalid_responses:
            with self.subTest(response=response):
                with self.assertRaises(AIInvalidResponseError):
                    SemanticReadQueryInterpreter(
                        RecordingBackend(response),
                        query_context(),
                    ).execute(
                        SemanticReadQueryRequest(
                            text=(
                                "Show observations for category alpha "
                                "with value 18."
                            ),
                            language="en",
                        )
                    )

    def test_grounding_fragments_must_exist_in_request(self):
        response = accepted_response()
        response["grounding"] = [
            {
                "query_fragment": "value = :value",
                "field": "value",
                "source_kind": "request",
                "source_reference": "value 81",
            }
        ]

        with self.assertRaises(AIInvalidResponseError):
            SemanticReadQueryInterpreter(
                RecordingBackend(response),
                query_context(),
            ).execute(
                SemanticReadQueryRequest(
                    text="Show observations for category alpha with value 18.",
                    language="en",
                )
            )

    def test_rejects_grounding_query_fragment_absent_from_candidate(self):
        response = accepted_response()
        response["grounding"][1]["query_fragment"] = "value = 81"

        with self.assertRaises(AIInvalidResponseError):
            SemanticReadQueryInterpreter(
                RecordingBackend(response),
                query_context(),
            ).execute(
                SemanticReadQueryRequest(
                    text=(
                        "Show observations for category alpha "
                        "with value 18."
                    ),
                    language="en",
                )
            )

    def test_accepts_grounding_from_an_exact_context_rule(self):
        response = {
            "status": "accepted",
            "normalized_interpretation": (
                "Return the latest available observation."
            ),
            "candidate_query": (
                "SELECT observed_at, value FROM observations "
                "ORDER BY observed_at DESC LIMIT 1"
            ),
            "parameters": [],
            "grounding": [
                {
                    "query_fragment": (
                        "ORDER BY observed_at DESC LIMIT 1"
                    ),
                    "field": "observed_at",
                    "source_kind": "context_rule",
                    "source_reference": (
                        "latest means the latest available observation"
                    ),
                }
            ],
            "reason": None,
        }

        result = SemanticReadQueryInterpreter(
            RecordingBackend(response),
            query_context(),
        ).execute(
            SemanticReadQueryRequest(
                text="Show the latest observation.",
                language="en",
            )
        )

        self.assertEqual(
            result.grounding,
            (
                ReadQueryGrounding(
                    query_fragment=(
                        "ORDER BY observed_at DESC LIMIT 1"
                    ),
                    field="observed_at",
                    source_kind=(
                        ReadQueryGroundingSource.CONTEXT_RULE
                    ),
                    source_reference=(
                        "latest means the latest available observation"
                    ),
                ),
            ),
        )

    def test_preserves_multiclause_constraints_in_italian_and_english(self):
        cases = (
            {
                "language": "it",
                "text": (
                    "Mostra le osservazioni della categoria alpha "
                    "dal 2020-01-01 al 2020-12-31 con valore maggiore "
                    "di 18 ma non 81."
                ),
                "query": (
                    "SELECT observed_at, value FROM observations "
                    "WHERE category = :category "
                    "AND observed_at BETWEEN :start_date AND :end_date "
                    "AND value > :minimum_value "
                    "AND value <> :excluded_value"
                ),
                "parameters": [
                    {"name": "category", "value": "alpha"},
                    {"name": "start_date", "value": "2020-01-01"},
                    {"name": "end_date", "value": "2020-12-31"},
                    {"name": "minimum_value", "value": 18},
                    {"name": "excluded_value", "value": 81},
                ],
                "grounding": [
                    (
                        "category = :category",
                        "category",
                        "categoria alpha",
                    ),
                    (
                        "observed_at BETWEEN :start_date AND :end_date",
                        "start_date",
                        "dal 2020-01-01 al 2020-12-31",
                    ),
                    (
                        "observed_at BETWEEN :start_date AND :end_date",
                        "end_date",
                        "dal 2020-01-01 al 2020-12-31",
                    ),
                    (
                        "value > :minimum_value",
                        "minimum_value",
                        "maggiore di 18",
                    ),
                    (
                        "value <> :excluded_value",
                        "excluded_value",
                        "non 81",
                    ),
                ],
            },
            {
                "language": "en",
                "text": (
                    "Show category beta observations from 2021-01-01 "
                    "to 2021-06-30 with value at least 10 or exactly 20."
                ),
                "query": (
                    "SELECT observed_at, value FROM observations "
                    "WHERE category = :category "
                    "AND observed_at BETWEEN :start_date AND :end_date "
                    "AND (value >= :minimum_value OR value = :exact_value)"
                ),
                "parameters": [
                    {"name": "category", "value": "beta"},
                    {"name": "start_date", "value": "2021-01-01"},
                    {"name": "end_date", "value": "2021-06-30"},
                    {"name": "minimum_value", "value": 10},
                    {"name": "exact_value", "value": 20},
                ],
                "grounding": [
                    (
                        "category = :category",
                        "category",
                        "category beta",
                    ),
                    (
                        "observed_at BETWEEN :start_date AND :end_date",
                        "start_date",
                        "from 2021-01-01 to 2021-06-30",
                    ),
                    (
                        "observed_at BETWEEN :start_date AND :end_date",
                        "end_date",
                        "from 2021-01-01 to 2021-06-30",
                    ),
                    (
                        "value >= :minimum_value",
                        "minimum_value",
                        "at least 10",
                    ),
                    (
                        "value = :exact_value",
                        "exact_value",
                        "exactly 20",
                    ),
                ],
            },
        )

        for case in cases:
            with self.subTest(language=case["language"]):
                response = {
                    "status": "accepted",
                    "normalized_interpretation": (
                        "Return every requested constrained observation."
                    ),
                    "candidate_query": (
                        case["query"] + " LIMIT 500"
                    ),
                    "parameters": case["parameters"],
                    "grounding": [
                        {
                            "query_fragment": query_fragment,
                            "field": field,
                            "source_kind": "request",
                            "source_reference": source_reference,
                        }
                        for (
                            query_fragment,
                            field,
                            source_reference,
                        ) in case["grounding"]
                    ],
                    "reason": None,
                }

                result = SemanticReadQueryInterpreter(
                    RecordingBackend(response),
                    query_context(),
                ).execute(
                    SemanticReadQueryRequest(
                        text=case["text"],
                        language=case["language"],
                    )
                )

                self.assertEqual(result.status, ReadQueryStatus.ACCEPTED)
                self.assertEqual(
                    {item.name for item in result.parameters},
                    {
                        parameter["name"]
                        for parameter in case["parameters"]
                    },
                )
                self.assertEqual(
                    {item.field for item in result.grounding},
                    {
                        parameter["name"]
                        for parameter in case["parameters"]
                    },
                )
                self.assertTrue(
                    all(
                        item.source_kind
                        is ReadQueryGroundingSource.REQUEST
                        for item in result.grounding
                    )
                )

    def test_negative_semantic_outcomes_never_contain_query_data(self):
        cases = (
            (
                "Delete all observations.",
                ReadQueryStatus.UNSUPPORTED,
            ),
            (
                "Predict the next observed value.",
                ReadQueryStatus.UNSUPPORTED,
            ),
            (
                "Which value should I choose?",
                ReadQueryStatus.UNSUPPORTED,
            ),
            (
                "Write a poem about category alpha.",
                ReadQueryStatus.UNSUPPORTED,
            ),
            (
                "Show alpha or beta observations with value 18.",
                ReadQueryStatus.AMBIGUOUS,
            ),
        )

        for request_text, expected_status in cases:
            with self.subTest(
                request=request_text,
                status=expected_status,
            ):
                response = {
                    "status": expected_status.value,
                    "normalized_interpretation": "",
                    "candidate_query": None,
                    "parameters": [],
                    "grounding": [],
                    "reason": "The complete request cannot be accepted.",
                }

                result = SemanticReadQueryInterpreter(
                    RecordingBackend(response),
                    query_context(),
                ).execute(
                    SemanticReadQueryRequest(
                        text=request_text,
                        language="en",
                    )
                )

                self.assertEqual(result.status, expected_status)
                self.assertIsNone(result.candidate_query)
                self.assertEqual(result.parameters, ())
                self.assertEqual(result.grounding, ())
                self.assertTrue(result.reason)

    def test_result_models_are_immutable(self):
        result = ReadQueryInterpretation(
            status=ReadQueryStatus.UNSUPPORTED,
            normalized_interpretation="",
            candidate_query=None,
            parameters=(),
            grounding=(),
            reason="Outside the configured domain.",
            context_id="example.read_query",
            context_revision="1",
            language="en",
        )

        with self.assertRaises((AttributeError, TypeError)):
            result.reason = "changed"



class SemanticQueryContextLoaderTests(unittest.TestCase):
    def context_mapping(self):
        return {
            "context_id": "example.read_query",
            "revision": "1",
            "dialect": "sqlite",
            "languages": ["it", "en"],
            "domain_description": (
                "Historical observations stored by the consumer."
            ),
            "relations": [
                {
                    "name": "observations",
                    "kind": "view",
                    "description": "Read-only historical observations.",
                    "columns": [
                        {
                            "name": "observed_at",
                            "data_type": "date",
                            "description": "Civil observation date.",
                        },
                        {
                            "name": "value",
                            "data_type": "integer",
                            "description": "Observed integer value.",
                        },
                    ],
                }
            ],
            "concepts": [
                {
                    "name": "measurement",
                    "description": "A numeric historical observation.",
                    "synonyms": ["value", "amount"],
                }
            ],
            "relationships": [],
            "limits": {
                "max_result_rows": 500,
                "max_relations": 1,
            },
            "semantic_rules": [
                "latest means the latest available observation"
            ],
            "accepted_examples": [
                "Show the latest observation."
            ],
            "rejected_examples": [
                "Delete the latest observation."
            ],
            "allowed_query_features": [
                "filter",
                "order",
                "limit",
            ],
        }

    def test_constructs_typed_context_from_mapping(self):
        context = semantic_query_context_from_mapping(
            self.context_mapping()
        )

        self.assertIsInstance(context, SemanticQueryContext)
        self.assertEqual(context.languages, ("it", "en"))
        self.assertEqual(context.relations[0].kind, "view")
        self.assertIsInstance(
            context.relations[0],
            SemanticQueryRelation,
        )
        self.assertIsInstance(
            context.relations[0].columns[0],
            SemanticQueryColumn,
        )
        self.assertIsInstance(
            context.concepts[0],
            SemanticQueryConcept,
        )
        self.assertEqual(
            context.concepts[0].synonyms,
            ("value", "amount"),
        )
        self.assertEqual(context.relationships, ())
        self.assertEqual(context.limits.max_result_rows, 500)
        self.assertEqual(context.limits.max_relations, 1)

    def test_rejects_extra_or_missing_context_fields(self):
        extra = self.context_mapping()
        extra["provider"] = "ollama"
        missing = self.context_mapping()
        del missing["revision"]

        for raw in (extra, missing):
            with self.subTest(raw=raw):
                with self.assertRaises(AIConfigurationError):
                    semantic_query_context_from_mapping(raw)

    def test_rejects_extra_or_malformed_nested_fields(self):
        extra_column = self.context_mapping()
        extra_column["relations"][0]["columns"][0]["sql"] = (
            "DROP TABLE observations"
        )

        malformed_relation = self.context_mapping()
        malformed_relation["relations"][0]["columns"] = "observed_at"

        for raw in (extra_column, malformed_relation):
            with self.subTest(raw=raw):
                with self.assertRaises(AIConfigurationError):
                    semantic_query_context_from_mapping(raw)

    def test_rejects_malformed_semantic_support_fields(self):
        malformed_synonyms = self.context_mapping()
        malformed_synonyms["concepts"][0]["synonyms"] = "value"

        dangling_relationship = self.context_mapping()
        dangling_relationship["relationships"] = [
            {
                "name": "missing relation",
                "left_relation": "observations",
                "left_column": "observed_at",
                "right_relation": "missing",
                "right_column": "value",
                "description": "Invalid relationship endpoint.",
            }
        ]

        boolean_limit = self.context_mapping()
        boolean_limit["limits"]["max_result_rows"] = True

        excessive_relation_limit = self.context_mapping()
        excessive_relation_limit["limits"]["max_relations"] = 2

        for raw in (
            malformed_synonyms,
            dangling_relationship,
            boolean_limit,
            excessive_relation_limit,
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(AIConfigurationError):
                    semantic_query_context_from_mapping(raw)

    def test_loader_does_not_mutate_consumer_mapping(self):
        raw = self.context_mapping()
        original_languages = list(raw["languages"])
        original_columns = [
            dict(column)
            for column in raw["relations"][0]["columns"]
        ]

        semantic_query_context_from_mapping(raw)

        self.assertEqual(raw["languages"], original_languages)
        self.assertEqual(
            raw["relations"][0]["columns"],
            original_columns,
        )



if __name__ == "__main__":
    unittest.main()
