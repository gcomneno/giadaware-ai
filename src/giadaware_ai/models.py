from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class LogAnalysis:
    summary: str
    severity: Severity
    possible_causes: tuple[str, ...]
    suggested_next_steps: tuple[str, ...]
