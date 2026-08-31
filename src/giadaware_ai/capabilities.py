from .backend import AIBackend
from .extension import AnalyzeCapability, TransformCapability
from .models import (
    LearningSourceAnalysis,
    LogAnalysis,
    TranslationRequest,
    TranslationResult,
)
from .validation import (
    validate_learning_source_analysis,
    validate_log_analysis,
    validate_translation_result,
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


_TRANSLATION_SYSTEM_PROMPT = """
You are a translation capability.

Translate the supplied text from the explicit source language to the explicit
target language while preserving its meaning.

You MUST NOT summarize, editorially rewrite, enrich, fact-correct, or add factual
content. Preserve names, numbers, dates, quantities, technical terms, quotations,
negation, uncertainty, and causal relationships. Preserve formatting such as
paragraph boundaries, lists, Markdown, and line breaks where practical.

Return only the requested structured translation result.
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


class TranslateTextCapability(
    TransformCapability[TranslationRequest, TranslationResult]
):
    """Translate text without provider coupling or editorial authority."""

    def execute(self, value: TranslationRequest) -> TranslationResult:
        if not isinstance(value, TranslationRequest):
            raise TypeError("value must be a TranslationRequest")

        text = value.text.strip()
        source_language = value.source_language.strip()
        target_language = value.target_language.strip()

        if not text:
            raise ValueError("translation text must not be empty")
        if not source_language:
            raise ValueError("source_language must not be empty")
        if not target_language:
            raise ValueError("target_language must not be empty")
        if source_language.casefold() == target_language.casefold():
            raise ValueError("source_language and target_language must differ")

        response_schema: dict[str, object] = {
            "type": "object",
            "properties": {
                "translated_text": {"type": "string"},
                "source_language": {
                    "type": "string",
                    "const": source_language,
                },
                "target_language": {
                    "type": "string",
                    "const": target_language,
                },
            },
            "required": [
                "translated_text",
                "source_language",
                "target_language",
            ],
            "additionalProperties": False,
        }

        raw = self._backend.generate_json(
            system_prompt=_TRANSLATION_SYSTEM_PROMPT,
            user_prompt=(
                f"Source language: {source_language}\n"
                f"Target language: {target_language}\n\n"
                "Text to translate:\n"
                f"{text}"
            ),
            response_schema=response_schema,
        )

        return validate_translation_result(
            raw,
            source_language=source_language,
            target_language=target_language,
        )


class AICapabilities:
    """Backwards-compatible facade over concrete semantic capabilities."""

    def __init__(self, backend: AIBackend) -> None:
        self._analyze_log = AnalyzeLogCapability(backend)
        self._analyze_learning_source = AnalyzeLearningSourceCapability(backend)
        self._translate_text = TranslateTextCapability(backend)

    def analyze_log(self, log_text: str) -> LogAnalysis:
        return self._analyze_log.execute(log_text)

    def analyze_learning_source(self, text: str) -> LearningSourceAnalysis:
        return self._analyze_learning_source.execute(text)

    def translate_text(
        self,
        text: str,
        *,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        return self._translate_text.execute(
            TranslationRequest(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
        )
