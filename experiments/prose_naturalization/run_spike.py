from __future__ import annotations

import json
import os
from pathlib import Path

from giadaware_ai.backends import OllamaBackend

from policy import SYSTEM_PROMPT, build_user_prompt


ROOT = Path(__file__).resolve().parent
CORPUS_PATH = ROOT / "corpus.json"
RUN_FLAG = "GIADAWARE_AI_RUN_PROSE_NATURALIZATION_SPIKE"
RUNS_ENV = "GIADAWARE_AI_PROSE_SPIKE_RUNS"
MODEL_ENV = "GIADAWARE_AI_PROSE_SPIKE_MODEL"
BASE_URL_ENV = "GIADAWARE_AI_PROSE_SPIKE_BASE_URL"


def load_corpus() -> list[dict[str, object]]:
    with CORPUS_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("corpus must be a JSON array")
    return data


def validate_candidate(raw: object) -> tuple[str, bool]:
    if not isinstance(raw, dict):
        raise ValueError("candidate must be a JSON object")
    if set(raw) != {"text", "changed"}:
        raise ValueError("candidate must contain exactly text and changed")
    text = raw["text"]
    changed = raw["changed"]
    if not isinstance(text, str) or not text.strip():
        raise ValueError("candidate text must be a non-empty string")
    if not isinstance(changed, bool):
        raise ValueError("candidate changed must be a boolean")
    return text, changed


def preserved_anchors(text: str, anchors: list[str]) -> tuple[list[str], list[str]]:
    present = [anchor for anchor in anchors if anchor in text]
    missing = [anchor for anchor in anchors if anchor not in text]
    return present, missing


def main() -> int:
    if os.environ.get(RUN_FLAG) != "1":
        raise SystemExit(
            f"real-model spike is opt-in; set {RUN_FLAG}=1"
        )

    model = os.environ.get(MODEL_ENV, "qwen2.5:1.5b-instruct")
    base_url = os.environ.get(BASE_URL_ENV, "http://localhost:11434")
    runs = int(os.environ.get(RUNS_ENV, "2"))
    if runs < 1:
        raise ValueError(f"{RUNS_ENV} must be at least 1")

    backend = OllamaBackend(model=model, base_url=base_url)

    for case in load_corpus():
        source = case["text"]
        anchors = case["anchors"]
        if not isinstance(source, str) or not isinstance(anchors, list):
            raise ValueError(f"invalid corpus case: {case.get('id')}")
        if not all(isinstance(anchor, str) for anchor in anchors):
            raise ValueError(f"invalid anchors: {case.get('id')}")

        for run_number in range(1, runs + 1):
            raw = backend.generate_json(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=build_user_prompt(source),
            )
            candidate, model_changed = validate_candidate(dict(raw))
            present, missing = preserved_anchors(candidate, anchors)

            record = {
                "case_id": case["id"],
                "language": case["language"],
                "category": case["category"],
                "expectation": case["expectation"],
                "run": run_number,
                "original": source,
                "candidate": candidate,
                "model_changed": model_changed,
                "observed_changed": candidate != source,
                "anchors_present": present,
                "anchors_missing": missing,
                "deterministic_gate": "PASS" if not missing else "FAIL",
            }
            print(json.dumps(record, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
