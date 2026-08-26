from collections.abc import Mapping
from typing import Protocol


class AIBackend(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        """Return JSON-object AI output, optionally constrained by JSON Schema.

        ``response_schema`` expresses a provider-independent structural request.
        It does not make the returned mapping trusted or canonical; consumer
        capabilities remain responsible for deterministic validation.
        """
        ...
