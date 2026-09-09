"""Provider-independent semantic read-query interpretation."""

from __future__ import annotations

import json
from typing import Final

from .backend import AIBackend
from .errors import AIConfigurationError
from .extension import TransformCapability
from .models import (
    ReadQueryInterpretation,
    SemanticQueryContext,
    SemanticReadQueryRequest,
)
from .validation import (
    validate_read_query_interpretation,
    validate_semantic_query_context,
)


_SYSTEM_PROMPT: Final = """
You are a semantic interpreter for consumer-declared read-only data.

Interpret the complete natural-language request only against the supplied
semantic context. Return exactly one structured interpretation.

Choose exactly one status:

- "accepted": the entire request is representable as one read-only query over
  the declared relations, columns, rules and allowed query features;
- "unsupported": any part asks for mutation, administration, prediction,
  advice, generic chat, or information outside the declared domain;
- "ambiguous": a material interpretation choice cannot be resolved from the
  request or an explicit context rule.

Status selection happens before query construction. A request containing any
unsupported material is unsupported even if another clause could be queried.
Never convert a mutation or prediction into a historical SELECT.

Accepted shape:
- normalized_interpretation: concise natural-language meaning, never SQL;
- candidate_query: one parameterized read-query candidate;
- parameters: only concrete values required by that candidate;
- grounding: query fragments mapped to exact request evidence or an
  exact deterministic semantic context rule;
- reason: null.

Unsupported or ambiguous shape:
- normalized_interpretation: empty string;
- candidate_query: null;
- parameters: empty array;
- grounding: empty array;
- reason: a non-empty explanation.

Each grounding item must identify an exact query_fragment and field.
For source_kind "request", source_reference must be a verbatim substring of the
original natural-language request. For source_kind "context_rule",
source_reference must be one exact semantic rule from the supplied context.
Exact and verbatim matches are case-sensitive.
Every parameter must have one grounding item whose field equals the parameter
name, whose query_fragment contains the exact :name placeholder and whose
source_reference contains the parameter value in canonical scalar form
as a distinct token delimited by Unicode non-word characters or string
boundaries, not merely as part of a longer word or number.
An accepted candidate_query must contain exactly one positive literal LIMIT no
greater than limits.max_result_rows. This LIMIT is required directly by the
validated context and does not require a semantic rule. Each FROM or JOIN
relation reference counts toward limits.max_relations.
Do not invent filters, ordering or defaults unless an explicit context rule
deterministically requires them. Never execute the query and never claim
that a candidate is safe, authorized or correct.

Classification examples independent of any consumer domain:

Request: "Delete every record."
Result status: "unsupported"

Request: "Predict tomorrow's value."
Result status: "unsupported"

Request: "Write a poem about the dataset."
Result status: "unsupported"

If the context states that a missing selector is material:
Request: "Show the record."
Result status: "ambiguous"
""".strip()


_REQUIRED_RESPONSE_FIELDS: Final[list[str]] = [
    "status",
    "normalized_interpretation",
    "candidate_query",
    "parameters",
    "grounding",
    "reason",
]

_PARAMETER_ITEMS_SCHEMA: Final[dict[str, object]] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "value"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
        },
        "value": {
            "type": [
                "string",
                "integer",
                "number",
                "boolean",
                "null",
            ]
        },
    },
}

_GROUNDING_ITEMS_SCHEMA: Final[dict[str, object]] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "query_fragment",
        "field",
        "source_kind",
        "source_reference",
    ],
    "properties": {
        "query_fragment": {
            "type": "string",
            "minLength": 1,
        },
        "field": {
            "type": "string",
            "minLength": 1,
        },
        "source_kind": {
            "type": "string",
            "enum": ["request", "context_rule"],
        },
        "source_reference": {
            "type": "string",
            "minLength": 1,
        },
    },
}


def _non_accepted_schema(status: str) -> dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(_REQUIRED_RESPONSE_FIELDS),
        "properties": {
            "status": {"const": status},
            "normalized_interpretation": {"const": ""},
            "candidate_query": {"type": "null"},
            "parameters": {
                "type": "array",
                "maxItems": 0,
                "items": _PARAMETER_ITEMS_SCHEMA,
            },
            "grounding": {
                "type": "array",
                "maxItems": 0,
                "items": _GROUNDING_ITEMS_SCHEMA,
            },
            "reason": {
                "type": "string",
                "minLength": 1,
            },
        },
    }


_RESPONSE_SCHEMA: Final[dict[str, object]] = {
    "oneOf": [
        {
            "type": "object",
            "additionalProperties": False,
            "required": list(_REQUIRED_RESPONSE_FIELDS),
            "properties": {
                "status": {"const": "accepted"},
                "normalized_interpretation": {
                    "type": "string",
                    "minLength": 1,
                },
                "candidate_query": {
                    "type": "string",
                    "minLength": 1,
                },
                "parameters": {
                    "type": "array",
                    "items": _PARAMETER_ITEMS_SCHEMA,
                },
                "grounding": {
                    "type": "array",
                    "items": _GROUNDING_ITEMS_SCHEMA,
                },
                "reason": {"type": "null"},
            },
        },
        _non_accepted_schema("unsupported"),
        _non_accepted_schema("ambiguous"),
    ]
}


def _context_payload(context: SemanticQueryContext) -> dict[str, object]:
    return {
        "context_id": context.context_id,
        "revision": context.revision,
        "dialect": context.dialect,
        "languages": list(context.languages),
        "domain_description": context.domain_description,
        "relations": [
            {
                "name": relation.name,
                "kind": relation.kind,
                "description": relation.description,
                "columns": [
                    {
                        "name": column.name,
                        "data_type": column.data_type,
                        "description": column.description,
                    }
                    for column in relation.columns
                ],
            }
            for relation in context.relations
        ],
        "concepts": [
            {
                "name": concept.name,
                "description": concept.description,
                "synonyms": list(concept.synonyms),
            }
            for concept in context.concepts
        ],
        "relationships": [
            {
                "name": relationship.name,
                "left_relation": relationship.left_relation,
                "left_column": relationship.left_column,
                "right_relation": relationship.right_relation,
                "right_column": relationship.right_column,
                "description": relationship.description,
            }
            for relationship in context.relationships
        ],
        "limits": {
            "max_result_rows": context.limits.max_result_rows,
            "max_relations": context.limits.max_relations,
        },
        "semantic_rules": list(context.semantic_rules),
        "accepted_examples": list(context.accepted_examples),
        "rejected_examples": list(context.rejected_examples),
        "allowed_query_features": list(
            context.allowed_query_features
        ),
    }


class SemanticReadQueryInterpreter(
    TransformCapability[
        SemanticReadQueryRequest,
        ReadQueryInterpretation,
    ]
):
    """Interpret a natural request without executing or authorizing its query."""

    def __init__(
        self,
        backend: AIBackend,
        context: SemanticQueryContext,
    ) -> None:
        super().__init__(backend)
        self._context = validate_semantic_query_context(context)

    @property
    def context(self) -> SemanticQueryContext:
        return self._context

    def execute(
        self,
        value: SemanticReadQueryRequest,
    ) -> ReadQueryInterpretation:
        if not isinstance(value, SemanticReadQueryRequest):
            raise TypeError(
                "value must be a SemanticReadQueryRequest"
            )
        if not isinstance(value.text, str):
            raise TypeError("request text must be a string")
        request_text = value.text.strip()
        if not request_text:
            raise ValueError("request text must not be empty")
        if not isinstance(value.language, str):
            raise TypeError("request language must be a string")
        language = value.language.strip()
        if not language:
            raise AIConfigurationError(
                "request language must not be empty"
            )
        if language not in self._context.languages:
            raise AIConfigurationError(
                f"language {language!r} is not declared by context "
                f"{self._context.context_id!r}"
            )

        context_json = json.dumps(
            _context_payload(self._context),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        raw = self._backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=(
                "Semantic query context:\n"
                f"{context_json}\n\n"
                f"Request language: {language}\n"
                "Natural-language request:\n"
                f"{request_text}"
            ),
            response_schema=_RESPONSE_SCHEMA,
        )

        return validate_read_query_interpretation(
            raw,
            context=self._context,
            request=request_text,
            language=language,
        )
