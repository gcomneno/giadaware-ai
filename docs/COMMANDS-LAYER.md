# GiadaWare AI Commands Layer

Status: operational convention, version 0.2

This document defines the current shared meaning of the custom command aliases used between Giancarlo and the assistant.

The `$` prefix marks a command belonging to the custom Commands Layer. These aliases are not ordinary natural-language verbs: they request a specific operational behavior.

## `$ok`

Purpose: accept the immediately preceding proposal, decision, checkpoint, or operational result as valid, continue from that accepted state, and propose the next coherent step.

Expected behavior:

- treat the immediately preceding proposal or result as accepted unless the user explicitly narrows the approval;
- preserve the accepted state as the new operational baseline;
- continue from that baseline rather than reopening already accepted choices without new evidence;
- complete any already-authorized continuation that is naturally implied and safe to perform;
- propose the next coherent operational step after the accepted point;
- keep the next step consistent with current scope, repository governance, safety gates, and any explicit user constraints.

`$ok` is therefore not a passive acknowledgement. It carries forward momentum.

Short meaning:

> Accept this, continue from here, and propose the next step.

Operational shorthand:

```text
$ok
  = ACCEPT
  + CONTINUE
  + PROPOSE NEXT STEP
```

## `$ko`

Purpose: reject the immediately preceding proposal, decision, checkpoint, or operational path, stop continuation on that rejected path, preserve everything that remains valid, and propose a coherent alternative or recovery step.

Expected behavior:

- treat the immediately preceding proposal or path as rejected unless the user explicitly narrows the rejection;
- do not continue executing or elaborating the rejected path;
- preserve prior facts, constraints, accepted decisions, artifacts, and work that remain independently valid;
- distinguish the rejected element from surrounding context instead of discarding the whole working state;
- when useful, identify why the rejected path no longer fits the objective or constraints;
- propose the nearest coherent alternative, correction, rollback, or recovery step;
- never reinterpret `$ko` as a request to undo already completed external side effects unless the user explicitly requests that rollback and it is actually possible.

Short meaning:

> Reject this path, preserve what still holds, and propose the best alternative.

Operational shorthand:

```text
$ko
  = REJECT CURRENT PATH
  + PRESERVE VALID CONTEXT
  + PROPOSE ALTERNATIVE
```

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

Two common command patterns are:

```text
$ok
    ↓
accepted operational baseline
    ↓
continuation + next-step proposal
```

```text
$ko
    ↓
rejected current path
    ↓
preserve valid context + alternative proposal
```

The knowledge-persistence pipeline is:

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

- `$ok` may accept a proposal without persisting it;
- `$ko` may reject only the current path while retaining surrounding context;
- `$formalizza` may stop after producing a stable in-conversation formalization;
- `$brevetta` may operate directly on material that is already sufficiently formalized.

## KNA interaction

`$KON` and `$KOFF` control whether the Knowledge Navigation Architecture is active.

When KNA is ON, repository discovery, placement, and routing performed for Commands Layer operations should use the KNA as the canonical navigation layer rather than inventing ad-hoc destinations.

The Commands Layer and KNA have different responsibilities:

- Commands Layer: defines the requested operation;
- KNA: helps determine where relevant knowledge lives and where new knowledge should be routed.

This document records the command aliases and their operational intent; it does not duplicate the full semantics of the KNA or other operational contracts.
