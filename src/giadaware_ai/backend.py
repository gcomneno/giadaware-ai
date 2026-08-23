from collections.abc import Mapping
from typing import Protocol


class AIBackend(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, object]:
        """Return structured AI output as a mapping."""
        ...
