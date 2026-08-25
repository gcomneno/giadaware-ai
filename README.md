# GiadaWare AI

Experimental infrastructure library for pluggable, read-only AI capabilities
in GiadaWare software.

**Status: Experimental 0.x. The public API may change before a stable release.**

GiadaWare AI lets application code depend on semantic AI capabilities rather
than specific models, providers, prompts, or transport protocols.

Core rule:

> AI processes and proposes; software validates, decides, and executes.

AI output is data, never authority.

## Current capabilities

Technical log analysis:

    analysis = ai.analyze_log(log_text)

Consumers receive a validated, typed `LogAnalysis`, not raw model output.

Learning-source analysis:

    analysis = ai.analyze_learning_source(text)

Consumers receive a validated, typed `LearningSourceAnalysis`. Source claims use
`ClaimSupport.EXPLICIT`, `ClaimSupport.INFERRED`, or `ClaimSupport.UNCLEAR` to
describe only the relationship between a candidate claim and the supplied
source. This does not imply independent truth verification or fact-checking.

The current public surface includes:

- `AICapabilities`;
- `AIBackend` protocol;
- the semantic extension API and 12 canonical capability families;
- `AnalyzeLogCapability`;
- `AnalyzeLearningSourceCapability`;
- typed `LogAnalysis` and `LearningSourceAnalysis` results;
- `SourceClaim`, `ClaimSupport`, and `Severity`;
- explicit AI failure types;
- structured-output validation;
- `OllamaBackend` as one replaceable backend implementation;
- deterministic tests using fake backends;
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

## Reference local runtime

The reference local development and integration runtime is:

    Ubuntu host
        |
        v
    native Ollama service
        |
        v
    http://localhost:11434
        |
        v
    qwen2.5:1.5b-instruct

Docker Compose is not required for this reference runtime.

Install Ollama natively on Ubuntu using the official Linux installer, then pull
the lightweight integration model:

    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen2.5:1.5b-instruct

Verify the local API:

    curl http://localhost:11434/api/tags

The runtime and model are backend configuration details. Consumers continue to
depend only on semantic GiadaWare AI capabilities.

This reference path has been verified end-to-end on an Ubuntu CPU-only host:
Ollama `0.32.15` running on `127.0.0.1:11434`,
`qwen2.5:1.5b-instruct`, and the real opt-in GiadaWare AI integration test all
completed successfully. This is verification evidence for the reference
deployment, not a minimum hardware or version requirement.

See `docs/ARCHITECTURE.md` for the architectural boundary,
`docs/SEMANTIC-CAPABILITY-CONTRACT.md` for the normative semantic capability
contract, and `docs/EXTENSION-API.md` for consumer specialization rules.

## Example

    from giadaware_ai import AICapabilities
    from giadaware_ai.backends import OllamaBackend

    backend = OllamaBackend(
        model="qwen2.5:1.5b-instruct",
        base_url="http://localhost:11434",
    )

    ai = AICapabilities(backend)

    log_result = ai.analyze_log(
        "ERROR Connection refused: database unavailable"
    )

    source_result = ai.analyze_learning_source(
        "A supplied transcript, article, or other learning source"
    )

    print(log_result.summary)
    print(source_result.central_thesis)

## Installation

GiadaWare AI is not yet published to PyPI.

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

## Non-goals

GiadaWare AI does not provide:

- autonomous agents;
- mutation or application-state control;
- generic chat;
- MCP;
- RAG;
- memory;
- a guarantee that AI output is correct.

## License

Apache-2.0.
