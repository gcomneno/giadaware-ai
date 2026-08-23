class AIError(Exception):
    """Base exception for GiadaWare AI Capability."""


class AIUnavailableError(AIError):
    """The configured AI backend is unavailable."""


class AITimeoutError(AIError):
    """The AI backend did not respond within the configured timeout."""


class AIInvalidResponseError(AIError):
    """The AI backend returned malformed or semantically invalid data."""


class AIUnsupportedCapabilityError(AIError):
    """The selected backend does not support the requested capability."""


class AIConfigurationError(AIError):
    """The AI capability or backend configuration is invalid."""
