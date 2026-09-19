# Semantic read-query qualification — qwen3.5:2b-q4_K_M

## Identity

- Date: 2026-09-19
- Capability: `SemanticReadQueryInterpreter`
- Capability contract: experimental `0.x`
- Context: `qualification.observations`
- Context revision: `1`
- Backend: GiadaWare AI `OllamaBackend`
- Model: `qwen3.5:2b-q4_K_M`
- Runtime: local Ollama `0.32.15`
- Thinking: disabled with `GIADAWARE_AI_QUALIFICATION_THINK=0`
- Languages evaluated: English and Italian
- Corpus: `tests/integration/test_semantic_read_query_ollama.py`

## Result

**NOT QUALIFIED**

The unchanged seven-case semantic qualification corpus completed in
279.650 seconds:

- 3 passed;
- 1 assertion failure;
- 3 ended with deterministic `AIInvalidResponseError`.

Passed:

- outside-domain rejection;
- mutation rejection;
- predictive rejection.

Failed:

- declared unfiltered default: the model returned `ambiguous` instead of
  `accepted`;
- English read request: grounding `query_fragment` was absent from the
  candidate query;
- Italian read request: grounding `query_fragment` was absent from the
  candidate query;
- materially ambiguous boolean request: the candidate contained a duplicate
  `category` read-query parameter.

## Interpretation

The backend/model/context composition is not qualified for the semantic
read-query capability.

The model correctly rejected the evaluated outside-domain, mutation and
predictive requests, but did not satisfy the complete qualification contract.
Supported read requests and material ambiguity must also be represented
correctly.

Deterministic validation continued to fail closed where model output violated
the contract. Assertions and validation were not weakened to accommodate the
model.

This semantic qualification result is separate from runtime verification.
`qwen3.5:2b-q4_K_M` successfully ran through the GiadaWare AI `OllamaBackend`
structured-output boundary with thinking disabled, but runtime availability and
valid structured output do not establish semantic qualification.

## Admission decision

This backend/model/context combination must not be advertised or admitted as
qualified for the semantic read-query capability.

The result does not invalidate the provider-independent API, deterministic
validation, or use of the model for separately evaluated capabilities.

## Reproduction

```bash
GIADAWARE_AI_RUN_READ_QUERY_QUALIFICATION=1 \
GIADAWARE_AI_QUALIFICATION_MODEL=qwen3.5:2b-q4_K_M \
GIADAWARE_AI_QUALIFICATION_BASE_URL=http://127.0.0.1:11434 \
GIADAWARE_AI_QUALIFICATION_THINK=0 \
PYTHONPATH=src \
python3 -m unittest discover \
  -s tests/integration \
  -p 'test_semantic_read_query_ollama.py' \
  -v
```
