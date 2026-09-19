# Semantic Read-Query Interpreter

## Status

Experimental public capability for the GiadaWare AI `0.x` line.

The interpreter converts a natural-language request into typed, untrusted
read-query data over a semantic context supplied by the consumer.

Canonical boundary:

> GiadaWare AI interprets. The consumer validates, authorizes and executes.

## Public API

```python
import json

from giadaware_ai import (
    SemanticReadQueryInterpreter,
    SemanticReadQueryRequest,
    semantic_query_context_from_mapping,
)

with open("read-query-context.json", encoding="utf-8") as stream:
    context = semantic_query_context_from_mapping(json.load(stream))

interpreter = SemanticReadQueryInterpreter(
    backend=backend,
    context=context,
)

result = interpreter.execute(
    SemanticReadQueryRequest(
        text="Show the latest observation for category alpha.",
        language="en",
    )
)
```

The capability belongs to the `TransformCapability` family and remains
provider-independent. Its public contract does not mention Ollama, model names,
endpoints, transports or provider response formats.

## Consumer-owned context

`SemanticQueryContext` is immutable and versioned through:

- `context_id`;
- `revision`.

The context declares:

- query dialect;
- supported request languages;
- domain description;
- readable tables or views;
- columns, data types and descriptions;
- named domain concepts with explicit synonyms;
- named relationships whose endpoints reference declared relations and columns;
- positive query limits for maximum result rows and joined relations;
- semantic and temporal interpretation rules;
- accepted and rejected examples;
- allowed query features.

Concepts, synonyms, relationships, limits and semantic rules are explicit,
typed, consumer-owned configuration. They do not become intrinsic GiadaWare AI
domain knowledge and they grant no execution authority.

Decoded JSON must pass through
`semantic_query_context_from_mapping()`. The loader:

- requires the exact supported field set;
- rejects unknown or missing fields;
- validates nested relations, columns, concepts, relationships and limits;
- rejects dangling relationship endpoints and invalid positive limits;
- converts lists to immutable tuples;
- does not mutate the supplied mapping;
- rejects provider or execution-authority fields.

A context describes meaning. It grants no database, filesystem or application
authority.

## Interpretation outcomes

`ReadQueryInterpretation.status` has exactly three values:

| Status | Meaning |
| --- | --- |
| `accepted` | The backend proposes that the complete request is representable as a read query in the supplied context. |
| `unsupported` | The request is outside the context or asks for mutation, administration, prediction or advice. |
| `ambiguous` | A material interpretation choice cannot be resolved from the request and context. |

An accepted result contains:

- a normalized interpretation;
- a candidate query;
- scalar bound parameters;
- a grounding manifest for query fragments derived from the request or an exact
  semantic rule in the supplied context;
- trusted library-generated context identity, revision and request language.

Each `ReadQueryGrounding` entry contains:

- `query_fragment`: the exact fragment present in the candidate query;
- `field`: the semantic field constrained by that fragment;
- `source_kind`: either `request` or `context_rule`;
- `source_reference`: an exact fragment of the original request, or an exact
  semantic rule from the validated context.

Unsupported and ambiguous results are both fail-closed rejection outcomes.
They contain no candidate query, parameters or grounding and include a reason.
A consumer must not execute, approximate, complete or otherwise recover a query
from either outcome. Only an `accepted` result may proceed to the consumer's
independent structural and authorization gates.

A consumer context may declare deterministic defaults for omitted selectors.
Such a rule can make an otherwise underspecified request unambiguous. Defaults
must be explicit in the supplied context; the interpreter must not invent them.

## Validation guarantees

GiadaWare AI deterministically validates:

- exact model-output fields;
- status values;
- status/query/reason invariants;
- parameter names, uniqueness and JSON-scalar values;
- finite floating-point values;
- grounding manifest shape and closed source kinds;
- case-sensitive literal presence of every `query_fragment` in the candidate
  query;
- case-sensitive literal presence of request references in the original
  request;
- exact, case-sensitive membership of context-rule references in validated
  semantic rules;
- exactly one grounding entry for every returned parameter;
- the exact `:<parameter-name>` placeholder in that grounding query fragment;
- the parameter value in canonical scalar form as a distinct token
  delimited by Unicode non-word characters or string boundaries within its
  source reference;
- exactly one positive literal `LIMIT`, not greater than
  `limits.max_result_rows`;
- no more `FROM` or `JOIN` relation references than `limits.max_relations`;
- trusted context identity generated by library code.

This validation proves conformance to the public result contract. It does not
prove that a candidate query is semantically complete, valid for a concrete
database, safe, efficient or authorized.

In particular, schema-constrained generation and `status="accepted"` never
mean `safe_to_execute`.

## Consumer authority boundary

The consumer must treat every accepted candidate as untrusted derived data.

Before execution, a database consumer is responsible for controls such as:

- parsing the candidate structurally;
- allowing one read-only statement only;
- allowlisting relations, columns, operators and functions;
- rejecting DML, DDL, transaction control and administration;
- matching placeholders to parameters;
- opening its database read-only;
- installing engine-specific authorizers;
- enforcing row, time and complexity limits;
- deciding how normalized meaning and results are presented.

GiadaWare AI performs none of these operations and never opens a database.

## Semantic completeness and grounding

The interpreter prompt requires the complete request to be represented, forbids
silently dropped clauses and requires each material query constraint to be
linked to an exact source in either the request or the supplied semantic rules.

Deterministic validation verifies the declared links with case-sensitive
literal matching: query fragments must occur in the candidate query, request
references must occur in the original request, and context-rule references must
exactly match a validated semantic rule. Parameter grounding must also contain
the exact placeholder and the parameter value in canonical scalar form
as a distinct Unicode word-delimited token.

The current exploratory limit checks require one positive literal `LIMIT`, count
each `FROM` or `JOIN` relation reference, and compare those values with the
validated context limits. These checks deliberately define a small operational
contract; they are not a general SQL parser. Validation can reject malformed or
visibly ungrounded output, but it does not parse or authorize SQL and cannot
prove universal natural-language understanding or semantic completeness.

Consumers must therefore retain their independent authority gate, and each
backend/model composition must be qualified for the intended language, domain
and operating envelope.

## Deterministic tests

Unit tests use controlled backends and require no model server:

```bash
PYTHONPATH=src python -m unittest discover -s tests/unit -v
```

They verify the public types, context loader, result invariants, grounding
checks, provider independence and absence of execution behavior.

Controlled responses demonstrate contract behavior. They do not qualify a real
model's semantic competence.

## Opt-in real-runtime qualification

A real-runtime evaluation must be separate from deterministic CI and identify:

- semantic capability and contract revision;
- exact context identifier and revision;
- backend/provider adapter;
- model and relevant runtime version;
- supported languages;
- evaluation corpus and operating envelope.

The corpus should include:

- accepted Italian and English read requests;
- paraphrases and synonyms;
- dates, ranges, comparisons and boolean relations;
- aggregation and grouping;
- outside-domain requests;
- materially ambiguous requests;
- predictive and advisory requests;
- mutation and administration requests;
- attempts to introduce ungrounded constraints;
- requests containing multiple clauses where none may be dropped.

Qualification must verify both classification and preservation of every material
constraint. Technical availability or valid JSON output is insufficient.

Real-provider evaluation is opt-in and must not become a requirement for the
deterministic unit suite.

The repository provides a reference qualification corpus:

```bash
GIADAWARE_AI_RUN_READ_QUERY_QUALIFICATION=1 \
PYTHONPATH=src \
python -m unittest discover \
  -s tests/integration \
  -p 'test_semantic_read_query_ollama.py' \
  -v
```

Optional infrastructure overrides are:

- `GIADAWARE_AI_QUALIFICATION_MODEL`;
- `GIADAWARE_AI_QUALIFICATION_BASE_URL`;
- `GIADAWARE_AI_QUALIFICATION_THINK` (`0` disables thinking, `1` enables it;
  when absent, the backend default is preserved).

A failing qualification does not justify weakening assertions or silently
accepting the composition. It means that the tested backend/model/context
combination is not qualified for the declared envelope.

The 2026-09-09 reference evaluation of `qwen2.5:1.5b-instruct` is recorded in
`docs/qualification/semantic-read-query-qwen2.5-1.5b-2026-09-09.md`. That
composition is explicitly **not qualified** for this capability.

The 2026-09-19 evaluation of `qwen3.5:2b-q4_K_M`, with thinking disabled, is
recorded in
`docs/qualification/semantic-read-query-qwen3.5-2b-q4_K_M-2026-09-19.md`.
That composition is also explicitly **not qualified** for this capability.

## Non-goals

The capability does not provide:

- SQL execution;
- database connections or credentials;
- structural SQL authorization;
- generic chat;
- consumer-specific domain knowledge;
- mutation capabilities;
- prediction or advice;
- universal semantic-correctness guarantees.

