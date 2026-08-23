# GiadaWare AI

Experimental infrastructure library for pluggable, read-only AI capabilities
in GiadaWare software.

**Status: Experimental M0. The public API may change before a stable release.**

GiadaWare AI lets application code depend on semantic AI capabilities rather
than specific models, providers, prompts, or transport protocols.

Core rule:

> AI processes and proposes; software validates, decides, and executes.

AI output is data, never authority.

## Current M0 capability

The first implemented capability is technical log analysis:

    analysis = ai.analyze_log(log_text)

Consumers receive a validated, typed `LogAnalysis`, not raw model output.

M0 currently provides:

- `AICapabilities`;
- `AIBackend` protocol;
- typed `LogAnalysis`;
- `Severity`;
- explicit AI failure types;
- structured-output validation;
- `OllamaBackend`;
- deterministic tests using a fake backend;
- an opt-in real Ollama integration test.

## Architectural principles

- AI is optional.
- AI has no mutation authority.
- Consumers depend on semantic capabilities, not prompts or models.
- AI output is treated as untrusted input.
- Outputs are validated before crossing the public library boundary.
- Backends are replaceable.
- Failures are explicit and typed.
- Local-first does not mean local-only.
- Local inference may be zero-cost, but free operation is not part of the API
  contract.

See `docs/ARCHITECTURE.md` for the architectural boundary and
`docs/SEMANTIC-CAPABILITY-CONTRACT.md` for the normative semantic capability
contract.

## Example

    from giadaware_ai import AICapabilities
    from giadaware_ai.backends import OllamaBackend

    backend = OllamaBackend(
        model="qwen2.5:1.5b-instruct",
        base_url="http://localhost:11434",
    )

    ai = AICapabilities(backend)

    result = ai.analyze_log(
        "ERROR Connection refused: database unavailable"
    )

    print(result.summary)
    print(result.severity)

## Installation

M0 is not yet published to PyPI.

Build a wheel from a checkout:

    python -m pip install build
    python -m build

Then install the generated wheel into an isolated environment.

## Testing

Run deterministic unit tests without an AI runtime:

    PYTHONPATH=src python -m unittest discover -s tests/unit -v

The real Ollama integration test is opt-in:

    GIADAWARE_AI_RUN_INTEGRATION=1 \
    PYTHONPATH=src \
    python -m unittest discover -s tests/integration -v

## Non-goals for M0

M0 does not provide:

- autonomous agents;
- mutation or application-state control;
- generic chat;
- MCP;
- RAG;
- memory;
- LibreChat integration;
- a guarantee that AI output is correct.

LibreChat was useful during the originating experiment but is not a dependency
or part of the GiadaWare AI public contract.

## License

Apache-2.0.
