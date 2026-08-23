from .backend import AIBackend
from .extension import AnalyzeCapability
from .models import LearningSourceAnalysis, LogAnalysis
from .validation import (
    validate_learning_source_analysis,
    validate_log_analysis,
)


_LOG_ANALYSIS_SYSTEM_PROMPT = """
You are a read-only technical log analyzer.

You MUST NOT claim to execute actions or modify anything.

Use only information supported by the supplied log.
Do not invent facts.

Return JSON only, with exactly these semantic fields:

summary
severity
possible_causes
suggested_next_steps

severity must be one of:

low
medium
high
unknown

possible_causes and suggested_next_steps must be arrays of strings.
""".strip()


_LEARNING_SOURCE_ANALYSIS_SYSTEM_PROMPT = """
You are a read-only learning-source analyzer.

Analyze only the supplied source material. Do not claim independent fact-checking,
verification, approval, publication readiness, or editorial authority.

Return JSON only with exactly these semantic fields:

central_thesis
key_concepts
source_claims
practical_applications
limitations
review_questions

central_thesis must be a non-empty string.
key_concepts, practical_applications, limitations, and review_questions must be
arrays of non-empty strings.

source_claims must be an array of objects. Each object must contain exactly:

claim
support

claim must be a non-empty string.
support must be one of:

explicit
inferred
unclear

support describes only how the candidate claim relates to the supplied source
text. It does not mean that the claim is true or independently verified.
""".strip()


class AnalyzeLogCapability(AnalyzeCapability[str, LogAnalysis]):
    """Concrete Analyze capability for technical logs."""

    def execute(self, value: str) -> LogAnalysis:
        if not isinstance(value, str):
            raise TypeError("log_text must be a string")

        if not value.strip():
            raise ValueError("log_text must not be empty")

        raw = self._backend.generate_json(
            system_prompt=_LOG_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=(
                "Analyze the following technical log.\n\n"
                f"{value}"
            ),
        )

        return validate_log_analysis(raw)


class AnalyzeLearningSourceCapability(
    AnalyzeCapability[str, LearningSourceAnalysis]
):
    """Analyze supplied learning material without editorial authority."""

    def execute(self, value: str) -> LearningSourceAnalysis:
        if not isinstance(value, str):
            raise TypeError("text must be a string")

        if not value.strip():
            raise ValueError("text must not be empty")

        raw = self._backend.generate_json(
            system_prompt=_LEARNING_SOURCE_ANALYSIS_SYSTEM_PROMPT,
            user_prompt=(
                "Analyze the following learning source.\n\n"
                f"{value}"
            ),
        )

        return validate_learning_source_analysis(raw)


class AICapabilities:
    """Backwards-compatible facade over concrete semantic capabilities."""

    def __init__(self, backend: AIBackend) -> None:
        self._analyze_log = AnalyzeLogCapability(backend)
        self._analyze_learning_source = AnalyzeLearningSourceCapability(backend)

    def analyze_log(self, log_text: str) -> LogAnalysis:
        return self._analyze_log.execute(log_text)

    def analyze_learning_source(self, text: str) -> LearningSourceAnalysis:
        return self._analyze_learning_source.execute(text)
