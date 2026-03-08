#!/usr/bin/env python3
"""
intent_handler.py - Intent classification for Pocket ASHA.
Primary: AWS Bedrock LLM classification. Fallback: keyword matching.
"""

from enum import Enum, auto
from typing import Tuple

from config import (
    CAPTURE_KEYWORDS, VITALS_KEYWORDS, RECORD_AUDIO_KEYWORDS,
    CONFIRM_KEYWORDS, DENY_KEYWORDS, HEALTH_KEYWORDS, EXIT_KEYWORDS,
    ENCOUNTER_KEYWORDS, SYNC_KEYWORDS, LANGUAGE_KEYWORDS, HELP_KEYWORDS,
)
from utils import get_logger

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


class Intent(Enum):
    START_ENCOUNTER = auto()
    CAPTURE_IMAGE = auto()
    MEASURE_VITALS = auto()
    RECORD_AUDIO = auto()
    CONFIRM = auto()
    DENY = auto()
    HEALTH_QUESTION = auto()
    SET_LANGUAGE = auto()
    SYNC_DATA = auto()
    HELP = auto()
    EXIT = auto()
    GREETING = auto()
    THANKS = auto()
    UNKNOWN = auto()


# keyword → intent mapping (order matters: first match wins)
_KEYWORD_MAP = [
    (ENCOUNTER_KEYWORDS, Intent.START_ENCOUNTER),
    (CAPTURE_KEYWORDS, Intent.CAPTURE_IMAGE),
    (VITALS_KEYWORDS, Intent.MEASURE_VITALS),
    (RECORD_AUDIO_KEYWORDS, Intent.RECORD_AUDIO),
    (CONFIRM_KEYWORDS, Intent.CONFIRM),
    (DENY_KEYWORDS, Intent.DENY),
    (HEALTH_KEYWORDS, Intent.HEALTH_QUESTION),
    (LANGUAGE_KEYWORDS, Intent.SET_LANGUAGE),
    (SYNC_KEYWORDS, Intent.SYNC_DATA),
    (HELP_KEYWORDS, Intent.HELP),
    (EXIT_KEYWORDS, Intent.EXIT),
]

_INTENT_NAME_MAP = {e.name: e for e in Intent}


def _classify_bedrock(text: str) -> Tuple[Intent, float]:
    """Try LLM-based classification via Bedrock."""
    try:
        from aws_handler import classify_intent_llm
        result = classify_intent_llm(text)
        if not result:
            return Intent.UNKNOWN, 0.0
        intent_name = result.get("intent", "UNKNOWN").upper()
        confidence = min(max(float(result.get("confidence", 0.0)), 0.0), 1.0)
        intent = _INTENT_NAME_MAP.get(intent_name, Intent.UNKNOWN)
        _logger().info("[INTENT] Bedrock classified: %s (%.0f%%)", intent.value, confidence * 100)
        return intent, confidence
    except Exception as e:
        _logger().warning("[INTENT] Bedrock classification failed: %s", e)
        return Intent.UNKNOWN, 0.0


def _classify_keywords(text: str) -> Tuple[Intent, float]:
    """Keyword-based fallback classification."""
    text_l = text.lower().strip()
    words = text_l.split()

    best_intent = Intent.UNKNOWN
    best_score = 0.0

    for keywords, intent in _KEYWORD_MAP:
        matches = 0
        for kw in keywords:
            if len(kw) <= 3:
                if kw in words:
                    matches += 1
            else:
                if kw in text_l:
                    matches += 1
        if matches > 0:
            score = min(0.5 + matches * 0.15, 0.98)
            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 0.65:
        return best_intent, best_score

    # Thanks
    if any(w in words for w in ["thanks", "thank", "dhanyavaad", "shukriya"]):
        return Intent.THANKS, 0.85

    # Greeting
    if any(w in words for w in ["hello", "hi", "namaste"]) or \
       any(g in text_l for g in ["good morning", "good afternoon", "good evening"]):
        return Intent.GREETING, 0.85

    if best_score > 0:
        return best_intent, best_score

    return Intent.UNKNOWN, 0.0


def classify(text: str) -> Tuple[Intent, float]:
    """
    Classify user intent from text.
    Primary: keyword matching (instant). Fallback: Bedrock LLM (for unknowns).
    Returns (Intent, confidence 0-1).
    """
    if not text:
        return Intent.UNKNOWN, 0.0

    # Try keywords first (instant, no API call)
    intent, confidence = _classify_keywords(text)
    if intent != Intent.UNKNOWN and confidence >= 0.65:
        _logger().info("[INTENT] METHOD: Keyword match")
        return intent, confidence

    # Fallback to Bedrock for ambiguous/unknown input
    print("  [Understanding...]", flush=True)
    intent, confidence = _classify_bedrock(text)
    if intent != Intent.UNKNOWN and confidence >= 0.6:
        _logger().info("[INTENT] METHOD: Bedrock LLM")
        return intent, confidence

    # Return keyword result even if low confidence, or UNKNOWN
    if intent == Intent.UNKNOWN:
        intent, confidence = _classify_keywords(text)
    _logger().info("[INTENT] METHOD: Keyword fallback (low confidence)")
    return intent, confidence
