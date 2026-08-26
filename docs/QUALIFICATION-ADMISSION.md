# GiadaWare AI Capability Qualification and Admission Contract

## Status

Design proposal for issue #22. This document is normative only for review of the experimental `0.x` line and does not yet introduce runtime enforcement.

## Purpose

GiadaWare AI must not equate backend/model availability with semantic capability competence.

A provider/model composition may be technically able to return structured output while still failing the semantic invariants of a concrete capability.

Canonical rule:

> A backend/model composition may expose a semantic capability only when that concrete capability has passed its declared evaluation contract for the intended operating envelope.

Qualification is capability-specific. Passing one capability never grants global model approval.

## Architectural boundary

Qualification belongs at the composition/admission boundary, not inside `AIBackend`.

```text
consumer intent
    |
    v
concrete semantic capability
    |
    v
admission controller
    |
    v
qualification registry / reviewed evidence
    |
    +-- rejected -> deterministic qualification failure
    |
    v
AIBackend
    |
    v
provider / runtime / model
```

`AIBackend` remains responsible for provider-independent inference transport and provider adaptation. It may report technical support such as schema-constrained JSON capability, but it does not decide whether a model is semantically competent for a concrete capability.

Public consumers continue to depend on semantic capabilities and must not need provider or model identity for domain decisions.

## Qualification states

Every evaluated capability/composition relationship uses one of four states:

- `UNVERIFIED` — no current admissible evidence exists;
- `PASS` — current evidence qualifies the composition for the declared operating envelope;
- `FAIL` — current evidence rejects the composition for the declared operating envelope;
- `CONDITIONAL` — current evidence qualifies the composition only inside an explicit bounded operating envelope.

Missing or stale evidence is treated as `UNVERIFIED`, not `FAIL`.

## Capability identity

Qualification targets a concrete semantic contract, not only a capability family.

A capability identity contains at least:

```text
CapabilityIdentity
    id
    contract_revision
```

`id` is a stable semantic identifier such as `analyze_log`.

`contract_revision` identifies the semantic behavior being evaluated, including capability-specific invariants and policy/instruction behavior that materially affects the contract.

Capability family identity alone is insufficient because two capabilities in the same family may require different model competence.

## Composition identity

Provider/model/runtime identity is technical composition metadata and remains outside consumer domain semantics.

A composition identity contains:

```text
CompositionIdentity
    backend_kind
    model_id
    model_revision?
    runtime_revision?
```

`model_revision` should use an immutable digest or revision when the provider/runtime makes one available.

`runtime_revision` is included only when the evaluation intentionally scopes itself to runtime behavior relevant to the result.

Absence of an immutable model revision weakens reproducibility and must be visible in the evidence rather than silently ignored.

## Evaluation identity

An evaluation must identify the exact suite that produced the qualification evidence.

```text
EvaluationIdentity
    suite_id
    suite_revision
    policy_revision
    schema_revision?
    corpus_revision?
```

Only fields that materially affect the evaluated contract need to participate in the identity.

## Qualification record

The reviewed qualification manifest stores records equivalent to:

```text
QualificationRecord
    capability
    composition
    status
    envelope
    evaluation
    dimensions
    evidence_refs
    evaluated_at
```

The record is trusted deterministic metadata produced by GiadaWare AI evaluation/review tooling. It must never be copied from model output or self-asserted by the model.

## Evaluation dimensions

GiadaWare AI must not assign one universal model quality score.

A qualification record may contain capability-specific dimensions such as:

```text
EvaluationDimension
    id
    outcome
    evidence_ref?
```

Dimension outcomes may include:

- `PASS`;
- `FAIL`;
- `WEAK`;
- `NOT_APPLICABLE`.

Examples include structural contract compliance, language preservation, factual preservation, technical-content preservation, stability, or operational timeout behavior when relevant to the concrete capability.

A dimension is evidence. Admission is decided by the qualification status and envelope, not by averaging dimension scores.

## Operating envelope

`CONDITIONAL` qualification must use an explicit bounded envelope rather than prose-only caveats.

The initial generic envelope should remain deliberately small:

```text
OperatingEnvelope
    languages?
    max_input_size?
    content_kinds?
```

Fields must be added only when real evaluations require them.

Provider/model identity must not appear in the operating envelope; it belongs to `CompositionIdentity`.

Capability-specific evaluators may define additional declarative constraints later, but generic abstractions must not be introduced speculatively.

## Admission semantics

Admission is deterministic and must occur before provider inference.

Rules:

- `PASS` is admitted only when capability, composition, and evaluation identities match current non-stale evidence;
- `CONDITIONAL` is admitted only when the invocation falls within its declared operating envelope;
- `FAIL` is rejected before provider inference;
- `UNVERIFIED` or missing qualification is rejected before provider inference;
- stale or mismatched evidence is treated as `UNVERIFIED`;
- admission failure must not trigger fallback inference implicitly.

Where an operating envelope depends on invocation input, admission has two phases:

1. composition-time check: current evidence exists for the concrete capability/composition;
2. invocation-time envelope check: the concrete request is inside the qualified envelope.

The invocation-time check must occur before `AIBackend.generate_json()` or any other provider call.

## Evidence model

Qualification uses two evidence layers.

### Raw evaluation evidence

Real-provider evaluations may generate logs, structured run records, deterministic gate results, timing data, and manual evaluation notes.

Raw evidence is not automatically trusted merely because it exists or because a model produced structured output.

### Reviewed qualification manifest

A small deterministic manifest is promoted only after evaluation review.

Runtime admission reads reviewed qualification records, not historical raw logs.

This prevents model self-certification and keeps admission inspectable and reproducible.

## Staleness and invalidation

Qualification becomes stale when an identity element on which the evaluation depends changes materially.

At minimum consider:

- concrete capability semantic contract or policy revision;
- evaluation suite or corpus revision;
- model identity or immutable revision;
- backend behavior relevant to the evaluated capability;
- response schema revision when material;
- runtime revision when the qualification explicitly scopes itself to that runtime.

Stale evidence becomes `UNVERIFIED`.

Unrelated package changes must not invalidate qualification automatically.

## Failure semantics

Technical unsupported behavior and semantic qualification failure are distinct.

`AIUnsupportedCapabilityError` currently means the selected backend cannot technically provide the requested capability or primitive.

Qualification failure should not silently reuse that meaning.

Candidate future exception:

```text
AIUnqualifiedCapabilityError
```

It may represent missing/unverified evidence, evaluated failure, stale evidence, or out-of-envelope invocation through a deterministic reason value or internal detail.

Do not add one exception class per qualification state unless real consumer handling requires it.

## Existing capability mapping

### `analyze_log`

The repository already contains a real Ollama integration test using `qwen2.5:1.5b-instruct` and verifies successful typed result construction.

This is historical positive evidence, but it is not automatically equivalent to a complete qualification suite under this contract.

Existing behavior should be migrated deliberately rather than grandfathered as `PASS` without an explicit evaluation definition.

### Prose naturalization spike

Issue #19 and PR #21 provide a concrete negative case study for `qwen2.5:1.5b-instruct`.

Observed evidence after schema-constrained output:

- structured contract compliance: pass for returned responses;
- Italian language preservation: fail;
- technical-content preservation: fail;
- stable `changed` semantics: fail;
- English behavior: partial/inconsistent;
- CPU-only runtime: operationally weak with observed timeouts.

The tested composition therefore fails admission for the evaluated prose-naturalization envelope even though the overall capability concept remains on hold rather than rejected architecturally.

## Test strategy

### Unit tests

Unit tests verify deterministic qualification machinery only:

- identity matching;
- state semantics;
- conditional envelope checks;
- stale evidence rejection;
- no backend invocation when admission fails;
- admitted requests reaching the backend;
- backend failures propagating unchanged after successful admission.

Unit tests must not depend on exact natural-language model output.

### Real-provider evaluations

Real-provider evaluations establish qualification evidence for capability-specific properties such as:

- structured contract compliance;
- semantic/factual preservation;
- language preservation;
- repeated-run stability;
- operational timeout behavior.

Exact wording is not a required success criterion unless a concrete capability explicitly guarantees it.

## Compatibility and migration

The existing `AICapabilities(backend)` facade currently constructs built-in capabilities directly from one backend.

Qualification enforcement must therefore define an intentional migration path for existing callers.

The design must not silently switch existing callers from permissive behavior to strict admission without a documented `0.x` compatibility decision.

Potential implementation shapes may include a composition object or admission policy injected at construction time, but no concrete API is selected by this document yet.

## Non-goals

This contract does not:

- add a new public semantic capability;
- globally enable or disable a model;
- assign a universal numeric model score;
- make structured output proof of semantic competence;
- move provider/model identity into consumer domain semantics;
- let models certify themselves;
- define automatic fallback to another provider/model;
- implement runtime admission yet.

## Design decisions still open

Before implementation, issue #22 must explicitly decide:

1. the stable `CapabilityIdentity` mechanism for built-in and consumer-owned capabilities;
2. reviewed manifest format and repository/runtime location;
3. `AIUnqualifiedCapabilityError` versus reuse of the current exception surface;
4. migration behavior for existing `AICapabilities(backend)` callers;
5. whether runtime admission should use a dedicated composition object, an admission controller injected into capabilities, or another minimal mechanism supported by evidence.

Implementation begins only after these points are reviewed.