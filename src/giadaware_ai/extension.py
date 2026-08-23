from abc import ABC, abstractmethod
from enum import Enum
from typing import ClassVar, Generic, TypeVar

from .backend import AIBackend


InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")


class CapabilityFamily(str, Enum):
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    CLASSIFY = "classify"
    EXTRACT = "extract"
    COMPARE = "compare"
    EXPLAIN = "explain"
    IDENTIFY = "identify"
    GENERATE = "generate"
    PROPOSE = "propose"
    TRANSFORM = "transform"
    SYNTHESIZE = "synthesize"
    DETECT = "detect"


class SemanticCapability(ABC, Generic[InputT, ResultT]):
    """Provider-independent base contract for semantic AI capabilities."""

    family: ClassVar[CapabilityFamily]

    def __init__(self, backend: AIBackend) -> None:
        self._backend = backend

    @abstractmethod
    def execute(self, value: InputT) -> ResultT:
        """Return a validated semantic result without application side effects."""
        raise NotImplementedError


class AnalyzeCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.ANALYZE


class SummarizeCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.SUMMARIZE


class ClassifyCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.CLASSIFY


class ExtractCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.EXTRACT


class CompareCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.COMPARE


class ExplainCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.EXPLAIN


class IdentifyCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.IDENTIFY


class GenerateCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.GENERATE


class ProposeCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.PROPOSE


class TransformCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.TRANSFORM


class SynthesizeCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.SYNTHESIZE


class DetectCapability(SemanticCapability[InputT, ResultT], ABC):
    family = CapabilityFamily.DETECT
