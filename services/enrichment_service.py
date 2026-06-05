"""Enrichment service: translation + text-to-speech for CAP alerts.

OpenAI handles both translation (gpt-4o-mini, batched JSON output) and TTS
(tts-1) for every language. Without OPENAI_API_KEY the service falls back to
mock strings + mock audio URLs so the pipeline still completes — the
graceful-degradation invariant the rest of services/ uses too.

Note: a previous Khaya (Ghana NLP) TTS integration was removed because the
ghananlp.org public API was withdrawn. The OpenAI per-language voice mapping
below is the v2 fallback for African-language audio; native voices are a
follow-up phase if/when an alternative provider lands.
"""
from __future__ import annotations

import json
import logging
import os
import uuid

from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# OpenAI tts-1 voice per language. African-language voices are approximated
# using `onyx` (the deepest, most neutral preset) since OpenAI doesn't ship a
# native Twi/Hausa/Ga/Ewe voice. English uses `alloy`.
_OPENAI_VOICE_PER_LANG = {
    "English": "alloy",
    "Twi": "onyx",
    "Hausa": "onyx",
    "Ga": "onyx",
    "Ewe": "onyx",
}


class EnrichmentService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
        self._audio_dir = os.path.join("static", "audio")
        os.makedirs(self._audio_dir, exist_ok=True)

    def translate_text(self, text: str, languages=("Twi", "Hausa")) -> dict:
        """Batched translation: ONE OpenAI call returns a JSON dict with the
        source plus all requested language variants. Mocks when no API key."""
        translations = {"English": text}

        if not self.openai_client:
            logger.warning("OpenAI not configured — using mock translations.")
            for lang in languages:
                translations[lang] = f"[{lang} Translation Mock]: {text}"
            return translations

        target_keys = ", ".join(f'"{lang}"' for lang in languages)
        system = (
            "You are a professional translator for Ghanaian languages. "
            "Translate the user's emergency alert text into each target language. "
            f"Reply with a single JSON object whose keys are exactly: {target_keys}. "
            "Each value is the translation as a plain string. No commentary, no extra keys."
        )
        try:
            resp = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
            )
            payload = json.loads(resp.choices[0].message.content)
            for lang in languages:
                value = payload.get(lang)
                translations[lang] = value if isinstance(value, str) and value.strip() else f"Translation Error: {text}"
        except Exception as e:
            logger.error("Batched translation failed: %s", e)
            for lang in languages:
                translations[lang] = f"Translation Error: {text}"

        return translations

    def text_to_speech(self, text: str, language: str = "English") -> str:
        """Generate audio for ``text`` in ``language`` and return the public
        URL under /static/audio/. OpenAI tts-1 for all languages; mock URL
        when OpenAI isn't configured."""
        if not text:
            return f"/static/audio/mock_{language.lower()}.mp3"

        if self.openai_client:
            try:
                voice = _OPENAI_VOICE_PER_LANG.get(language, "alloy")
                resp = self.openai_client.audio.speech.create(
                    model="tts-1", voice=voice, input=text,
                )
                filename = f"alert_{uuid.uuid4().hex}_{language.lower()}.mp3"
                filepath = os.path.join(self._audio_dir, filename)
                resp.stream_to_file(filepath)
                logger.info("OpenAI TTS produced %s for language=%s.", filename, language)
                return f"/static/audio/{filename}"
            except Exception as e:
                logger.error("OpenAI TTS failed for language=%s: %s", language, e)

        logger.warning("TTS for %s falling back to mock URL.", language)
        return f"/static/audio/mock_{language.lower()}.mp3"


enrichment_service = EnrichmentService()
