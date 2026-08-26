# GiadaWare AI Backend Contract

## Status

Provider-independent backend contract for the experimental `0.x` line.

## Purpose

`AIBackend` is the structural boundary between semantic capabilities and concrete inference providers. It may expose provider-independent inference primitives needed by concrete capabilities, but it must not leak provider request fields, model-specific options, runtime objects, or transport semantics into consumer domain code.

The contract preserves the architecture:

    consumer-owned semantic capability
            |
            v
    provider-independent AIBackend
            |
            v
    provider-specific backend
            |
            v
    runtime / model

## JSON generation primitive

The backend primitive is:

```python
class AIBackend(Protocol):
    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_schema: Mapping[str, object] | None = None,
    ) -> Mapping[str, object]:
        ...
```

`response_schema` is a provider-independent request for a JSON object constrained by the supplied JSON Schema.

The schema is owned by the concrete semantic capability that needs the structure. GiadaWare AI core does not own consumer domain schemas and does not interpret them as application semantics.

## Schema-less behavior

When `response_schema is None`, backends preserve ordinary JSON-object generation. Existing built-in capabilities that do not request a schema continue to use this behavior unchanged.

For the experimental `0.x` line, existing callers of `generate_json()` remain source-compatible because the new parameter is optional and keyword-only. Backend implementations that claim structural conformance to the updated `AIBackend` protocol must accept the new optional keyword.

## Schema-constrained behavior

When `response_schema` is provided, a backend must either:

1. request provider-supported schema-constrained structured output; or
2. raise the existing `AIUnsupportedCapabilityError` if that backend cannot provide the requested constraint.

A backend must not silently downgrade a schema-constrained request to unconstrained JSON generation.

A backend may validate provider-independent configuration needed to serialize or transmit the schema. It must not perform consumer-domain validation or decide whether the resulting candidate is canonical application data.

## Ollama mapping

`OllamaBackend` translates the provider-independent request internally:

- `response_schema is None` -> Ollama `format: "json"`;
- `response_schema is not None` -> Ollama `format: <JSON Schema object>`.

The Ollama field name `format` is an implementation detail and is not part of the public `AIBackend` contract.

The caller-owned schema is read and copied for provider payload construction; it is not mutated.

## Error semantics

Existing backend failure semantics remain authoritative:

- configuration or non-serializable schema input -> `AIConfigurationError`;
- timeout -> `AITimeoutError`;
- unavailable provider -> `AIUnavailableError`;
- malformed provider envelope or malformed model JSON -> `AIInvalidResponseError`;
- unsupported schema-constrained generation in a future backend -> `AIUnsupportedCapabilityError`.

Schema-constrained generation does not introduce auto-repair, silent fallback, or a new trusted-output exception path.

## Authority boundary

Structured output improves shape. It does not grant authority.

Canonical flow:

    schema-constrained AI output
            |
            v
    structured candidate
            |
            v
    consumer deterministic validation
            |
            v
    accepted / rejected

Forbidden interpretation:

    schema-constrained AI output
            |
            v
    trusted / canonical application data

A JSON Schema can constrain representation. It does not establish factual truth, business validity, provenance, approval, persistence authority, or canonical status.

Concrete semantic capabilities and consuming applications remain responsible for deterministic validation and all application decisions.

## Non-goals

This contract does not:

- expose Ollama-specific options to consumers;
- validate arbitrary JSON Schema semantics inside GiadaWare AI;
- add consumer-domain schemas to GiadaWare AI core;
- add prompt tuning for Grocery Deal Intelligence or any other consumer;
- auto-repair malformed or semantically invalid model output;
- change models or provider selection;
- make structured output authoritative.

## Design principle

> Constrain structure. Do not grant authority. Keep providers behind the boundary.
