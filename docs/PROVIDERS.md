# GiadaWare AI Provider Status

## Status

Provider/runtime status record for the experimental `0.x` line.

This document describes implemented backend adapters and observed runtime
paths. It does not qualify any provider/model composition for arbitrary
semantic capabilities.

Canonical boundary:

> AI output is data, never authority.

## Status taxonomy

GiadaWare AI uses three distinct statuses.

### Supported backend

An implemented adapter satisfying the provider-independent GiadaWare AI backend
contract.

Support means the adapter implements `AIBackend.generate_json()` and maps its
provider transport, authentication, response parsing, timeouts, structured
output, and typed failures behind the shared boundary. It does not mean the
backend is available in a particular environment.

### Runtime-verified backend

A backend/model/provider path for which a real provider call has been
successfully observed through the shared `AIBackend` structured-output
boundary.

Runtime verification proves only that the observed path could make a real call
and return structurally valid data for the observed smoke contract. It does not
prove provider quality, current availability, current pricing, safety, truth,
or semantic capability competence.

### Semantically qualified composition

A specific:

```text
capability x backend/model x operating envelope x evaluation evidence
```

that has passed its declared evaluation contract and reviewed qualification
process.

Qualification is capability-specific. Backend availability and runtime
verification must not be treated as qualification evidence unless a declared
evaluation contract explicitly admits the road-test observation as raw input
and a reviewed qualification record promotes it.

## Current provider state

| Backend | Default model | Role | Current status |
| --- | --- | --- | --- |
| `OllamaBackend` | `qwen2.5:1.5b-instruct` | Lightweight local reference runtime | Supported backend; runtime-verified backend |
| `DeepSeekBackend` | `deepseek-v4-flash` | Optional remote backend | Supported backend; runtime-verified backend |
| `OpenAIBackend` | `gpt-5.6-luna` | Optional remote backend | Supported backend; runtime-verified backend |

All three use the provider-independent `AIBackend.generate_json()` boundary.
Consumers must depend on semantic capabilities and contracts rather than
provider identity.

The status table is not a provider ranking, benchmark, fallback order, pricing
claim, semantic qualification manifest, or provider-selection policy.

## Local reference runtime

The current lightweight local reference path is:

```text
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
```

This path has been verified as a real runtime path. It remains a development
and integration reference, not a minimum supported host specification and not a
semantic qualification for every capability.

## Optional remote backends

`DeepSeekBackend` and `OpenAIBackend` are optional remote implementations of
the same backend contract. They are never selected implicitly and do not add
automatic routing, fallback, tool execution, web search, autonomous agents, or
consumer authority.

Remote-provider credentials are injected into adapters by consumers. Keep
credentials outside the repository. Environment variables or an external local
secret store are appropriate examples. Secret values must never be committed or
documented.

Provider account and billing availability are operational prerequisites for
remote calls. HTTP availability, account, billing, or configuration failures
are operational failures; they are not semantic qualification failures.

## gpt-oss host decision

`gpt-oss:20b` was considered for the current local host. The current host is
CPU-only with approximately 8 GiB RAM, while the model is in roughly the 16 GiB
memory class. It was therefore rejected for this host, and no model download
was performed.

This is a host/runtime suitability decision, not a universal rejection of
`gpt-oss:20b`. `qwen2.5:1.5b-instruct` remains the lightweight local reference
model for the current host.

## Related documents

- `docs/BACKEND-CONTRACT.md` defines the provider-independent boundary.
- `docs/ROAD-TESTS.md` records the 2026-09-12 three-provider runtime road test.
- `docs/QUALIFICATION-ADMISSION.md` defines semantic qualification and
  admission rules.
