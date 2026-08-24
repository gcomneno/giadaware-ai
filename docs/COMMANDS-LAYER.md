# GiadaWare AI Commands Layer

Status: operational convention, version 0.1

This document defines the current shared meaning of the custom command aliases used between Giancarlo and the assistant.

The `$` prefix marks a command belonging to the custom Commands Layer. These aliases are not ordinary natural-language verbs: they request a specific operational behavior.

## `$formalizza`

Purpose: transform an idea, discovery, observation, candidate, or decision that emerged in conversation into an explicit, structured, governable object.

Expected behavior:

- clarify what is being formalized;
- define purpose, boundaries, and semantics;
- distinguish facts, hypotheses, constraints, and decisions where relevant;
- assign state, classification, provenance, and verification criteria when useful;
- produce a formulation stable enough to be retained, evaluated, developed, routed, or rejected.

`$formalizza` does not by itself require repository mutation, file creation, issue/PR creation, or persistence outside the conversation.

Short meaning:

> Put this into a clear, structured, governable form.

## `$brevetta`

Purpose: take knowledge, a decision, a formalization, or a discovery that is important enough not to remain only in chat, identify the most appropriate repository and persistence location, and put it in writing there according to that repository's governance.

Expected behavior:

- identify the semantically appropriate repository or project;
- inspect and respect applicable governance, including `AGENTS.md`, repository structure, conventions, and workflow rules;
- determine the correct persistence location before writing;
- translate the material into the appropriate repository artifact or documentation form;
- avoid arbitrary placement and unnecessary duplication;
- when the operating environment permits it and the applicable workflow allows it, perform the persistence operation and record it through the repository's normal version-control process.

`$brevetta` is therefore a command for knowledge placement, repository routing, and documentary persistence.

It does **not** mean:

- legal patent filing;
- patent search;
- patent reconnaissance;
- patentability analysis.

Short meaning:

> This is worth keeping: find it the right home and write it down there.

## Relationship between the commands

The common pipeline is:

```text
$formalizza
    ↓
structured, governable object
    ↓
$brevetta
    ↓
repository routing + documentary persistence
```

The commands remain independent:

- `$formalizza` may stop after producing a stable in-conversation formalization;
- `$brevetta` may operate directly on material that is already sufficiently formalized.

## KNA interaction

`$KON` and `$KOFF` control whether the Knowledge Navigation Architecture is active.

When KNA is ON, repository discovery, placement, and routing performed for Commands Layer operations should use the KNA as the canonical navigation layer rather than inventing ad-hoc destinations.

The Commands Layer and KNA have different responsibilities:

- Commands Layer: defines the requested operation;
- KNA: helps determine where relevant knowledge lives and where new knowledge should be routed.

This document records the command aliases and their operational intent; it does not duplicate the full semantics of the KNA or other operational contracts.
