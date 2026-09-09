from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ClaimSupport(str, Enum):
    """Relationship between a candidate claim and the supplied source text."""

    EXPLICIT = "explicit"
    INFERRED = "inferred"
    UNCLEAR = "unclear"


@dataclass(frozen=True, slots=True)
class LogAnalysis:
    summary: str
    severity: Severity
    possible_causes: tuple[str, ...]
    suggested_next_steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceClaim:
    claim: str
    support: ClaimSupport


@dataclass(frozen=True, slots=True)
class LearningSourceAnalysis:
    central_thesis: str
    key_concepts: tuple[str, ...]
    source_claims: tuple[SourceClaim, ...]
    practical_applications: tuple[str, ...]
    limitations: tuple[str, ...]
    review_questions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TranslationRequest:
    text: str
    source_language: str
    target_language: str


@dataclass(frozen=True, slots=True)
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str


class ReadQueryStatus(str, Enum):
    """Semantic outcome of a read-query interpretation."""

    ACCEPTED = "accepted"
    UNSUPPORTED = "unsupported"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True, slots=True)
class SemanticQueryColumn:
    name: str
    data_type: str
    description: str


@dataclass(frozen=True, slots=True)
class SemanticQueryRelation:
    name: str
    kind: str
    description: str
    columns: tuple[SemanticQueryColumn, ...]


@dataclass(frozen=True, slots=True)
class SemanticQueryConcept:
    """Consumer-declared domain concept and its accepted synonyms."""

    name: str
    description: str
    synonyms: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SemanticQueryRelationship:
    """Consumer-declared relationship between two readable columns."""

    name: str
    left_relation: str
    left_column: str
    right_relation: str
    right_column: str
    description: str


@dataclass(frozen=True, slots=True)
class SemanticQueryLimits:
    """Interpretation limits declared by the consumer."""

    max_result_rows: int
    max_relations: int


@dataclass(frozen=True, slots=True)
class SemanticQueryContext:
    """Consumer-owned, versioned semantic description of readable data."""

    context_id: str
    revision: str
    dialect: str
    languages: tuple[str, ...]
    domain_description: str
    relations: tuple[SemanticQueryRelation, ...]
    concepts: tuple[SemanticQueryConcept, ...]
    relationships: tuple[SemanticQueryRelationship, ...]
    limits: SemanticQueryLimits
    semantic_rules: tuple[str, ...]
    accepted_examples: tuple[str, ...]
    rejected_examples: tuple[str, ...]
    allowed_query_features: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SemanticReadQueryRequest:
    text: str
    language: str


ReadQueryScalar = str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class ReadQueryParameter:
    name: str
    value: ReadQueryScalar


class ReadQueryGroundingSource(str, Enum):
    """Trusted vocabulary for semantic grounding provenance."""

    REQUEST = "request"
    CONTEXT_RULE = "context_rule"


@dataclass(frozen=True, slots=True)
class ReadQueryGrounding:
    """Evidence connecting a query fragment to declared semantics."""

    query_fragment: str
    field: str
    source_kind: ReadQueryGroundingSource
    source_reference: str


@dataclass(frozen=True, slots=True)
class ReadQueryInterpretation:
    """Validated but untrusted candidate interpretation.

    The query remains consumer-controlled data and carries no execution
    authority.
    """

    status: ReadQueryStatus
    normalized_interpretation: str
    candidate_query: str | None
    parameters: tuple[ReadQueryParameter, ...]
    grounding: tuple[ReadQueryGrounding, ...]
    reason: str | None
    context_id: str
    context_revision: str
    language: str
