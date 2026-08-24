# Swiftlet Candidate — Storage-backed Sparse-MoE Local Inference

Status: CANDIDATE

Classification: external architectural/reference source and possible specialized backend candidate for Apple deployments.

## Source context

Swiftlet was identified during external technology reconnaissance as a runtime focused on low-RAM local inference for sparse Mixture-of-Experts models on Apple Silicon.

The relevant value for GiadaWare AI is not the project name itself, nor any single benchmark claim. The architectural pattern worth preserving is:

> storage-backed sparse-MoE inference as a low-RAM local backend strategy.

No installation or integration is implied by this document.

## Why it matters to GiadaWare AI

GiadaWare AI already requires consuming products to depend on semantic capabilities rather than models, providers, prompts, or transports. Backends are replaceable infrastructure details.

Swiftlet suggests a possible additional backend class beneath that semantic boundary:

```text
GiadaWare Product
      |
      v
semantic capability
      |
      v
AIBackend abstraction
      |
      v
Swiftlet adapter (candidate)
      |
      v
sparse MoE model on Apple Silicon
```

This is compatible in principle with the current architecture because provider/model identity remains outside product-domain semantics.

## Candidate capability

The candidate is not "use Swiftlet".

The candidate is:

> support specialized local inference backends that trade RAM residency for bounded storage-backed expert loading while preserving GiadaWare AI semantic capability contracts.

Such a backend could be useful where:

- local execution is preferred for privacy or cost reasons;
- available RAM is limited relative to model storage size;
- the model architecture is sparse enough that only a subset of experts is active per token;
- platform-specific acceleration is acceptable.

## Important semantic boundary

A Swiftlet-class backend may decide how to:

- load or cache model weights;
- move expert weights between storage and memory;
- invoke the underlying runtime;
- expose transport/runtime failures through the GiadaWare AI backend error model.

It must not redefine:

- the meaning of a semantic capability;
- result schemas;
- application policy;
- mutation authority;
- privacy or locality guarantees without explicit configuration.

Backend optimization authority is permitted; semantic authority is not.

## Platform scope

The current candidate is Apple-specific because the observed implementation is based on Swift and Metal on Apple Silicon.

Therefore it must not be treated as:

- a universal replacement for Ollama;
- the default GiadaWare AI backend;
- a Linux backend candidate without a separate implementation path.

Its correct current role is:

> specialized local backend candidate for Apple deployments.

## Resource trade-off

The architectural trade is:

```text
lower RAM residency
        |
        v
more storage I/O and cache sensitivity
```

This means benchmark quality depends materially on:

- model sparsity;
- expert activation pattern;
- storage performance;
- cache hit rate;
- prompt length;
- hardware generation;
- quantization/runtime implementation.

No isolated RAM or throughput claim should become part of the GiadaWare AI contract.

## Verification questions before any integration

Before Swiftlet or a similar runtime can move beyond reference status, verify:

1. whether it exposes a stable programmatic integration surface suitable for an `AIBackend` adapter;
2. whether structured-output needs can be supported without weakening validation guarantees;
3. how timeout, cancellation, and runtime failures map to the existing typed failure model;
4. whether streaming is available and whether it matters for current semantic capabilities;
5. how model identity and quantization details remain confined to backend configuration;
6. how local-only guarantees can be made explicit and testable;
7. whether storage-backed loading causes unacceptable latency variance for target capabilities;
8. what provenance/technical invocation metadata should be exposed separately from semantic result data;
9. whether the runtime lifecycle is safe for concurrent consumer workloads;
10. whether the maintenance and platform lock-in cost is justified against Ollama or other existing runtimes.

## Adoption decision

Current decision:

- external architectural/reference source: ACCEPT;
- candidate specialized backend: ACCEPT FOR STUDY;
- immediate integration: NO;
- replacement for Ollama: NO;
- production dependency: NO;
- future Apple-specific experiment: POSSIBLE.

## Canonical takeaway

The durable knowledge to retain is:

> GiadaWare AI may benefit from specialized local backends that exploit sparse-model execution and storage-backed expert loading to reduce RAM requirements, provided those optimizations stay strictly below the semantic capability boundary and do not silently change locality, privacy, cost, or result semantics.
