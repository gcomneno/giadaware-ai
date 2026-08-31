# Prose naturalization spike

Issue: #19

Status: experiment only. This directory does not define or expose a public GiadaWare AI capability.

## Question

Can the current reference model perform a bounded prose transformation that reduces unwanted formulaic writing while preserving the semantic content of the supplied text?

The experiment studies ideas found during a static audit of `blader/humanizer` at commit `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5`, but it does not copy, load, install, execute, or depend on that project or its `SKILL.md`.

The canonical research/provenance record is:

`docs/research/prose-naturalization-upstream-audit.md`

The internal policy in this directory is independently written for the GiadaWare AI semantic contract.

## Architectural boundary

The experiment uses the existing backend boundary only:

```text
controlled corpus
      |
      v
GiadaWare-owned experimental policy
      |
      v
AIBackend.generate_json()
      |
      v
reference Ollama backend
```

It deliberately does not add `AICapabilities.naturalize_prose()`, a concrete `TransformCapability`, a public result model, or a validator to `src/giadaware_ai`.

## Strong invariants

A candidate rewrite must preserve:

- factual propositions;
- names and named references;
- numbers, dates, quantities, units, and version identifiers;
- quotations and citations;
- negation;
- causal relationships;
- epistemic strength and uncertainty;
- relevant technical terminology;
- source language;
- intended register when that register is functional.

A candidate rewrite must not invent facts, sources, quotations, citations, personal details, context, or claims. It must not strengthen or weaken claims.

AI-detector performance, claims of human authorship, and claims of detector resistance are explicitly excluded from success criteria.

## Corpus

`corpus.json` contains ten controlled cases: five categories represented once in Italian and once in English.

Categories:

1. naturally written prose;
2. deliberately formulaic prose;
3. already manually revised prose;
4. fact-sensitive prose;
5. intentionally schematic technical prose.

Each case declares literal anchors that deterministic checks require the output to preserve. Anchors are deliberately incomplete: passing them does not prove semantic preservation.

## Running

From the repository root:

```bash
PYTHONPATH=src python -m unittest discover -s experiments/prose_naturalization/tests -v
```

The real-model experiment is opt-in:

```bash
GIADAWARE_AI_RUN_PROSE_NATURALIZATION_SPIKE=1 \
PYTHONPATH=src \
python experiments/prose_naturalization/run_spike.py
```

Default reference configuration:

- model: `qwen2.5:1.5b-instruct`;
- endpoint: `http://localhost:11434`.

The runner writes no files and performs no network access other than the configured backend request itself. Results are printed as JSON for manual capture/review by the operator.

## Evaluation

For each run, review:

- semantic preservation;
- factual preservation;
- omissions;
- unsupported additions;
- naturalness/readability;
- redundancy;
- transformation aggressiveness.

Run the corpus repeatedly to inspect reasonable stability. The output need not be textually identical between runs.

The deterministic checks are gates, not proof. A case that preserves every literal anchor can still fail semantically.

## Decision gate

Classify failures separately as policy/prompt, model, backend/runtime, or architectural limitations.

The spike ends with `GO`, `GO WITH CHANGES`, `HOLD`, or `REJECT`. Only a later issue may propose a public concrete `TransformCapability` specialization.
