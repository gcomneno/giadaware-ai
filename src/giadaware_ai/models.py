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
