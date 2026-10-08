# Structured-output qualification experiment

Status: completed

Research question:

> Does structured-output enforcement reduce syntax/structural failures while
> leaving semantic failures measurable?

External research reference:

`Empirical Study for Structured Output Control in LLMs for Software Engineering`
(arXiv:2606.09395)

## Protocol

The same GiadaWare semantic read-query corpus was evaluated under two treatments:

- control: Ollama JSON mode without a JSON Schema;
- treatment: Ollama JSON mode constrained by the existing GiadaWare response schema.

The following were held constant:

- system prompt;
- user prompt;
- semantic context;
- seven-case corpus;
- model;
- backend;
- thinking configuration;
- post-generation deterministic validation.

No retry, prompt change, parameter tuning, or post-hoc filtering was used.

## Model and runtime

```text
model = qwen3.5:2b-q4_K_M
backend = OllamaBackend
base_url = http://127.0.0.1:11434
thinking = disabled
```

## Results

```text
CONTROL
syntax       = 7/7
structure    = 0/7
semantics    = 0/7
avg latency  = 40.676 s

STRUCTURED
syntax       = 7/7
structure    = 7/7
semantics    = 3/7
avg latency  = 16.018 s
```

The structured treatment converted all seven observed control-side structural
failures into schema-conformant outputs.

Semantic validation nevertheless failed in four of seven structured cases:

- accepted English request: grounding source reference failure;
- accepted Italian request: grounding query fragment failure;
- accepted default request: grounding source reference failure;
- ambiguous request: duplicate parameter construction.

The structured treatment therefore improved structural conformance without
eliminating semantic failures.

## Latency

The structured treatment was faster in this single run:

```text
40.676 s -> 16.018 s
```

This is an observed single-run result only. It does not establish a general
latency advantage for constrained decoding.

## Conclusion

The experiment supports the following project-local evidence:

> Schema-constrained structured output can provide strong structural
> conformance while semantic correctness remains an independent qualification
> problem.

This result supports the existing GiadaWare AI architecture, which already
separates structured-output validation from semantic qualification.

The experiment does not establish universal model behavior, universal
constrained-decoding performance, or universal semantic correctness.

## Artifacts

```text
run_experiment.py
results-qwen3.5-2b-q4_K_M.json
README.md
```
