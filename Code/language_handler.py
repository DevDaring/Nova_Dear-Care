#!/usr/bin/env python3
"""
language_handler.py - Multilingual support for Dear-Care on RDK S100.
Maps supported languages to AWS Polly voices and Transcribe language codes.
"""

from typing import Optional, Dict

# Supported languages with Polly Neural voice IDs and Transcribe codes.
LANGUAGES: Dict[str, Dict] = {
    "en": {
        "name": "English",
        "name_local": "English",
        "polly_voice": "Matthew",
        "polly_engine": "neural",
        "polly_lang": "en-US",
        "transcribe_lang": "en-US",
    },
    "hi": {
        "name": "Hindi",
        "name_local": "हिन्दी",
        "polly_voice": "Kajal",
        "polly_engine": "neural",
        "polly_lang": "hi-IN",
        "transcribe_lang": "hi-IN",
    },
    "fr": {
        "name": "French",
        "name_local": "Français",
        "polly_voice": "Lea",
        "polly_engine": "neural",
        "polly_lang": "fr-FR",
        "transcribe_lang": "fr-FR",
    },
    "de": {
        "name": "German",
        "name_local": "Deutsch",
        "polly_voice": "Vicki",
        "polly_engine": "neural",
        "polly_lang": "de-DE",
        "transcribe_lang": "de-DE",
    },
    "it": {
        "name": "Italian",
        "name_local": "Italiano",
        "polly_voice": "Bianca",
        "polly_engine": "neural",
        "polly_lang": "it-IT",
        "transcribe_lang": "it-IT",
    },
    "es": {
        "name": "Spanish",
        "name_local": "Español",
        "polly_voice": "Lucia",
        "polly_engine": "neural",
        "polly_lang": "es-ES",
        "transcribe_lang": "es-ES",
    },
    "pt": {
        "name": "Portuguese",
        "name_local": "Português",
        "polly_voice": "Camila",
        "polly_engine": "neural",
        "polly_lang": "pt-BR",
        "transcribe_lang": "pt-BR",
    },
}

# Current language state
_current_lang = "en"


def set_language(code: str) -> bool:
    """Set current language by ISO code. Returns True if valid."""
    global _current_lang
    if code in LANGUAGES:
        _current_lang = code
        return True
    # Try matching by name
    for k, v in LANGUAGES.items():
        if code.lower() in (v["name"].lower(), v["name_local"].lower()):
            _current_lang = k
            return True
    return False


def get_language() -> str:
    return _current_lang


def get_language_info() -> Dict:
    return LANGUAGES.get(_current_lang, LANGUAGES["en"])


def get_polly_voice() -> Optional[str]:
    info = get_language_info()
    return info.get("polly_voice")


def get_polly_lang_code() -> str:
    return get_language_info().get("polly_lang", "en-IN")


def get_transcribe_lang_code() -> Optional[str]:
    return get_language_info().get("transcribe_lang")


def detect_language_from_text(text: str) -> str:
    """Simple heuristic language detection from text keywords."""
    text_l = text.lower()
    lang_triggers = {
        "english": "en", "speak english": "en",
        "hindi": "hi", "speak hindi": "hi", "हिन्दी": "hi",
        "french": "fr", "speak french": "fr", "français": "fr",
        "german": "de", "speak german": "de", "deutsch": "de",
        "italian": "it", "speak italian": "it", "italiano": "it",
        "spanish": "es", "speak spanish": "es", "español": "es",
        "portuguese": "pt", "speak portuguese": "pt", "português": "pt",
    }
    for trigger, code in lang_triggers.items():
        if trigger in text_l:
            return code
    return _current_lang


def list_supported() -> str:
    """Return a formatted string of supported languages."""
    lines = [f"  {v['name']} ({v['name_local']})" for v in LANGUAGES.values()]
    return "\n".join(lines)
