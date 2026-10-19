"""Run with an isolated consumer Python (-I), never with PYTHONPATH=src."""

import inspect
import json
import sys
import unittest
from importlib import metadata, resources
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import giadaware_ai
from giadaware_ai import (
    AICapabilities,
    AIConfigurationError,
    AIError,
    AIInvalidResponseError,
    AITimeoutError,
    AIUnavailableError,
    AIUnsupportedCapabilityError,
    CapabilityFamily,
    LogAnalysis,
    Severity,
    SynthesizeCapability,
)
from giadaware_ai.backend import AIBackend
from giadaware_ai.backends import OllamaBackend


class InstalledDistributionTests(unittest.TestCase):
    def test_imports_come_from_consumer_environment(self):
        self.assertNotEqual(sys.prefix, sys.base_prefix)
        self.assertTrue(Path(giadaware_ai.__file__).is_relative_to(sys.prefix))
        self.assertEqual(metadata.version("giadaware-ai"), "0.0.2")
        self.assertEqual(metadata.metadata("giadaware-ai")["Requires-Python"], ">=3.11")
        self.assertTrue(resources.files("giadaware_ai").joinpath("py.typed").is_file())

    def test_backend_primitive_and_mocked_schema_generation(self):
        signature = inspect.signature(AIBackend.generate_json)
        for name in ("system_prompt", "user_prompt", "response_schema"):
            self.assertEqual(signature.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIsNone(signature.parameters["response_schema"].default)
        backend = OllamaBackend(model="packaging-smoke", timeout=1, think=False)
        schema = {"type": "object", "properties": {"text": {"type": "string"}}}
        for constraint in (None, schema):
            envelope = {"message": {"content": '{"text": "candidate"}'}}
            with patch("urllib.request.urlopen", return_value=BytesIO(json.dumps(envelope).encode())) as call:
                result = backend.generate_json(
                    system_prompt="Synthetic packaging test",
                    user_prompt="Synthetic input",
                    response_schema=constraint,
                )
            self.assertEqual(result, {"text": "candidate"})
            payload = json.loads(call.call_args.args[0].data)
            self.assertEqual(payload["format"], constraint if constraint is not None else "json")
        with self.assertRaises(AIConfigurationError):
            OllamaBackend(model="")

    def test_synthesize_extension_executes_and_validates(self):
        class FakeBackend:
            def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
                return {"text": user_prompt}

        class ConsumerSynthesis(SynthesizeCapability[str, str]):
            def execute(self, value: str) -> str:
                raw = self._backend.generate_json(
                    system_prompt="Synthetic test only",
                    user_prompt=value,
                    response_schema={"type": "object"},
                )
                text = raw.get("text")
                if not isinstance(text, str) or not text:
                    raise AIInvalidResponseError("text must be non-empty")
                return text

        self.assertTrue(inspect.isabstract(SynthesizeCapability))
        capability = ConsumerSynthesis(FakeBackend())
        self.assertEqual(capability.family, CapabilityFamily.SYNTHESIZE)
        self.assertEqual(capability.execute("candidate"), "candidate")
        with self.assertRaises(AIInvalidResponseError):
            capability.execute("")

    def test_typed_error_family_is_catchable(self):
        for error in (
            AIConfigurationError, AIInvalidResponseError, AITimeoutError,
            AIUnavailableError, AIUnsupportedCapabilityError,
        ):
            with self.subTest(error=error.__name__), self.assertRaises(AIError):
                raise error("synthetic failure")
        self.assertFalse(issubclass(AITimeoutError, AIUnavailableError))

    def test_facade_returns_validated_public_result(self):
        class FakeBackend:
            def generate_json(self, *, system_prompt, user_prompt, response_schema=None):
                return {
                    "summary": "Synthetic failure", "severity": "high",
                    "possible_causes": [], "suggested_next_steps": [],
                }

        result = AICapabilities(FakeBackend()).analyze_log("ERROR synthetic failure")
        self.assertIsInstance(result, LogAnalysis)
        self.assertEqual(result.severity, Severity.HIGH)


if __name__ == "__main__":
    unittest.main(verbosity=2)
