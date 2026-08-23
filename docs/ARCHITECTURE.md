# GiadaWare AI Capability — Architecture

## Status

Approved for M0 architectural proof.

## Purpose

Provide GiadaWare products with optional, pluggable AI capabilities while
keeping application authority in deterministic software.

Canonical rule:

> AI processes and proposes; software validates, decides, and executes.

AI output is data, never authority.

## Architectural boundary

A consuming product depends on semantic AI capabilities, not on models,
providers, prompts, or transport details.

Architecture:

    GiadaWare Product
            |
            v
    GiadaWare AI Capability
            |
            v
    AI Backend / Runtime
            |
            v
    Local or remote inference provider

LibreChat is not part of the public contract.

Ollama is an infrastructure implementation detail.

## Normative principles

1. AI is optional.
2. AI has no mutation authority.
3. Consumers depend on semantic capabilities, not prompts or models.
4. AI output is untrusted input.
5. Outputs must be validated before crossing the public library boundary.
6. Backends must be replaceable.
7. Failures must be explicit and typed.
8. Local-first does not mean local-only.
9. The architecture may enable zero-cost local inference, but does not promise
   that every backend is free.
10. Provider and model identity must not leak into product domain semantics.

## Mutation boundary

The AI layer MUST NOT directly:

- modify application state;
- persist domain data;
- write or delete consumer files;
- perform Git mutations;
- send messages;
- change permissions or configuration;
- perform transactions;
- invoke destructive operations.

Any effect on application state belongs exclusively to the consuming software.

## M0 capability

The first supported semantic capability is:

    analysis = ai.analyze_log(log_text)

The consumer receives a validated typed LogAnalysis, not raw model output.

## Failure model

The public API distinguishes at least:

- AIUnavailableError
- AITimeoutError
- AIInvalidResponseError
- AIUnsupportedCapabilityError
- AIConfigurationError

AI failure must degrade the optional feature, not the base product.

## M0 acceptance criteria

M0 proves:

- public semantic capability contract;
- typed and validated results;
- replaceable backend protocol;
- Ollama-backed implementation;
- fake-backend contract tests;
- real local integration test;
- graceful unavailable-AI behaviour;
- absence of mutation primitives.

Chat, agents, MCP, RAG, memory and LibreChat integration are explicitly outside
M0 scope.
