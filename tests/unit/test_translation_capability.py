import unittest

from giadaware_ai import (
    AICapabilities,
    AIInvalidResponseError,
    CapabilityFamily,
    TranslateTextCapability,
    TranslationRequest,
    TranslationResult,
)


class CapturingBackend:
    def __init__(self, response):
        self.response = response
        self.response_schema = None
        self.system_prompt = None
        self.user_prompt = None

    def generate_json(
        self,
        *,
        system_prompt,
        user_prompt,
        response_schema=None,
    ):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.response_schema = response_schema
        return self.response


class TranslationCapabilityTests(unittest.TestCase):
    def test_translates_through_provider_independent_transform_capability(self):
        backend = CapturingBackend(
            {
                "translated_text": "Ciao mondo.",
                "source_language": "English",
                "target_language": "Italian",
            }
        )
        capability = TranslateTextCapability(backend)

        result = capability.execute(
            TranslationRequest(
                text="Hello world.",
                source_language="English",
                target_language="Italian",
            )
        )

        self.assertEqual(capability.family, CapabilityFamily.TRANSFORM)
        self.assertEqual(
            result,
            TranslationResult(
                translated_text="Ciao mondo.",
                source_language="English",
                target_language="Italian",
            ),
        )
        self.assertEqual(
            backend.response_schema["properties"]["source_language"]["const"],
            "English",
        )
        self.assertEqual(
            backend.response_schema["properties"]["target_language"]["const"],
            "Italian",
        )
        self.assertNotIn("ollama", repr(backend.response_schema).lower())
        self.assertNotIn("format", backend.response_schema)

    def test_facade_exposes_translation(self):
        backend = CapturingBackend(
            {
                "translated_text": "Buongiorno.",
                "source_language": "English",
                "target_language": "Italian",
            }
        )

        result = AICapabilities(backend).translate_text(
            "Good morning.",
            source_language="English",
            target_language="Italian",
        )

        self.assertEqual(result.translated_text, "Buongiorno.")

    def test_preserves_source_text_exactly_for_backend_input(self):
        source = "  First line.\n\n- item\n"
        backend = CapturingBackend(
            {
                "translated_text": "  Prima riga.\n\n- elemento\n",
                "source_language": "English",
                "target_language": "Italian",
            }
        )

        TranslateTextCapability(backend).execute(
            TranslationRequest(
                text=source,
                source_language="English",
                target_language="Italian",
            )
        )

        self.assertTrue(backend.user_prompt.endswith(source))

    def test_rejects_language_identity_drift(self):
        backend = CapturingBackend(
            {
                "translated_text": "Bonjour.",
                "source_language": "French",
                "target_language": "Italian",
            }
        )

        with self.assertRaises(AIInvalidResponseError):
            TranslateTextCapability(backend).execute(
                TranslationRequest(
                    text="Hello.",
                    source_language="English",
                    target_language="Italian",
                )
            )

    def test_rejects_empty_text_before_backend_call(self):
        backend = CapturingBackend({})

        with self.assertRaises(ValueError):
            TranslateTextCapability(backend).execute(
                TranslationRequest(
                    text="   ",
                    source_language="English",
                    target_language="Italian",
                )
            )

        self.assertIsNone(backend.response_schema)

    def test_rejects_same_source_and_target_language(self):
        backend = CapturingBackend({})

        with self.assertRaises(ValueError):
            TranslateTextCapability(backend).execute(
                TranslationRequest(
                    text="Hello.",
                    source_language="English",
                    target_language="english",
                )
            )


if __name__ == "__main__":
    unittest.main()
