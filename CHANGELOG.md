# Changelog

## Unreleased

### Added

- Experimental M0 public package boundary.
- Semantic `analyze_log()` capability.
- Replaceable `AIBackend` protocol.
- Schema-constrained JSON backend boundary.
- Optional provider-independent JSON Schema constraints for `generate_json()`.
- Ollama backend.
- Ollama structured-output mapping for schema-constrained JSON generation.
- Typed immutable log-analysis result.
- Structured AI-output validation.
- Explicit failure hierarchy.
- Deterministic fake-backend tests.
- Opt-in Ollama integration tests, including schema-constrained output coverage.
- Installed-wheel verification.
- Semantic capability contract and canonical capability-family taxonomy.
- Qualification/admission design that separates backend availability from
  semantic capability competence.
- Learning-source analysis capability.
- Translation capability and provider-independent translation contract.
- Semantic read-query interpreter and reference qualification record.
- DeepSeek backend as an optional remote `AIBackend` implementation.
- OpenAI backend as an optional remote `AIBackend` implementation.
- Provider status taxonomy for supported, runtime-verified, and semantically
  qualified compositions.
- Three-provider runtime road-test documentation for Qwen local, DeepSeek
  remote, and OpenAI remote provider paths.

### Changed

- Prose naturalization remains experiment-only with the current decision held
  at `HOLD`; no public naturalization capability is exposed.
