#!/usr/bin/env python3
"""
language_handler.py - Multilingual support for Dear-Care on RDK S100.
Maps Indian languages to AWS Polly voices and Transcribe language codes.
"""

from typing import Optional, Dict

# Supported languages with Polly voice IDs and Transcribe codes
LANGUAGES: Dict[str, Dict] = {
    "en": {
        "name": "English",
        "name_local": "English",
        "polly_voice": "Kajal",
        "polly_engine": "neural",
        "polly_lang": "en-IN",
        "transcribe_lang": "en-IN",
    },
    "hi": {
        "name": "Hindi",
        "name_local": "हिन्दी",
        "polly_voice": "Kajal",
        "polly_engine": "neural",
        "polly_lang": "hi-IN",
        "transcribe_lang": "hi-IN",
    },
    "bn": {
        "name": "Bengali",
        "name_local": "বাংলা",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "bn-IN",
        "transcribe_lang": "bn-IN",
    },
    "ta": {
        "name": "Tamil",
        "name_local": "தமிழ்",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "ta-IN",
        "transcribe_lang": "ta-IN",
    },
    "te": {
        "name": "Telugu",
        "name_local": "తెలుగు",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "te-IN",
        "transcribe_lang": "te-IN",
    },
    "mr": {
        "name": "Marathi",
        "name_local": "मराठी",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "mr-IN",
        "transcribe_lang": "mr-IN",
    },
    "gu": {
        "name": "Gujarati",
        "name_local": "ગુજરાતી",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "gu-IN",
        "transcribe_lang": "gu-IN",
    },
    "kn": {
        "name": "Kannada",
        "name_local": "ಕನ್ನಡ",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "kn-IN",
        "transcribe_lang": "kn-IN",
    },
    "ml": {
        "name": "Malayalam",
        "name_local": "മലയാളം",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "ml-IN",
        "transcribe_lang": "ml-IN",
    },
    "or": {
        "name": "Odia",
        "name_local": "ଓଡ଼ିଆ",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "or-IN",
        "transcribe_lang": None,
    },
    "pa": {
        "name": "Punjabi",
        "name_local": "ਪੰਜਾਬੀ",
        "polly_voice": None,
        "polly_engine": "standard",
        "polly_lang": "pa-IN",
        "transcribe_lang": "pa-IN",
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
        "hindi": "hi", "speak hindi": "hi", "हिन्दी": "hi",
        "tamil": "ta", "speak tamil": "ta", "தமிழ்": "ta",
        "telugu": "te", "speak telugu": "te", "తెలుగు": "te",
        "bengali": "bn", "speak bengali": "bn", "বাংলা": "bn",
        "marathi": "mr", "speak marathi": "mr", "मराठी": "mr",
        "gujarati": "gu", "ગુજરાતી": "gu",
        "kannada": "kn", "ಕನ್ನಡ": "kn",
        "malayalam": "ml", "മലയാളം": "ml",
        "odia": "or", "ଓଡ଼ିଆ": "or",
        "punjabi": "pa", "ਪੰਜਾਬੀ": "pa",
        "english": "en", "speak english": "en",
    }
    for trigger, code in lang_triggers.items():
        if trigger in text_l:
            return code
    return _current_lang


def list_supported() -> str:
    """Return a formatted string of supported languages."""
    lines = [f"  {v['name']} ({v['name_local']})" for v in LANGUAGES.values()]
    return "\n".join(lines)
