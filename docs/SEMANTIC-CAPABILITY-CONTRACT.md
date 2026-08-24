# GiadaWare AI Semantic Capability Contract v0.1

## Status

Normative contract for the experimental `0.x` line.

This document hardens the architectural rules established by M0 before the
public capability surface expands.

Canonical rule:

> AI processes and proposes; software validates, decides, and executes.
>
> AI output is data, never authority.

## 1. Semantic capability definition

A semantic capability is a provider-independent, side-effect-free operation
that expresses a reusable consumer intent, accepts explicitly defined input,
and returns a validated typed result whose meaning does not depend on a
specific model, prompt, provider, runtime, or transport.

A public semantic capability MUST:

- express consumer intent rather than provider mechanics;
- avoid provider, model, runtime, prompt, and transport names in its public
  semantics;
- be read-only and side-effect-free;
- define accepted input and a typed output contract;
- define the meaning of every public field;
- validate model output before returning it across the public library boundary;
- remain implementable by conceptually different backends;
- keep AI output advisory rather than authoritative;
- define explicit failure semantics;
- be justified by a real consumer or concrete proof of value rather than by
  speculative API growth.

Provider primitives such as `generate_json`, `chat`, `complete`, raw prompts,
or `call_ollama` are backend mechanics, not semantic capabilities.

## 2. Public contract versus implementation detail

The public semantic contract includes:

- capability names;
- accepted input types and documented preconditions;
- result type names;
- result field names and types;
- result field meaning;
- public enumerations;
- public exception hierarchy;
- documented behavioural guarantees;
- documented degradation guarantees.

The following are implementation details unless explicitly promoted to the
public contract:

- prompt text and system messages;
- provider request and response shapes;
- sampling parameters;
- model names;
- transport protocol details;
- retry implementation;
- provider-specific SDK objects;
- provider-specific structured-output envelopes.

Consumers MUST NOT rely on implementation details for domain decisions.

## 3. Result stability and inference nondeterminism

Public result types are structural API contracts.

Structural stability covers at least:

- type names;
- field names;
- field types;
- enumeration members;
- documented field meaning.

Structural stability does not imply inference determinism.

Consumers MUST NOT depend on exact natural-language wording, ordering, or
reproducibility of AI-derived content unless a capability explicitly guarantees
those properties.

A valid result may differ between invocations, models, providers, or runtime
versions while still conforming to the same semantic result contract.

## 4. Compatibility and versioning

During the `0.x` line, breaking changes remain possible, but they MUST be
intentional and documented.

For a future stable `1.0` line, the following are breaking unless explicitly
covered by a compatibility policy:

- removing a public capability;
- renaming a public capability;
- removing or renaming a public result field;
- changing the meaning of a public field;
- removing enumeration members;
- restricting inputs that were previously documented as valid;
- changing documented failure semantics in a way that invalidates consumer
  handling.

The following are normally additive:

- adding a backend;
- adding a new capability;
- adding a new consumer-specific extension point;
- improving prompts or provider adaptation while preserving the semantic
  contract.

Capability names SHOULD NOT gain version suffixes such as `_v2` unless schema
or semantic evolution truly requires a distinct public contract.

## 5. Backend contract

A backend implements inference transport and provider adaptation; it does not
define application semantics.

A backend MAY:

- invoke a local or remote inference runtime or provider;
- serialize requests and parse provider responses;
- authenticate to a provider;
- apply timeouts;
- map provider failures into GiadaWare AI typed failures;
- request or parse structured output;
- expose technical observability metadata outside domain semantics;
- perform safe retries when retry behaviour does not change semantic, privacy,
  or cost guarantees.

A backend MUST NOT:

- mutate consumer or application state;
- persist consumer domain data;
- write or delete consumer files;
- perform Git mutations;
- publish content;
- send messages;
- perform transactions;
- change permissions or application configuration;
- invoke destructive operations;
- bypass semantic result validation;
- leak provider-specific objects into public semantic result types;
- redefine the meaning of a capability.

## 6. Failure taxonomy

All public AI failures derive from `AIError`.

The public failure model is:

- `AIConfigurationError` — configuration is missing, invalid, or internally
  inconsistent before successful inference can occur;
- `AIUnavailableError` — the selected backend or provider cannot currently
  provide the requested inference service;
- `AITimeoutError` — the request exceeded the configured execution deadline;
- `AIInvalidResponseError` — inference returned material that cannot satisfy
  the semantic result contract after validation;
- `AIUnsupportedCapabilityError` — the selected backend or composition cannot
  provide the requested semantic capability.

`AITimeoutError` is an availability failure and MAY be represented as a
specialization of `AIUnavailableError`.

Failures MUST NOT be silently converted into empty values, fabricated defaults,
or success-looking semantic results.

Capability-specific exceptions SHOULD NOT be added unless a real semantic need
cannot be represented by the shared taxonomy.

## 7. Fallback and degradation

Fallback MUST NOT silently change semantic, privacy, locality, or cost
guarantees.

In particular, failure of a local backend MUST NOT silently redirect consumer
input to a remote provider.

Fallback is allowed only when explicitly configured at the composition
boundary by the consuming application or its deployment configuration.

A fallback policy MUST make the relevant change in guarantees visible to the
composition layer.

Failure of an optional AI capability MUST NOT fail the deterministic base
product unless the consuming product explicitly declares that capability
required.

Degradation therefore means that the optional AI feature becomes unavailable or
incomplete while deterministic product behaviour remains usable.

## 8. Trust boundary and provenance

GiadaWare AI distinguishes three layers:

1. **Consumer input** — deterministic data supplied by the consumer.
2. **Raw inference** — untrusted provider or model output.
3. **Validated result** — typed AI-derived data that satisfies the public
   semantic schema, optionally accompanied by trusted library-generated
   technical metadata.

Raw inference is never authority.

Validation establishes structural and semantic-contract conformance; it does
not establish factual truth, correctness, approval, safety, or domain validity
beyond the guarantees explicitly defined by a capability.

Trusted technical metadata, when exposed, MUST be generated by GiadaWare AI
code and MUST NOT be copied from model output.

Provider or model identity MUST remain outside consumer domain semantics.
Technical identity MAY be exposed separately for observability, audit,
debugging, or reproducibility, but consumers MUST NOT be required to use it for
domain decisions.

## 9. Library metadata versus consumer artifact provenance

GiadaWare AI owns semantic result contracts and, where exposed, trusted
technical invocation metadata.

Consumer-owned artifact provenance remains outside GiadaWare AI.

Examples of consumer responsibilities include:

- filesystem paths;
- input artifact names;
- SHA-256 or other content identity;
- pipeline-stage association;
- restart and reuse semantics;
- persistence format;
- labels such as `authority = "ai-advisory"`;
- publication, review, approval, or workflow state.

These concerns MUST NOT be added to semantic result types merely because one
consumer needs them.

## 10. Deterministic metadata versus AI-derived fields

Where GiadaWare AI exposes an envelope around a semantic result, the contract
MUST distinguish trusted deterministic metadata from AI-derived data.

Deterministic metadata is produced by library code and may include identifiers
such as capability identity, schema identity, backend identity, model identity,
or invocation metadata when those are intentionally exposed.

AI-derived fields are values inferred or generated from consumer input, such as
summaries, candidate causes, classifications, explanations, extracted claims,
or suggestions.

A model MUST NOT be permitted to self-assert trusted metadata.

## 11. Authority exclusions

GiadaWare AI semantic results MUST NOT directly represent application authority.

Unless a future contract explicitly introduces a separately reviewed and
bounded concept, result types MUST NOT use fields whose semantics imply that AI
has approved, verified, decided, executed, published, or made a consumer action
safe.

Examples that require special scrutiny and are excluded by default include:

- `approved`;
- `review_status`;
- `publication_ready`;
- `verified_claims`;
- `correctness`;
- `safe_to_execute`;
- `decision` as an authoritative outcome.

A capability may describe evidence, candidates, uncertainty, limitations, or
suggestions without crossing this boundary.

## 12. Admission rule for new public capabilities

A new capability MUST NOT enter the public GiadaWare AI capability catalog
until all of the following can be answered yes:

1. Does it express consumer intent rather than provider mechanics?
2. Is it plausibly reusable beyond one narrow call site?
3. Can its input and output be defined without naming a provider or model?
4. Can its output be structurally validated?
5. Is every public field semantically explainable?
6. Is it read-only and side-effect-free?
7. Can consumers treat the result as advisory data rather than authority?
8. Are failure semantics explicit?
9. Could conceptually different backends implement it?
10. Is there a real consumer or concrete proof of value that justifies it?

A consumer-specific capability may remain outside the GiadaWare AI public
catalog while still reusing the semantic extension contract defined by the
library.

## 13. Learning-source analysis capability

`analyze_learning_source` is an implemented public semantic capability in the
experimental `0.x` line:

    analyze_learning_source(text: str) -> LearningSourceAnalysis

The result model is:

    LearningSourceAnalysis
        central_thesis
        key_concepts
        source_claims
        practical_applications
        limitations
        review_questions

Source claims distinguish how a claim relates to the supplied source:

- `EXPLICIT`;
- `INFERRED`;
- `UNCLEAR`.

This classification describes the model's relationship between a candidate
claim and the supplied source text. It does not imply independent truth
verification or fact-checking.

Validated means semantic-contract conforming. It does not mean factually
verified, evidence accepted, editorially accepted, or promoted in a consumer
workflow.

Learning-source analysis remains below consumer-owned editorial, review, and
publication authority:

    AI-derived learning analysis
        != editorial candidate
        != reviewed source
        != review checkpoint
        != publication authority

`LearningSourceAnalysis` MUST NOT add fields such as `facts`, `verified_claims`,
`correctness`, `review_status`, `approved`, `publication_ready`, `lesson`, or
`recommended_final_text`.

## 14. Canonical capability families

GiadaWare AI defines twelve canonical semantic capability families for contract
v0.1:

- `AnalyzeCapability`;
- `SummarizeCapability`;
- `ClassifyCapability`;
- `ExtractCapability`;
- `CompareCapability`;
- `ExplainCapability`;
- `IdentifyCapability`;
- `GenerateCapability`;
- `ProposeCapability`;
- `TransformCapability`;
- `SynthesizeCapability`;
- `DetectCapability`.

Normative rule:

> Capability families define semantic extension contracts, not generic
> inference operations.

These families are canonical at the taxonomy level for contract v0.1, but they
do not imply that every family has an immediately implemented public capability.
Concrete capabilities remain demand-driven and must satisfy the admission rule
in section 12.

### 14.1 Analyze

`AnalyzeCapability` derives a bounded structured interpretation from supplied
material.

Typical specializations may include log analysis, learning-source analysis, or
consumer-specific domain analysis.

Analysis MUST NOT imply approval, verification, diagnosis, or application
authority merely because the result is structured.

The existing `analyze_log()` capability belongs to this family. This taxonomy
classification does not change its current public behavior.

### 14.2 Summarize

`SummarizeCapability` compresses supplied material into a smaller semantic
representation while preserving the invariants declared by the concrete
capability.

A summary MUST NOT silently introduce claims whose status differs from the
source relationship promised by the concrete capability.

### 14.3 Classify

`ClassifyCapability` maps supplied material to a declared taxonomy, label set,
schema, or bounded class space.

The taxonomy or class space is part of the concrete capability contract.
Classification output is advisory unless the consumer independently promotes it
through deterministic application rules.

### 14.4 Extract

`ExtractCapability` recovers structured information represented in supplied
material according to a declared schema.

The concrete capability MUST distinguish, where relevant, between directly
present source material and inferred interpretation. Extraction MUST NOT turn
source assertions into independently verified facts.

### 14.5 Compare

`CompareCapability` describes similarities, differences, relationships, or
changes between two or more supplied inputs.

A comparison may expose structured contrast without deciding which input is
correct, authoritative, preferable, or approved unless a separately reviewed
contract defines such semantics.

### 14.6 Explain

`ExplainCapability` produces an advisory explanation of supplied content,
evidence, output, or state representation.

Explanation improves interpretability; it does not create evidence, authority,
or truth merely by describing existing material.

### 14.7 Identify

`IdentifyCapability` surfaces bounded candidate properties, limitations,
possible causes, open questions, themes, or other observations from supplied
material.

Identification semantics MUST use wording and result types that avoid implying
that a candidate observation has been independently verified.

### 14.8 Generate

`GenerateCapability` creates a specifically contracted advisory artifact from
supplied input or context.

It MUST NOT become a generic completion primitive such as `generate(prompt)` or
`generate_anything(...)`.

Every concrete generation capability MUST define the artifact class it produces
and the semantic limits of that output. Generated material remains advisory and
MUST NOT itself represent approval, publication authority, final review state,
or authorization to execute an action.

### 14.9 Propose

`ProposeCapability` suggests bounded candidate options for consumer review, such
as categories, tags, next checks, or other explicitly contracted proposals.

Proposal semantics are intentionally weaker than recommendation, decision, or
execution semantics:

> AI proposes; consumer software decides.

`Recommend` SHOULD normally be modeled as a specialization of `Propose` rather
than introduced as a separate authority-bearing family.

### 14.10 Transform

`TransformCapability` converts supplied material into another semantic
representation while preserving invariants explicitly declared by the concrete
capability.

A transform MUST state which properties are intended to remain invariant. It
MUST NOT silently add new authority-bearing claims or present inferred additions
as preserved source content.

### 14.11 Synthesize

`SynthesizeCapability` integrates multiple supplied inputs into a structured
combined view.

Synthesis is distinct from summarization and comparison: it may combine themes,
findings, conflicts, gaps, or complementary material, but it MUST preserve the
provenance distinction between supplied inputs and AI-derived integration.

Synthesis MUST NOT collapse disagreement into a fabricated consensus.

### 14.12 Detect

`DetectCapability` surfaces candidate patterns, events, conditions,
contradictions, anomalies, or other bounded phenomena defined by the concrete
capability.

Detection means model-detected candidate, not established fact. Concrete detect
capabilities MUST avoid result semantics that imply verification merely because
a pattern was detected.

### 14.13 Family overlap and specialization

Concrete capabilities SHOULD belong to the family that best describes their
primary consumer intent. A capability MAY conceptually overlap adjacent
families, but its public contract MUST choose one primary family rather than
expose ambiguous generic behavior.

For example:

- `analyze_learning_source()` is primarily `AnalyzeCapability`, even if its
  result contains extracted claims and identified limitations;
- a capability whose primary purpose is to recover entities is
  `ExtractCapability`, even if implementation requires analysis;
- a capability that suggests next checks is `ProposeCapability`, even if it
  first identifies gaps internally.

Internal model behavior does not determine family membership. Consumer-facing
semantic intent does.

### 14.14 Consumer specialization

The intended semantic hierarchy is:

    SemanticCapability
        -> Capability Family
            -> Concrete Capability
                -> optional Consumer Specialization

A consumer-specific capability MAY specialize one of the canonical families
without being promoted into the GiadaWare AI public capability catalog.

Examples include:

    AnalyzeCapability
        -> AnalyzeLogCapability
        -> AnalyzeLearningSourceCapability
        -> AnalyzeInvoiceCapability        # consumer-owned when domain-specific

    CompareCapability
        -> CompareContractVersionsCapability

    ExtractCapability
        -> ExtractDomainEntitiesCapability

Consumer-specific specialization MUST inherit the global semantic contract and
family invariants. It MUST remain provider-independent, read-only,
side-effect-free, typed, validated, advisory, and subject to explicit failure
semantics.

Inheritance here is semantic, not necessarily Python class inheritance. The
runtime representation is deliberately left to the extension-API design work.

### 14.15 Excluded authority-oriented families

The following concepts are explicitly outside the canonical semantic AI family
set because their ordinary meaning crosses or obscures the authority boundary:

- `Decide`;
- `Approve`;
- `Execute`;
- `Validate`;
- `Verify`.

The absence of these families does not forbid deterministic consumer software
from deciding, validating, verifying, approving, or executing. It means those
responsibilities do not belong to GiadaWare AI semantic inference authority.

Generic prompt/completion families are also excluded. `chat`, `complete`, raw
`generate`, provider calls, and prompt execution remain backend or application
mechanics, not semantic capability families.

## 15. Normative summary

The public GiadaWare AI surface is a semantic API, not an LLM plumbing API.

Consumers ask for a bounded semantic capability. Backends adapt inference
providers. GiadaWare AI validates provider output before exposing typed
AI-derived data. Consumers retain all application authority.

The twelve canonical families provide a stable vocabulary for extending that
surface without turning GiadaWare AI into a generic prompt API or an authority
layer.

No model, backend, prompt, runtime, transport, capability family, or
consumer-specific persistence rule is allowed to redefine that boundary.
