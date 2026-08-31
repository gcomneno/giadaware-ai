import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy.py"
RUNNER_PATH = ROOT / "run_spike.py"
CORPUS_PATH = ROOT / "corpus.json"

spec = importlib.util.spec_from_file_location("prose_spike_policy", POLICY_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load spike policy")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

sys.path.insert(0, str(ROOT))
runner_spec = importlib.util.spec_from_file_location("prose_spike_runner", RUNNER_PATH)
if runner_spec is None or runner_spec.loader is None:
    raise RuntimeError("cannot load spike runner")
runner = importlib.util.module_from_spec(runner_spec)
runner_spec.loader.exec_module(runner)


class ProseNaturalizationSpikeContractTests(unittest.TestCase):
    def test_policy_does_not_reference_upstream_runtime(self) -> None:
        lowered = policy.SYSTEM_PROMPT.lower()
        self.assertNotIn("blader", lowered)
        self.assertNotIn("humanizer", lowered)
        self.assertNotIn("skill.md", lowered)

    def test_policy_excludes_detector_evasion(self) -> None:
        lowered = policy.SYSTEM_PROMPT.lower()
        self.assertIn("do not optimize for ai detectors", lowered)
        self.assertIn("do not claim the result is human-written", lowered)

    def test_empty_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            policy.build_user_prompt("   ")

    def test_non_string_input_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            policy.build_user_prompt(123)

    def test_candidate_requires_exact_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly text and changed"):
            runner.validate_candidate({"text": "ok", "changed": True, "extra": 1})

    def test_candidate_accepts_exact_contract(self) -> None:
        self.assertEqual(
            ("rewritten", True),
            runner.validate_candidate({"text": "rewritten", "changed": True}),
        )

    def test_response_schema_requires_exact_contract(self) -> None:
        self.assertEqual("object", runner.RESPONSE_SCHEMA["type"])
        self.assertEqual(["text", "changed"], runner.RESPONSE_SCHEMA["required"])
        self.assertFalse(runner.RESPONSE_SCHEMA["additionalProperties"])
        properties = runner.RESPONSE_SCHEMA["properties"]
        self.assertEqual({"text", "changed"}, set(properties))
        self.assertEqual({"type": "string"}, properties["text"])
        self.assertEqual({"type": "boolean"}, properties["changed"])

    def test_corpus_has_required_bilingual_categories(self) -> None:
        with CORPUS_PATH.open(encoding="utf-8") as handle:
            corpus = json.load(handle)

        required = {
            "natural",
            "formulaic",
            "manually_reviewed",
            "fact_sensitive",
            "technical_schematic",
        }
        by_language = {"it": set(), "en": set()}
        for case in corpus:
            by_language[case["language"]].add(case["category"])

        self.assertEqual(required, by_language["it"])
        self.assertEqual(required, by_language["en"])

    def test_fact_sensitive_cases_have_multiple_literal_anchors(self) -> None:
        with CORPUS_PATH.open(encoding="utf-8") as handle:
            corpus = json.load(handle)

        cases = [case for case in corpus if case["category"] == "fact_sensitive"]
        self.assertEqual(2, len(cases))
        for case in cases:
            self.assertGreaterEqual(len(case["anchors"]), 5)
            for anchor in case["anchors"]:
                self.assertIn(anchor, case["text"])


if __name__ == "__main__":
    unittest.main()
