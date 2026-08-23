from collections.abc import Mapping

from .errors import AIInvalidResponseError
from .models import LogAnalysis, Severity


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
