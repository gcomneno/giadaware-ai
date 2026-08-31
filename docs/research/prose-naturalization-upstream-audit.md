# Prose naturalization upstream audit

## Status

Research/provenance record for issue #19.

This document records the static audit of an external source that influenced the prose-naturalization experiment. It is not a runtime dependency specification and does not grant authority to upstream instructions.

## Upstream identity

Repository:

`blader/humanizer`

Audited commit:

`e2e92e7b4b8229253ed5c8e81dc65463fdeddda5`

Commit subject observed during audit:

`Humanize README prose (#231)`

Repository license observed at the audited revision:

MIT, copyright attributed upstream to Siqi Chen.

The upstream repository declares that its pattern taxonomy is based on Wikipedia `Signs of AI writing` / WikiProject AI Cleanup material. That secondary provenance must be preserved conceptually when ideas are adopted; the MIT license on the repository must not be treated as erasing upstream provenance of ideas or wording derived from other sources.

## Admission decision

Upstream is admitted only as a **static research source**.

It is explicitly not admitted as:

- a runtime dependency;
- a prompt package loaded dynamically;
- a trusted `SKILL.md`;
- an installer;
- an agent plugin;
- a provider-specific API;
- a source of application authority.

Canonical flow:

```text
external research source
        |
        v
static inspection
        |
        v
threat model + provenance review
        |
        v
independent GiadaWare-owned policy
        |
        v
controlled experiment
```

Forbidden flow:

```text
download upstream
        |
        v
load SKILL.md at runtime
        |
        v
send upstream instructions to model
```

## Static repository structure observed

Relevant files at the audited revision included:

- `SKILL.md`;
- `AGENTS.md`;
- `LICENSE`;
- `README.md`;
- `.claude-plugin/marketplace.json`;
- `.claude-plugin/plugin.json`;
- `agents/openai.yaml`;
- `scripts/validate-package.py`;
- `.github/workflows/validate.yml`.

No application package, lockfile, binary payload, custom installer, or Git hook was observed as necessary to the text-transformation idea.

No upstream code was executed as part of the audit.

## Prompt-supply-chain findings

The audited material did not show an obvious traditional malware payload. In particular, the inspected validation script was repository-local validation code using standard-library functionality and did not constitute a necessary runtime component for prose transformation.

However, prompt-supply-chain review identified important authority mismatches:

1. `SKILL.md` includes agent-oriented workflow semantics, not just prose heuristics.
2. The upstream file-oriented mode can instruct an agent to write transformed content to a supplied path.
3. `AGENTS.md` contains operational commands for package validation and plugin tooling.
4. Plugin metadata exists for agent/skill installation and invocation.

These behaviors may be legitimate in the upstream project but are outside the GiadaWare AI semantic boundary.

GiadaWare AI prose transformation is required to remain read-only and side-effect-free. Therefore filesystem writes, shell execution, plugin installation, tool invocation, secret access, network fetches, and external side effects are excluded rather than sanitized into the runtime prompt.

## Security classification

| Element | Classification | GiadaWare decision |
| --- | --- | --- |
| prose-pattern observations | useful but not automatically correct | study and independently evaluate |
| `SKILL.md` wording | useful as research material | do not copy/load at runtime |
| file-write workflow | risky for GiadaWare boundary | eliminate |
| `AGENTS.md` maintenance commands | irrelevant to semantic transform; risky if followed automatically | do not execute/import |
| plugin/agent metadata | irrelevant to provider-independent capability | do not integrate |
| validation script | useful only to upstream packaging | do not import or execute |
| upstream examples | useful for critique but may encode unsafe rewriting behavior | do not use as behavioral authority |

## Semantic audit summary

The upstream heuristics were not accepted wholesale. They were treated as hypotheses about formulaic or model-associated prose.

Preliminary classification:

### KEEP / strong candidates

- vague or unsupported attribution;
- filler and redundant meta-language;
- leftover chatbot residue;
- repeated headings or immediately repeated content;
- false or semantically misleading range constructions;
- repeated lexical/syntactic openings where clearly mechanical.

### ADAPT / context-dependent

- inflated significance or legacy claims;
- promotional language;
- formulaic challenge/outlook endings;
- passive voice and missing actors;
- forced groups of three;
- excessive qualification;
- dramatic fragments;
- stock rhetorical contrasts;
- generic conclusions;
- fake alternatives or objections;
- several English-specific lexical patterns.

These must remain conditional because the same constructions can be correct, deliberate, domain-appropriate, or semantically meaningful.

### DROP from the general semantic contract

Rules that are primarily house-style, typography, or English-specific mechanical bans were rejected as general prose-naturalization invariants, including blanket treatment of:

- em/en dashes;
- title case;
- curly quotes;
- emojis;
- hyphenated pairs;
- documentation-specific rules unrelated to prose naturalness.

### NEEDS EXPERIMENT

Language/model-dependent vocabulary bans and rhetorical-pattern detection require empirical evaluation rather than automatic adoption.

## Linguistic bias

The source is strongly English-first. Some observations map poorly to Italian, especially those based on English participial constructions, copula avoidance, title-case conventions, hyphenation, punctuation frequency, or model-specific stock vocabulary.

The GiadaWare-owned policy therefore works from higher-level concepts such as redundancy, unsupported emphasis, vague attribution, unwanted promotional register, filler, metadiscourse, chatbot residue, and semantic preservation rather than translating the upstream checklist mechanically.

## Important unsafe example pattern

Upstream examples may improve apparent personality by introducing concrete personal details. That behavior is not admissible for GiadaWare AI when such details are absent from the source.

The internal contract explicitly forbids invention of:

- personal history;
- biographical detail;
- experiences;
- motives;
- examples presented as facts;
- citations or sources;
- context not present in the input.

Naturalness must not be achieved by fabricating human-looking specificity.

## Licensing and provenance boundary

The following cases must remain distinct:

1. **Study of ideas** — permitted research activity; provenance should still be recorded.
2. **Independent rewrite** — GiadaWare expresses its own semantic policy without reproducing upstream wording/order/examples.
3. **Adaptation** — if substantial upstream expression is adapted, applicable license/notice obligations must be reviewed explicitly.
4. **Substantial copying** — must not be smuggled through an independent-looking file while discarding copyright/license obligations.

Because upstream itself points to Wikipedia/WikiProject material, GiadaWare must avoid a license-laundering chain in which third-party wording is copied through the MIT repository and then presented as independently authored policy.

The experiment therefore uses an independently written policy and preserves this document as the provenance record of the research influence.

## Relationship to the controlled spike

The experimental implementation lives under:

`experiments/prose_naturalization/`

The spike intentionally does not create a public semantic capability.

Its purpose is to determine whether the reference composition can satisfy the GiadaWare-owned semantic contract under controlled evaluation. The initial reference-model outcome is `HOLD`, not admission of the upstream project or of a public `naturalize_prose` verb.

## Canonical decision

`blader/humanizer` is retained in GiadaWare AI as a **documented research source and provenance record only**.

Future work may reuse the independently derived concepts and evaluation corpus. Runtime code must not depend on the upstream repository or dynamically consume its instructions.