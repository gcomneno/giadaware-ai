# Free Claude Code — external architectural/reference candidate

## Status

CANDIDATE — external architectural/reference source for GiadaWare AI.

No installation, integration, or production dependency is approved by this document.

## Source

Upstream project:

- repository: `Alishahryar1/free-claude-code`
- license: MIT
- role: local provider/model gateway and compatibility layer for coding clients and agents

The upstream project exposes a local proxy/API surface and supports multiple remote and local inference providers.

## Why it matters to GiadaWare AI

GiadaWare AI already requires consuming products to depend on semantic capabilities rather than models or providers, and treats provider/runtime details as backend implementation concerns.

Free Claude Code is relevant below that semantic boundary because it demonstrates a provider-agnostic routing layer capable of selecting among models/providers while presenting stable client-facing protocols.

Candidate layering:

```text
GiadaWare Product
        |
        v
GiadaWare AI semantic capability
        |
        v
AIBackend abstraction
        |
        v
optional provider/model gateway
        |
        v
local or remote inference provider
```

The gateway must never become semantic or application authority.

## Cost finding

The useful claim must be stated narrowly.

### What is genuinely free

- Free Claude Code itself is open source under the MIT license, so using the gateway software carries no license fee.
- It can expose a local API/proxy endpoint that another program can call.
- It can route to local providers such as Ollama, llama.cpp, or LM Studio, permitting zero external inference charges when suitable local hardware and models are used.
- It can also route to provider free tiers or explicitly free models when those providers make them available.

Therefore a zero-marginal-API-cost deployment for GiadaWare AI is technically possible.

### What is not guaranteed to be free

Free Claude Code is not itself a hosted inference service that guarantees free inference.

Actual inference cost depends on the selected provider/model. Provider free tiers, quotas, eligibility rules, account requirements, and terms can change independently of Free Claude Code.

The upstream project explicitly states that free-tier availability and limits are controlled by each provider and may change.

Consequently GiadaWare AI must never expose a public guarantee such as "AI inference is free" merely because this gateway is used.

## Semantic and governance constraints

Any future experiment or integration must preserve the existing GiadaWare AI boundaries:

- consumers depend on semantic capabilities, not provider/model identities;
- provider/model routing is infrastructure, not domain semantics;
- AI output remains untrusted until validated;
- fallback must not silently change privacy, locality, semantic, or cost guarantees;
- local-to-remote fallback requires explicit configuration;
- credentials and provider-specific objects must not leak into semantic result contracts;
- failures must remain explicit and typed.

## Trust boundary

A provider/model gateway may handle sensitive material including:

- API credentials;
- prompts and source material;
- model responses;
- tool-call traffic;
- routing and fallback metadata.

Before adoption, GiadaWare AI must assess at least:

- secret storage and exposure;
- telemetry and logging;
- data retention;
- provider privacy terms;
- provider ToS compatibility for the intended mode of use;
- capability preservation across protocol translation;
- retry and fallback semantics;
- cost and quota observability;
- supply-chain and dependency risk.

## Candidate capability

The architectural candidate extracted from this source is:

> provider-agnostic inference gateway with explicit routing, cost, locality, privacy, and capability-preservation boundaries.

The candidate is broader and more durable than the upstream project's current list of providers or free-token claims.

## Adoption decision

Current decision:

- study/reference: YES;
- candidate for a future GiadaWare AI backend/gateway experiment: YES;
- install automatically: NO;
- production dependency: NO;
- promise of permanently free inference: NO;
- zero-cost operating mode: YES, conditionally, through local inference or provider free tiers.

## Verification questions before any implementation

1. Does the gateway expose an API surface suitable for an `AIBackend` adapter without leaking provider semantics upward?
2. Which GiadaWare AI capabilities survive protocol translation without semantic loss?
3. Can routing and fallback be configured so locality, privacy, and cost boundaries remain explicit?
4. Can a deterministic test backend remain the contract authority while the gateway is only an infrastructure implementation?
5. How are credentials stored, refreshed, and isolated?
6. Can cost/free-tier state be observed without promoting it to a semantic guarantee?
7. Is direct integration with selected providers simpler and safer than introducing the extra gateway layer?

Until those questions are answered, Free Claude Code remains an external architectural/reference candidate rather than an adopted component.
