from __future__ import annotations

import math
import re
from collections.abc import Mapping

from .errors import AIConfigurationError, AIInvalidResponseError
from .models import (
    ClaimSupport,
    LearningSourceAnalysis,
    LogAnalysis,
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
    Severity,
    SourceClaim,
    TranslationResult,
)


_READ_QUERY_FIELDS = frozenset(
    {
        "status",
        "normalized_interpretation",
        "candidate_query",
        "parameters",
        "grounding",
        "reason",
    }
)


def _require_string(
    data: Mapping[str, object],
    key: str,
) -> str:
    value = data.get(key)

    if not isinstance(value, str) or not value.strip():
        raise AIInvalidResponseError(
            f"{key!r} must be a non-empty string"
        )

    return value.strip()


def _require_string_list(
    data: Mapping[str, object],
    key: str,
) -> tuple[str, ...]:
    value = data.get(key)

    if not isinstance(value, list):
        raise AIInvalidResponseError(
            f"{key!r} must be a list"
        )

    result: list[str] = []

    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise AIInvalidResponseError(
                f"{key!r} must contain only non-empty strings"
            )
        result.append(item.strip())

    return tuple(result)


def _require_source_claims(
    data: Mapping[str, object],
    key: str = "source_claims",
) -> tuple[SourceClaim, ...]:
    value = data.get(key)

    if not isinstance(value, list):
        raise AIInvalidResponseError(
            f"{key!r} must be a list"
        )

    result: list[SourceClaim] = []

    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise AIInvalidResponseError(
                f"{key!r}[{index}] must be an object"
            )

        claim = _require_string(item, "claim")
        support_raw = _require_string(item, "support")

        try:
            support = ClaimSupport(support_raw)
        except ValueError as exc:
            raise AIInvalidResponseError(
                f"invalid claim support: {support_raw!r}"
            ) from exc

        result.append(SourceClaim(claim=claim, support=support))

    return tuple(result)


def validate_log_analysis(
    data: Mapping[str, object],
) -> LogAnalysis:
    summary = _require_string(data, "summary")
    severity_raw = _require_string(data, "severity")

    try:
        severity = Severity(severity_raw)
    except ValueError as exc:
        raise AIInvalidResponseError(
            f"invalid severity: {severity_raw!r}"
        ) from exc

    possible_causes = _require_string_list(
        data,
        "possible_causes",
    )

    suggested_next_steps = _require_string_list(
        data,
        "suggested_next_steps",
    )

    return LogAnalysis(
        summary=summary,
        severity=severity,
        possible_causes=possible_causes,
        suggested_next_steps=suggested_next_steps,
    )


def validate_learning_source_analysis(
    data: Mapping[str, object],
) -> LearningSourceAnalysis:
    return LearningSourceAnalysis(
        central_thesis=_require_string(data, "central_thesis"),
        key_concepts=_require_string_list(data, "key_concepts"),
        source_claims=_require_source_claims(data),
        practical_applications=_require_string_list(
            data,
            "practical_applications",
        ),
        limitations=_require_string_list(data, "limitations"),
        review_questions=_require_string_list(data, "review_questions"),
    )


def validate_translation_result(
    data: Mapping[str, object],
    *,
    source_language: str,
    target_language: str,
) -> TranslationResult:
    translated_text = _require_string(data, "translated_text")
    returned_source = _require_string(data, "source_language")
    returned_target = _require_string(data, "target_language")

    if returned_source != source_language:
        raise AIInvalidResponseError(
            "translation result source_language does not match request"
        )

    if returned_target != target_language:
        raise AIInvalidResponseError(
            "translation result target_language does not match request"
        )

    return TranslationResult(
        translated_text=translated_text,
        source_language=returned_source,
        target_language=returned_target,
    )


def _configuration_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AIConfigurationError(f"{field} must be a non-empty string")
    return value.strip()


def _configuration_strings(
    value: object,
    field: str,
    *,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise AIConfigurationError(f"{field} must be a tuple")
    if not allow_empty and not value:
        raise AIConfigurationError(f"{field} must not be empty")

    normalized: list[str] = []
    for item in value:
        normalized.append(_configuration_text(item, field))

    if len(set(normalized)) != len(normalized):
        raise AIConfigurationError(f"{field} must not contain duplicates")
    return tuple(normalized)


def _validate_relation(
    relation: object,
    index: int,
) -> SemanticQueryRelation:
    if not isinstance(relation, SemanticQueryRelation):
        raise AIConfigurationError(
            f"relations[{index}] must be a SemanticQueryRelation"
        )

    name = _configuration_text(relation.name, f"relations[{index}].name")
    kind = _configuration_text(relation.kind, f"relations[{index}].kind")
    if kind not in {"table", "view"}:
        raise AIConfigurationError(
            f"relations[{index}].kind must be 'table' or 'view'"
        )
    description = _configuration_text(
        relation.description,
        f"relations[{index}].description",
    )
    if not isinstance(relation.columns, tuple) or not relation.columns:
        raise AIConfigurationError(
            f"relations[{index}].columns must be a non-empty tuple"
        )

    column_names: set[str] = set()
    normalized_columns: list[SemanticQueryColumn] = []
    for column_index, column in enumerate(relation.columns):
        if not isinstance(column, SemanticQueryColumn):
            raise AIConfigurationError(
                f"relations[{index}].columns[{column_index}] "
                "must be a SemanticQueryColumn"
            )
        column_name = _configuration_text(
            column.name,
            f"relations[{index}].columns[{column_index}].name",
        )
        data_type = _configuration_text(
            column.data_type,
            f"relations[{index}].columns[{column_index}].data_type",
        )
        column_description = _configuration_text(
            column.description,
            f"relations[{index}].columns[{column_index}].description",
        )
        if column_name in column_names:
            raise AIConfigurationError(
                f"duplicate column {column_name!r} in relation {name!r}"
            )
        column_names.add(column_name)
        normalized_columns.append(
            SemanticQueryColumn(
                name=column_name,
                data_type=data_type,
                description=column_description,
            )
        )

    return SemanticQueryRelation(
        name=name,
        kind=kind,
        description=description,
        columns=tuple(normalized_columns),
    )


_CONTEXT_FIELDS = frozenset(
    {
        "context_id",
        "revision",
        "dialect",
        "languages",
        "domain_description",
        "relations",
        "concepts",
        "relationships",
        "limits",
        "semantic_rules",
        "accepted_examples",
        "rejected_examples",
        "allowed_query_features",
    }
)
_RELATION_FIELDS = frozenset(
    {"name", "kind", "description", "columns"}
)
_COLUMN_FIELDS = frozenset(
    {"name", "data_type", "description"}
)
_CONCEPT_FIELDS = frozenset(
    {"name", "description", "synonyms"}
)
_RELATIONSHIP_FIELDS = frozenset(
    {
        "name",
        "left_relation",
        "left_column",
        "right_relation",
        "right_column",
        "description",
    }
)
_LIMIT_FIELDS = frozenset(
    {"max_result_rows", "max_relations"}
)


def _require_configuration_fields(
    data: Mapping[str, object],
    expected: frozenset[str],
    label: str,
) -> None:
    actual = set(data)
    if actual == expected:
        return

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    details: list[str] = []
    if missing:
        details.append("missing: " + ", ".join(missing))
    if extra:
        details.append("extra: " + ", ".join(extra))
    raise AIConfigurationError(
        f"invalid {label} fields (" + "; ".join(details) + ")"
    )


def _mapping_string(
    data: Mapping[str, object],
    key: str,
    label: str,
) -> str:
    value = data[key]
    if not isinstance(value, str) or not value.strip():
        raise AIConfigurationError(
            f"{label}.{key} must be a non-empty string"
        )
    return value.strip()


def _mapping_string_list(
    data: Mapping[str, object],
    key: str,
    label: str,
) -> tuple[str, ...]:
    value = data[key]
    if not isinstance(value, list):
        raise AIConfigurationError(
            f"{label}.{key} must be a list"
        )

    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise AIConfigurationError(
                f"{label}.{key}[{index}] must be a non-empty string"
            )
        result.append(item.strip())
    return tuple(result)


def _mapping_positive_integer(
    data: Mapping[str, object],
    key: str,
    label: str,
) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AIConfigurationError(
            f"{label}.{key} must be a positive integer"
        )
    return value


def semantic_query_context_from_mapping(
    data: Mapping[str, object],
) -> SemanticQueryContext:
    """Construct and validate an immutable context from decoded JSON data."""

    if not isinstance(data, Mapping):
        raise AIConfigurationError(
            "semantic query context must be an object"
        )
    _require_configuration_fields(
        data,
        _CONTEXT_FIELDS,
        "semantic query context",
    )

    raw_relations = data["relations"]
    if not isinstance(raw_relations, list):
        raise AIConfigurationError(
            "semantic query context.relations must be a list"
        )

    relations: list[SemanticQueryRelation] = []
    for relation_index, raw_relation in enumerate(raw_relations):
        relation_label = f"relations[{relation_index}]"
        if not isinstance(raw_relation, Mapping):
            raise AIConfigurationError(
                f"{relation_label} must be an object"
            )
        _require_configuration_fields(
            raw_relation,
            _RELATION_FIELDS,
            relation_label,
        )

        raw_columns = raw_relation["columns"]
        if not isinstance(raw_columns, list):
            raise AIConfigurationError(
                f"{relation_label}.columns must be a list"
            )

        columns: list[SemanticQueryColumn] = []
        for column_index, raw_column in enumerate(raw_columns):
            column_label = (
                f"{relation_label}.columns[{column_index}]"
            )
            if not isinstance(raw_column, Mapping):
                raise AIConfigurationError(
                    f"{column_label} must be an object"
                )
            _require_configuration_fields(
                raw_column,
                _COLUMN_FIELDS,
                column_label,
            )
            columns.append(
                SemanticQueryColumn(
                    name=_mapping_string(
                        raw_column,
                        "name",
                        column_label,
                    ),
                    data_type=_mapping_string(
                        raw_column,
                        "data_type",
                        column_label,
                    ),
                    description=_mapping_string(
                        raw_column,
                        "description",
                        column_label,
                    ),
                )
            )

        relations.append(
            SemanticQueryRelation(
                name=_mapping_string(
                    raw_relation,
                    "name",
                    relation_label,
                ),
                kind=_mapping_string(
                    raw_relation,
                    "kind",
                    relation_label,
                ),
                description=_mapping_string(
                    raw_relation,
                    "description",
                    relation_label,
                ),
                columns=tuple(columns),
            )
        )

    raw_concepts = data["concepts"]
    if not isinstance(raw_concepts, list):
        raise AIConfigurationError(
            "semantic query context.concepts must be a list"
        )

    concepts: list[SemanticQueryConcept] = []
    for concept_index, raw_concept in enumerate(raw_concepts):
        concept_label = f"concepts[{concept_index}]"
        if not isinstance(raw_concept, Mapping):
            raise AIConfigurationError(
                f"{concept_label} must be an object"
            )
        _require_configuration_fields(
            raw_concept,
            _CONCEPT_FIELDS,
            concept_label,
        )
        concepts.append(
            SemanticQueryConcept(
                name=_mapping_string(
                    raw_concept,
                    "name",
                    concept_label,
                ),
                description=_mapping_string(
                    raw_concept,
                    "description",
                    concept_label,
                ),
                synonyms=_mapping_string_list(
                    raw_concept,
                    "synonyms",
                    concept_label,
                ),
            )
        )

    raw_relationships = data["relationships"]
    if not isinstance(raw_relationships, list):
        raise AIConfigurationError(
            "semantic query context.relationships must be a list"
        )

    relationships: list[SemanticQueryRelationship] = []
    for relationship_index, raw_relationship in enumerate(
        raw_relationships
    ):
        relationship_label = f"relationships[{relationship_index}]"
        if not isinstance(raw_relationship, Mapping):
            raise AIConfigurationError(
                f"{relationship_label} must be an object"
            )
        _require_configuration_fields(
            raw_relationship,
            _RELATIONSHIP_FIELDS,
            relationship_label,
        )
        relationships.append(
            SemanticQueryRelationship(
                name=_mapping_string(
                    raw_relationship,
                    "name",
                    relationship_label,
                ),
                left_relation=_mapping_string(
                    raw_relationship,
                    "left_relation",
                    relationship_label,
                ),
                left_column=_mapping_string(
                    raw_relationship,
                    "left_column",
                    relationship_label,
                ),
                right_relation=_mapping_string(
                    raw_relationship,
                    "right_relation",
                    relationship_label,
                ),
                right_column=_mapping_string(
                    raw_relationship,
                    "right_column",
                    relationship_label,
                ),
                description=_mapping_string(
                    raw_relationship,
                    "description",
                    relationship_label,
                ),
            )
        )

    raw_limits = data["limits"]
    if not isinstance(raw_limits, Mapping):
        raise AIConfigurationError(
            "semantic query context.limits must be an object"
        )
    _require_configuration_fields(
        raw_limits,
        _LIMIT_FIELDS,
        "limits",
    )
    limits = SemanticQueryLimits(
        max_result_rows=_mapping_positive_integer(
            raw_limits,
            "max_result_rows",
            "limits",
        ),
        max_relations=_mapping_positive_integer(
            raw_limits,
            "max_relations",
            "limits",
        ),
    )

    context = SemanticQueryContext(
        context_id=_mapping_string(
            data,
            "context_id",
            "semantic query context",
        ),
        revision=_mapping_string(
            data,
            "revision",
            "semantic query context",
        ),
        dialect=_mapping_string(
            data,
            "dialect",
            "semantic query context",
        ),
        languages=_mapping_string_list(
            data,
            "languages",
            "semantic query context",
        ),
        domain_description=_mapping_string(
            data,
            "domain_description",
            "semantic query context",
        ),
        relations=tuple(relations),
        concepts=tuple(concepts),
        relationships=tuple(relationships),
        limits=limits,
        semantic_rules=_mapping_string_list(
            data,
            "semantic_rules",
            "semantic query context",
        ),
        accepted_examples=_mapping_string_list(
            data,
            "accepted_examples",
            "semantic query context",
        ),
        rejected_examples=_mapping_string_list(
            data,
            "rejected_examples",
            "semantic query context",
        ),
        allowed_query_features=_mapping_string_list(
            data,
            "allowed_query_features",
            "semantic query context",
        ),
    )
    return validate_semantic_query_context(context)


def _validate_concepts(
    concepts: object,
) -> tuple[SemanticQueryConcept, ...]:
    if not isinstance(concepts, tuple):
        raise AIConfigurationError("concepts must be a tuple")

    normalized: list[SemanticQueryConcept] = []
    names: set[str] = set()

    for index, concept in enumerate(concepts):
        if not isinstance(concept, SemanticQueryConcept):
            raise AIConfigurationError(
                f"concepts[{index}] must be a SemanticQueryConcept"
            )

        name = _configuration_text(
            concept.name,
            f"concepts[{index}].name",
        )
        if name in names:
            raise AIConfigurationError(
                f"duplicate semantic concept: {name!r}"
            )
        names.add(name)

        normalized.append(
            SemanticQueryConcept(
                name=name,
                description=_configuration_text(
                    concept.description,
                    f"concepts[{index}].description",
                ),
                synonyms=_configuration_strings(
                    concept.synonyms,
                    f"concepts[{index}].synonyms",
                ),
            )
        )

    return tuple(normalized)


def _validate_relationships(
    relationships: object,
    relations: tuple[SemanticQueryRelation, ...],
) -> tuple[SemanticQueryRelationship, ...]:
    if not isinstance(relationships, tuple):
        raise AIConfigurationError("relationships must be a tuple")

    relation_columns = {
        relation.name: {
            column.name
            for column in relation.columns
        }
        for relation in relations
    }
    normalized: list[SemanticQueryRelationship] = []
    names: set[str] = set()

    for index, relationship in enumerate(relationships):
        if not isinstance(
            relationship,
            SemanticQueryRelationship,
        ):
            raise AIConfigurationError(
                f"relationships[{index}] must be a "
                "SemanticQueryRelationship"
            )

        label = f"relationships[{index}]"
        name = _configuration_text(
            relationship.name,
            f"{label}.name",
        )
        if name in names:
            raise AIConfigurationError(
                f"duplicate semantic relationship: {name!r}"
            )
        names.add(name)

        left_relation = _configuration_text(
            relationship.left_relation,
            f"{label}.left_relation",
        )
        left_column = _configuration_text(
            relationship.left_column,
            f"{label}.left_column",
        )
        right_relation = _configuration_text(
            relationship.right_relation,
            f"{label}.right_relation",
        )
        right_column = _configuration_text(
            relationship.right_column,
            f"{label}.right_column",
        )

        for side, relation_name, column_name in (
            ("left", left_relation, left_column),
            ("right", right_relation, right_column),
        ):
            if relation_name not in relation_columns:
                raise AIConfigurationError(
                    f"{label}.{side}_relation references unknown "
                    f"relation {relation_name!r}"
                )
            if column_name not in relation_columns[relation_name]:
                raise AIConfigurationError(
                    f"{label}.{side}_column references unknown "
                    f"column {column_name!r} in relation "
                    f"{relation_name!r}"
                )

        normalized.append(
            SemanticQueryRelationship(
                name=name,
                left_relation=left_relation,
                left_column=left_column,
                right_relation=right_relation,
                right_column=right_column,
                description=_configuration_text(
                    relationship.description,
                    f"{label}.description",
                ),
            )
        )

    return tuple(normalized)


def _validate_limits(
    limits: object,
    relation_count: int,
) -> SemanticQueryLimits:
    if not isinstance(limits, SemanticQueryLimits):
        raise AIConfigurationError(
            "limits must be a SemanticQueryLimits"
        )

    for field_name, value in (
        ("max_result_rows", limits.max_result_rows),
        ("max_relations", limits.max_relations),
    ):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise AIConfigurationError(
                f"limits.{field_name} must be a positive integer"
            )

    if limits.max_relations > relation_count:
        raise AIConfigurationError(
            "limits.max_relations must not exceed the number "
            "of declared relations"
        )

    return SemanticQueryLimits(
        max_result_rows=limits.max_result_rows,
        max_relations=limits.max_relations,
    )


def validate_semantic_query_context(
    context: object,
) -> SemanticQueryContext:
    """Validate consumer configuration before any backend inference."""

    if not isinstance(context, SemanticQueryContext):
        raise AIConfigurationError(
            "context must be a SemanticQueryContext"
        )

    context_id = _configuration_text(context.context_id, "context_id")
    revision = _configuration_text(context.revision, "revision")
    dialect = _configuration_text(context.dialect, "dialect")
    languages = _configuration_strings(
        context.languages,
        "languages",
        allow_empty=False,
    )
    domain_description = _configuration_text(
        context.domain_description,
        "domain_description",
    )

    if not isinstance(context.relations, tuple) or not context.relations:
        raise AIConfigurationError("relations must be a non-empty tuple")
    relations = tuple(
        _validate_relation(relation, index)
        for index, relation in enumerate(context.relations)
    )
    relation_names = [relation.name for relation in relations]
    if len(set(relation_names)) != len(relation_names):
        raise AIConfigurationError("relation names must be unique")

    concepts = _validate_concepts(context.concepts)
    relationships = _validate_relationships(
        context.relationships,
        relations,
    )
    limits = _validate_limits(
        context.limits,
        len(relations),
    )

    return SemanticQueryContext(
        context_id=context_id,
        revision=revision,
        dialect=dialect,
        languages=languages,
        domain_description=domain_description,
        relations=relations,
        concepts=concepts,
        relationships=relationships,
        limits=limits,
        semantic_rules=_configuration_strings(
            context.semantic_rules,
            "semantic_rules",
        ),
        accepted_examples=_configuration_strings(
            context.accepted_examples,
            "accepted_examples",
        ),
        rejected_examples=_configuration_strings(
            context.rejected_examples,
            "rejected_examples",
        ),
        allowed_query_features=_configuration_strings(
            context.allowed_query_features,
            "allowed_query_features",
        ),
    )


def _optional_response_string(
    data: Mapping[str, object],
    key: str,
) -> str | None:
    value = data[key]
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise AIInvalidResponseError(
            f"{key!r} must be null or a non-empty string"
        )
    return value.strip()


def _read_query_parameters(value: object) -> tuple[ReadQueryParameter, ...]:
    if not isinstance(value, list):
        raise AIInvalidResponseError("'parameters' must be a list")

    parameters: list[ReadQueryParameter] = []
    names: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != {"name", "value"}:
            raise AIInvalidResponseError(
                f"parameters[{index}] must contain exactly name and value"
            )
        name = _require_string(item, "name")
        parameter_value = item["value"]
        if not (
            parameter_value is None
            or isinstance(parameter_value, (str, int, float, bool))
        ):
            raise AIInvalidResponseError(
                f"parameters[{index}].value must be a JSON scalar"
            )
        if (
            isinstance(parameter_value, float)
            and not math.isfinite(parameter_value)
        ):
            raise AIInvalidResponseError(
                f"parameters[{index}].value must be finite"
            )
        if name in names:
            raise AIInvalidResponseError(
                f"duplicate read-query parameter: {name!r}"
            )
        names.add(name)
        parameters.append(
            ReadQueryParameter(name=name, value=parameter_value)
        )
    return tuple(parameters)


def _parameter_value_reference(parameter: ReadQueryParameter) -> str:
    value = parameter.value
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        if not value:
            raise AIInvalidResponseError(
                f"parameter {parameter.name!r} has no groundable value"
            )
        return value
    return str(value)


def _read_query_grounding(
    value: object,
    *,
    request_text: str,
    candidate_query: str | None,
    parameters: tuple[ReadQueryParameter, ...],
    context: SemanticQueryContext,
) -> tuple[ReadQueryGrounding, ...]:
    if not isinstance(value, list):
        raise AIInvalidResponseError("'grounding' must be a list")

    grounding: list[ReadQueryGrounding] = []
    parameters_by_name = {item.name: item for item in parameters}
    grounded_parameters: set[str] = set()

    expected_fields = {
        "query_fragment",
        "field",
        "source_kind",
        "source_reference",
    }

    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != expected_fields:
            raise AIInvalidResponseError(
                f"grounding[{index}] must contain exactly "
                "query_fragment, field, source_kind and source_reference"
            )

        query_fragment = _require_string(item, "query_fragment")
        field = _require_string(item, "field")
        source_raw = _require_string(item, "source_kind")
        source_reference = _require_string(
            item,
            "source_reference",
        )

        try:
            source_kind = ReadQueryGroundingSource(source_raw)
        except ValueError as error:
            raise AIInvalidResponseError(
                f"invalid grounding source_kind: {source_raw!r}"
            ) from error

        if (
            candidate_query is None
            or query_fragment not in candidate_query
        ):
            raise AIInvalidResponseError(
                f"grounding[{index}].query_fragment is absent "
                "from candidate_query"
            )

        if source_kind is ReadQueryGroundingSource.REQUEST:
            if source_reference not in request_text:
                raise AIInvalidResponseError(
                    f"grounding[{index}].source_reference is absent "
                    "from the request"
                )
        elif source_reference not in context.semantic_rules:
            raise AIInvalidResponseError(
                f"grounding[{index}].source_reference is not an "
                "exact semantic context rule"
            )

        parameter = parameters_by_name.get(field)
        if parameter is not None:
            if field in grounded_parameters:
                raise AIInvalidResponseError(
                    f"duplicate grounding for parameter: {field!r}"
                )
            grounded_parameters.add(field)

            placeholder = f":{field}"
            placeholder_pattern = (
                re.escape(placeholder) + r"(?![A-Za-z0-9_])"
            )
            if re.search(placeholder_pattern, query_fragment) is None:
                raise AIInvalidResponseError(
                    f"grounding[{index}].query_fragment does not contain "
                    f"exact parameter placeholder {placeholder!r}"
                )

            value_reference = _parameter_value_reference(parameter)
            value_pattern = (
                r"(?<!\w)"
                + re.escape(value_reference)
                + r"(?!\w)"
            )
            if re.search(value_pattern, source_reference) is None:
                raise AIInvalidResponseError(
                    f"parameter {field!r} value is not supported by "
                    "its grounding source_reference"
                )

        grounding.append(
            ReadQueryGrounding(
                query_fragment=query_fragment,
                field=field,
                source_kind=source_kind,
                source_reference=source_reference,
            )
        )

    return tuple(grounding)

def _validate_candidate_result_limit(
    candidate_query: str,
    limits: SemanticQueryLimits,
) -> None:
    matches = re.findall(
        r"\bLIMIT\s+(\d+)\b",
        candidate_query,
        flags=re.IGNORECASE,
    )
    if len(matches) != 1:
        raise AIInvalidResponseError(
            "accepted candidate_query must contain exactly one "
            "literal LIMIT"
        )

    result_limit = int(matches[0])
    if result_limit <= 0:
        raise AIInvalidResponseError(
            "candidate_query LIMIT must be positive"
        )
    if result_limit > limits.max_result_rows:
        raise AIInvalidResponseError(
            "candidate_query LIMIT exceeds "
            "context.limits.max_result_rows"
        )


def _validate_candidate_relation_limit(
    candidate_query: str,
    limits: SemanticQueryLimits,
) -> None:
    relation_references = re.findall(
        r"\b(?:FROM|JOIN)\s+[A-Za-z_][A-Za-z0-9_.]*\b",
        candidate_query,
        flags=re.IGNORECASE,
    )
    if len(relation_references) > limits.max_relations:
        raise AIInvalidResponseError(
            "candidate_query relation count exceeds "
            "context.limits.max_relations"
        )


def validate_read_query_interpretation(
    data: Mapping[str, object],
    *,
    context: SemanticQueryContext,
    request: str,
    language: str,
) -> ReadQueryInterpretation:
    """Validate untrusted inference and add trusted invocation identity."""

    if not isinstance(data, Mapping):
        raise AIInvalidResponseError(
            "read-query interpretation must be an object"
        )
    if set(data) != _READ_QUERY_FIELDS:
        missing = sorted(_READ_QUERY_FIELDS - set(data))
        extra = sorted(set(data) - _READ_QUERY_FIELDS)
        details: list[str] = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise AIInvalidResponseError(
            "invalid read-query fields (" + "; ".join(details) + ")"
        )

    status_raw = _require_string(data, "status")
    try:
        status = ReadQueryStatus(status_raw)
    except ValueError as error:
        raise AIInvalidResponseError(
            f"invalid read-query status: {status_raw!r}"
        ) from error

    normalized_value = data["normalized_interpretation"]
    if not isinstance(normalized_value, str):
        raise AIInvalidResponseError(
            "'normalized_interpretation' must be a string"
        )
    normalized = normalized_value.strip()
    candidate_query = _optional_response_string(data, "candidate_query")
    reason = _optional_response_string(data, "reason")
    parameters = _read_query_parameters(data["parameters"])
    grounding = _read_query_grounding(
        data["grounding"],
        request_text=request,
        candidate_query=candidate_query,
        parameters=parameters,
        context=context,
    )

    if status is ReadQueryStatus.ACCEPTED:
        if not normalized:
            raise AIInvalidResponseError(
                "accepted interpretation requires normalized_interpretation"
            )
        if candidate_query is None:
            raise AIInvalidResponseError(
                "accepted interpretation requires candidate_query"
            )
        if reason is not None:
            raise AIInvalidResponseError(
                "accepted interpretation must not contain a reason"
            )
        _validate_candidate_result_limit(
            candidate_query,
            context.limits,
        )
        _validate_candidate_relation_limit(
            candidate_query,
            context.limits,
        )
        grounded_fields = {item.field for item in grounding}
        missing_grounding = {
            parameter.name
            for parameter in parameters
            if parameter.name not in grounded_fields
        }
        if missing_grounding:
            raise AIInvalidResponseError(
                "parameters without grounding: "
                + ", ".join(sorted(missing_grounding))
            )
    else:
        if candidate_query is not None or parameters or grounding:
            raise AIInvalidResponseError(
                "non-accepted interpretation must not contain query data"
            )
        if normalized:
            raise AIInvalidResponseError(
                "non-accepted interpretation must not be normalized"
            )
        if reason is None:
            raise AIInvalidResponseError(
                "non-accepted interpretation requires a reason"
            )

    return ReadQueryInterpretation(
        status=status,
        normalized_interpretation=normalized,
        candidate_query=candidate_query,
        parameters=parameters,
        grounding=grounding,
        reason=reason,
        context_id=context.context_id,
        context_revision=context.revision,
        language=language,
    )
