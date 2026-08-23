from .backend import AIBackend
from .extension import AnalyzeCapability
from .models import LogAnalysis
from .validation import validate_log_analysis


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


class AICapabilities:
    """Backwards-compatible facade over concrete semantic capabilities."""

    def __init__(self, backend: AIBackend) -> None:
        self._analyze_log = AnalyzeLogCapability(backend)

    def analyze_log(self, log_text: str) -> LogAnalysis:
        return self._analyze_log.execute(log_text)
