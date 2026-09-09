# Semantic read-query qualification — qwen2.5:1.5b-instruct

## Identity

- Date: 2026-09-09
- Capability: `SemanticReadQueryInterpreter`
- Capability contract: experimental `0.x`, including issue #28 hardening
- Context: `qualification.observations`
- Context revision: `1`
- Backend: GiadaWare AI `OllamaBackend`
- Model: `qwen2.5:1.5b-instruct`
- Runtime: local Ollama `0.32.15`
- Python: `3.12.3`
- Languages evaluated: English and Italian
- Corpus: `tests/integration/test_semantic_read_query_ollama.py`

## Evaluated semantics

The context declares that an observation request without category or temporal
selectors means all observations. Omission is therefore resolved by a
consumer-owned deterministic default and is not treated as ambiguity.

Material ambiguity is evaluated separately using a boolean expression whose
operator scope cannot be determined from the request.

The effective contract requires:

- exact, case-sensitive grounding references;
- exact parameter placeholders;
- parameter values represented as distinct canonical tokens;
- exactly one positive literal `LIMIT` within `max_result_rows`;
- relation-reference counts within `max_relations`.

## Result

**NOT QUALIFIED**

Observed result after rerunning the unchanged seven-case corpus against the
issue #28 contract:

- 1 passed;
- 6 ended with deterministic `AIInvalidResponseError`;
- runtime: 111.562 seconds.

Passed:

- outside-domain rejection.

Rejected by deterministic validation:

- declared unfiltered default: grounding query fragment absent from the
  candidate query;
- English read request: accepted candidate omitted the required literal
  `LIMIT`;
- Italian read request: grounding cited a source that was not an exact
  semantic context rule;
- mutation request: the model attempted an accepted candidate without the
  required literal `LIMIT`;
- predictive request: the model attempted an accepted candidate without the
  required literal `LIMIT`;
- materially ambiguous boolean request: grounding cited a source that was not
  an exact semantic context rule.

## Interpretation

The composition remains unqualified.

The stricter deterministic contract improves fail-closed behavior: mutation,
prediction and ambiguity attempts did not cross the public result boundary as
validated `accepted` interpretations. They were rejected as invalid backend
responses.

That rejection does not qualify the composition. The model still failed to
produce valid accepted interpretations for supported requests and still made
incorrect semantic status or construction choices for mutation, prediction and
ambiguity cases.

The deterministic checks can reject malformed, inconsistent or visibly
ungrounded output. They do not prove universal natural-language understanding
or correct semantic classification.

GiadaWare AI still performs no query execution and grants no authority to any
candidate. Consumer-owned structural parsing, authorization and read-only
execution controls remain mandatory.

## Admission decision

This backend/model/context combination must not be advertised or admitted as
qualified for the semantic read-query capability.

The result does not invalidate:

- the provider-independent public API;
- deterministic context validation;
- deterministic result validation;
- provenance validation for the grounding manifest;
- fail-closed rejection of invalid backend responses;
- other GiadaWare AI capabilities qualified separately;
- evaluation of another backend/model composition.

Assertions and deterministic validation must not be weakened to accommodate the
reference model.

## Reproduction

```bash
GIADAWARE_AI_RUN_READ_QUERY_QUALIFICATION=1 \
GIADAWARE_AI_QUALIFICATION_MODEL=qwen2.5:1.5b-instruct \
GIADAWARE_AI_QUALIFICATION_BASE_URL=http://127.0.0.1:11434 \
PYTHONPATH=src \
python3 -m unittest discover \
  -s tests/integration \
  -p 'test_semantic_read_query_ollama.py' \
  -v
```
