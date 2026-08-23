from collections.abc import Mapping

from .errors import AIInvalidResponseError
from .models import (
    ClaimSupport,
    LearningSourceAnalysis,
    LogAnalysis,
    Severity,
    SourceClaim,
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
