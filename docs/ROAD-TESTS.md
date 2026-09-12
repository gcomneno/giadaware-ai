# GiadaWare AI Runtime Road Tests

## Status

Historical runtime smoke evidence for provider paths.

Road tests are not qualification records and must stay outside
`docs/qualification/`. They document observed operational behavior only.

## 2026-09-12 three-provider structured-output smoke

### Purpose

The road test checked whether three backend/model/provider paths could make a
real call through the shared `AIBackend.generate_json()` structured-output
boundary.

It did not evaluate any public semantic capability contract. In particular, the
Italian result message did not exercise or qualify the Translation capability.

### Shared smoke contract

All providers used the same JSON Schema / structured-output boundary and were
asked to:

- calculate `19 * 23`;
- return expected integer result `437`;
- return language field exactly `Italian`;
- return a non-empty short Italian result message.

Passing this smoke contract shows observed structural and simple arithmetic
success for this one call. It is not evidence of general reasoning ability,
translation quality, factual reliability, safety, current pricing, or semantic
qualification.

### Observed successful results

| Provider path | Call | Semantic smoke check | Latency | Result |
| --- | --- | --- | --- | --- |
| Qwen local: `OllamaBackend` / `qwen2.5:1.5b-instruct` | PASS | PASS | 6.279 s | `{"result": 437, "language": "Italian", "message": "Il risultato è 437."}` |
| DeepSeek remote: `DeepSeekBackend` / `deepseek-v4-flash` | PASS | PASS | 0.933 s | `{"result": 437, "language": "Italian", "message": "Il risultato è 437."}` |
| OpenAI remote: `OpenAIBackend` / `gpt-5.6-luna` | PASS | PASS | 2.279 s | `{"result": 437, "language": "Italian", "message": "Il risultato è 437."}` |

The latency observations are historical single-run observations from
2026-09-12. They are not performance benchmarks, current guarantees, provider
rankings, or routing guidance.

### Operational failures before success

- DeepSeek initially returned HTTP 402 before API funding.
- OpenAI initially returned HTTP 429 before API billing became available.
- Both real provider paths passed after the respective account/billing
  condition was resolved.

These are operational observations only. They do not indicate semantic failure
or semantic qualification.

### Observed cost evidence

Historical single-run API costs observed in provider usage/cost exports for the
successful road test:

| Provider path | Observed API cost | Token notes |
| --- | ---: | --- |
| Qwen local | `$0` | Local runtime; no remote API cost |
| DeepSeek remote | `$0.00007425` | 1 request; 143 input/cache-miss tokens; 88 output tokens; 231 total tokens |
| OpenAI remote | `$0.00008300` | 1 model request; 91 input tokens; 54 output tokens; 145 total tokens |
| Total remote API cost | `$0.00015725` | DeepSeek plus OpenAI successful calls |

These costs and token counts are historical single-run observations from
2026-09-12. They are not current pricing guarantees, normalized cost
comparisons, performance benchmarks, provider rankings, or semantic
qualification evidence.

No account balances, payment details, API keys, or secret values are part of
this record.

## Qualification boundary

Road-test observations may at most become raw evaluation inputs where a
declared evaluation contract makes them relevant. Admission must depend on a
reviewed qualification record for a specific:

```text
capability x backend/model x operating envelope x evaluation evidence
```

A successful provider call through `AIBackend.generate_json()` must not be
conflated with semantic qualification.
