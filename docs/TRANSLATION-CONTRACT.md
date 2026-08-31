# GiadaWare AI Translation Contract

## Status

Provider-independent semantic translation contract for the experimental `0.x` line.

## Purpose

GiadaWare AI provides translation semantics; consuming products own language presentation.

The public boundary is:

    product / tool
          |
          v
    TranslateTextCapability / AICapabilities.translate_text()
          |
          v
    provider-independent AIBackend
          |
          v
    provider adapter / runtime

Consumers do not depend on Ollama fields, model names, provider SDKs, endpoints, or transport envelopes.

## Semantic operation

A translation request contains:

- source text;
- explicit source language;
- explicit target language.

A successful result contains:

- translated text;
- the same source-language identity;
- the same target-language identity.

`TranslationRequest` and `TranslationResult` are immutable typed values. `TranslateTextCapability` belongs to the `Transform` family. The compatibility facade exposes the same semantics through:

```python
result = ai.translate_text(
    text,
    source_language="English",
    target_language="Italian",
)
```

Language identifiers are explicit caller-owned semantic labels. GiadaWare AI does not silently detect or replace them.

## Translation invariants

Translation must preserve source meaning. It must not silently:

- summarize;
- editorially rewrite;
- enrich or embellish;
- add factual content;
- correct domain claims;
- strengthen or weaken uncertainty;
- alter negation or causal relationships.

Names, numbers, dates, quantities, technical terms, quotations, and other fact-sensitive material must be preserved semantically. Formatting such as paragraphs, lists, Markdown, and line breaks should be preserved where practical.

These rules define the capability contract. Schema-constrained output improves structural compliance but does not prove semantic translation quality.

## Structured output

The current AI-backed implementation requests a schema-constrained object with exactly:

- `translated_text`;
- `source_language`;
- `target_language`.

The language fields are constrained to the requested values and are checked again deterministically before returning `TranslationResult`.

The schema is a GiadaWare AI capability detail. Provider-specific structured-output mechanics remain inside the concrete backend.

## Validation and failures

GiadaWare AI validates result structure and request/result language identity deterministically.

Malformed model/provider output remains an `AIInvalidResponseError`. Backend transport/configuration failures retain the existing shared error hierarchy.

Deterministic validation proves conformance to the result contract; it does not prove that a translation is factually or linguistically correct.

## Capability qualification

Defining the translation capability does not automatically qualify every backend/model composition to perform it.

A provider/model may satisfy transport and JSON-schema requirements while still producing semantically poor translations. Translation quality and operating-envelope qualification therefore remain separate evaluation/admission concerns.

No reference model is declared translation-qualified merely by this contract.

## Static localization boundary

GiadaWare AI does not own product localization.

In particular, this capability does not add or imply:

- GUI language selectors;
- product-level `--language` options;
- localized application menus;
- canonical-English repository migrations;
- multilingual documentation policy;
- mandatory runtime AI translation.

Stable UI strings should normally use deterministic localization catalogs. GiadaWare AI may be used offline to produce candidate translations for such catalogs, but products remain responsible for review, storage, publication, and language selection.

## Provider independence

The semantic API does not require an LLM-specific consumer contract. Current implementations may use `AIBackend`; future local or specialized translation-provider adapters may be introduced behind the same semantic capability boundary without changing consumer translation semantics.

## Authority boundary

Translation output is derived presentation data, not application authority.

> GiadaWare AI provides translation semantics; products own language presentation.
