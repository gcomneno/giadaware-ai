from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from jsonschema import ValidationError, validate

from giadaware_ai.backends import OllamaBackend
from giadaware_ai.errors import AIError
from giadaware_ai.read_query import (
    _RESPONSE_SCHEMA,
    _SYSTEM_PROMPT,
    _context_payload,
    validate_read_query_interpretation,
)
from tests.integration.test_semantic_read_query_ollama import (
    SemanticReadQueryOllamaQualificationTests,
)


CASES = (
    ("accepted_english", "Show all observations.", "en"),
    ("accepted_italian", "Mostra tutte le osservazioni.", "it"),
    ("accepted_default", "Show the observation.", "en"),
    ("unsupported_domain", "Write a poem about alpha.", "en"),
    (
        "ambiguous",
        "Show observations for category alpha or category beta with value 18.",
        "en",
    ),
    ("unsupported_mutation", "Delete all observations.", "en"),
    ("unsupported_predictive", "Predict the next observed value.", "en"),
)


@dataclass
class Result:
    case_id: str
    treatment: str
    elapsed_seconds: float
    syntax: str
    structure: str
    semantics: str
    status: str
    error: str | None
    raw_output: dict[str, Any] | None


def prompt(context: Any, request: str, language: str) -> str:
    context_json = json.dumps(
        _context_payload(context),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    return (
        "Semantic query context:\n"
        f"{context_json}\n\n"
        f"Request language: {language}\n"
        "Natural-language request:\n"
        f"{request}"
    )


def classify(
    raw: dict[str, Any],
    *,
    context: Any,
    request: str,
    language: str,
) -> tuple[str, str, str, str, str | None]:
    try:
        syntax = "PASS"
        validate(instance=raw, schema=_RESPONSE_SCHEMA)
        structure = "PASS"
    except ValidationError as exc:
        return "PASS", "FAIL", "UNKNOWN", "INVALID", str(exc)

    try:
        result = validate_read_query_interpretation(
            raw,
            context=context,
            request=request,
            language=language,
        )
    except AIError as exc:
        return "PASS", "PASS", "FAIL", "INVALID", str(exc)

    return (
        syntax,
        structure,
        "PASS",
        result.status.value,
        None,
    )


def run_case(
    backend: OllamaBackend,
    context: Any,
    *,
    case_id: str,
    request: str,
    language: str,
    treatment: str,
) -> Result:
    started = time.perf_counter()

    try:
        raw = backend.generate_json(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=prompt(context, request, language),
            response_schema=_RESPONSE_SCHEMA
            if treatment == "structured"
            else None,
        )
        elapsed = time.perf_counter() - started

        syntax, structure, semantics, status, error = classify(
            raw,
            context=context,
            request=request,
            language=language,
        )

        return Result(
            case_id=case_id,
            treatment=treatment,
            elapsed_seconds=elapsed,
            syntax=syntax,
            structure=structure,
            semantics=semantics,
            status=status,
            error=error,
            raw_output=raw,
        )
    except Exception as exc:
        return Result(
            case_id=case_id,
            treatment=treatment,
            elapsed_seconds=time.perf_counter() - started,
            syntax="FAIL",
            structure="UNKNOWN",
            semantics="UNKNOWN",
            status="ERROR",
            error=f"{type(exc).__name__}: {exc}",
            raw_output=None,
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:11434",
    )
    parser.add_argument(
        "--think",
        choices=("0", "1"),
        default="0",
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    SemanticReadQueryOllamaQualificationTests.setUpClass()
    context = SemanticReadQueryOllamaQualificationTests.interpreter._context

    backend = OllamaBackend(
        model=args.model,
        base_url=args.base_url,
        think=args.think == "1",
    )

    results: list[Result] = []

    for case_id, request, language in CASES:
        for treatment in ("control", "structured"):
            results.append(
                run_case(
                    backend,
                    context,
                    case_id=case_id,
                    request=request,
                    language=language,
                    treatment=treatment,
                )
            )

    payload = {
        "experiment": "structured-output-control",
        "model": args.model,
        "base_url": args.base_url,
        "think": args.think,
        "cases": [asdict(result) for result in results],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    for treatment in ("control", "structured"):
        group = [r for r in results if r.treatment == treatment]
        print(
            f"{treatment.upper()}_SYNTAX="
            f"{sum(r.syntax == 'PASS' for r in group)}/{len(group)}"
        )
        print(
            f"{treatment.upper()}_STRUCTURE="
            f"{sum(r.structure == 'PASS' for r in group)}/{len(group)}"
        )
        print(
            f"{treatment.upper()}_SEMANTICS="
            f"{sum(r.semantics == 'PASS' for r in group)}/{len(group)}"
        )

    print(f"RESULT_FILE={output}")
    print(f"RESULT_COUNT={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
