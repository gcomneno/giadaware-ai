# GiadaWare AI Semantic Capability Extension API

## Status

Approved design for the experimental `0.x` extension surface introduced by issue #3.

This document explains how the semantic hierarchy defined by the contract is represented in Python without turning GiadaWare AI into a generic prompt API.

## Decision

GiadaWare AI uses a deliberately small combination of:

- a generic abstract base class, `SemanticCapability[InputT, ResultT]`;
- twelve thin family abstract base classes such as `AnalyzeCapability` and `ExtractCapability`;
- a stable `CapabilityFamily` enum for family identity;
- composition with the existing provider-independent `AIBackend` protocol;
- concrete capabilities that implement `execute()` and own their hidden inference instructions and result validation.

The existing `AICapabilities` facade remains supported. It delegates to concrete capabilities so existing M0 call sites such as `ai.analyze_log(...)` do not change merely to satisfy the extension hierarchy.

## Why ABCs

ABCs are used for the semantic extension surface because family membership is intentional and normative, not merely structural.

A consumer that writes:

    class AnalyzeInvoiceCapability(AnalyzeCapability[InvoiceText, InvoiceAnalysis]):
        ...

is explicitly declaring that the new capability inherits the Analyze family contract.

This is useful in code review, tests, documentation and type checking.

The family ABCs are intentionally thin. They do not duplicate inference plumbing and they do not imply that every family must have a built-in concrete capability.

## Why not Protocol-only

`Protocol` remains appropriate for `AIBackend`, because backend substitutability is primarily structural: any implementation with the required provider-independent method shape can satisfy the backend contract.

A Protocol-only semantic hierarchy was rejected because accidental structural conformance would be too weak for normative family membership. A class should not become an Analyze capability merely because it happens to expose an `execute()` method with a compatible signature.

## Why not pure composition

Pure composition could avoid inheritance entirely, but it would make consumer specialization less explicit and would require a separate family descriptor to be carried and checked everywhere.

The chosen model keeps composition where it matters — backend injection — while using nominal inheritance only for semantic family identity.

## Why generics

`SemanticCapability[InputT, ResultT]` makes the input and result contract explicit for both built-in and consumer-owned capabilities.

For example:

    AnalyzeCapability[str, LogAnalysis]

or:

    AnalyzeCapability[InvoiceText, InvoiceAnalysis]

The generic parameters are part of the extension contract; they do not encode provider details.

## Execution boundary

A semantic capability receives an `AIBackend` through composition at construction time.

Concrete capability implementation code may use the provider-independent backend primitive internally, but consuming domain code should only invoke the semantic capability.

Conceptually:

    composition boundary
        -> backend
        -> concrete semantic capability
        -> consumer domain code calls execute(...)

The consumer domain layer does not need to know Ollama, model names, base URLs, provider request envelopes or transport details.

Prompt or instruction text remains implementation detail inside the concrete capability and is not exposed as part of the public semantic result contract.

## Safety and enforceability

Python inheritance cannot mechanically prove that arbitrary consumer code is side-effect-free. The extension API therefore combines enforceable structure with normative constraints.

Enforceable/testable properties include:

- explicit family identity;
- typed input/result parameters;
- provider-independent backend injection;
- abstract `execute()` requirement;
- immutable typed result types where defined;
- existing typed failure hierarchy;
- validation before built-in capabilities return model-derived results;
- no mutation primitive in the base extension API.

Normative properties that remain subject to implementation review and tests include:

- read-only behavior;
- absence of application authority;
- no persistence or other side effects;
- no provider-specific leakage into semantic results;
- correct semantic use of the selected family.

A consumer specialization that violates those invariants is non-conforming even if Python allows it to instantiate.

Subclassing or inheriting a semantic capability family grants semantic family membership only; it does not grant review authority, workflow promotion authority, persistence authority, publication authority, or consumer application authority.

## Core example

`AnalyzeLogCapability` is the first built-in concrete capability mapped onto the extension API:

    AnalyzeCapability[str, LogAnalysis]
        -> AnalyzeLogCapability

`AICapabilities.analyze_log()` delegates to this capability, preserving M0 public behavior.

## Consumer specialization

A consumer-specific capability may live entirely outside the GiadaWare AI package:

    AnalyzeCapability
        -> AnalyzeInvoiceCapability

It does not need to be added to the GiadaWare AI public capability catalog merely to reuse the semantic family and backend contracts.

If later evidence shows that the capability is broadly reusable and satisfies the public admission rule, it may be proposed separately for promotion into the core catalog.

## Compatibility

For the experimental `0.x` line:

- `AICapabilities` remains the compatibility facade for existing M0 consumers;
- new concrete capability classes may coexist with facade methods;
- family classes and `CapabilityFamily` are public extension API;
- provider-specific backends remain outside semantic family identity;
- no consumer is required to subclass a concrete GiadaWare AI capability to create a new domain capability.

This design may evolve during `0.x`, but changes must remain intentional and documented under the Semantic Capability Contract.
