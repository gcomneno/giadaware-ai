# AnalyzeLearningSourceCapability

## Status

Implemented public semantic capability for the experimental `0.x` line.

`AnalyzeLearningSourceCapability` belongs to `AnalyzeCapability` and exposes the
consumer-facing facade operation:

    analyze_learning_source(text: str) -> LearningSourceAnalysis

The capability is read-only, provider-independent, advisory, and subject to the
global Semantic Capability Contract.

## Result contract

`LearningSourceAnalysis` is immutable and contains:

- `central_thesis: str`;
- `key_concepts: tuple[str, ...]`;
- `source_claims: tuple[SourceClaim, ...]`;
- `practical_applications: tuple[str, ...]`;
- `limitations: tuple[str, ...]`;
- `review_questions: tuple[str, ...]`.

`SourceClaim` is immutable and contains:

- `claim: str`;
- `support: ClaimSupport`.

`ClaimSupport` has exactly three values:

- `EXPLICIT = "explicit"`;
- `INFERRED = "inferred"`;
- `UNCLEAR = "unclear"`.

`ClaimSupport` describes only the relationship between a candidate claim and the
supplied source text. It does not establish factual truth, correctness,
independent verification, approval, or editorial authority.

## Validation boundary

Raw backend output is untrusted. GiadaWare AI validates all required fields and
claim entries before returning `LearningSourceAnalysis`.

GiadaWare AI validation means schema and semantic-contract conformance only.

Missing fields, malformed claim objects, empty required strings, or unsupported
`ClaimSupport` values raise `AIInvalidResponseError`.

Empty or non-string consumer input is rejected before inference.

Backend availability and timeout failures remain explicit and are not converted
into empty or success-looking results.

## Authority boundary

Learning-source analysis is advisory semantic data:

    AI-derived learning analysis
        != editorial candidate
        != reviewed source
        != review checkpoint
        != publication authority

Any promotion into editorial candidate, review, workflow, or publication state
is consumer-owned and outside GiadaWare AI validation.

GiadaWare AI validation does not mean factual verification, evidence
acceptance, editorial acceptance, or workflow promotion.

The capability does not expose fields for:

- facts or verified facts;
- verified claims;
- correctness;
- confidence as an authority proxy;
- review or approval state;
- publication readiness;
- canonical lesson text;
- recommended final text.

Provider-supplied fields claiming backend/model identity, authority, hashes, or
other trusted metadata are not part of the semantic result type and are not
promoted by validation.

## Consumer boundary

Consumer code may use:

    analysis = ai.analyze_learning_source(text)

without knowing the provider, model, prompt, base URL, or transport envelope.

Filesystem paths, input hashes, persistence envelopes, pipeline association,
restart/reuse semantics, and labels such as `ai-advisory` remain consumer-owned
artifact concerns and are not part of `LearningSourceAnalysis`.
