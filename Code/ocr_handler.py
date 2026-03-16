#!/usr/bin/env python3
"""
ocr_handler.py - PaddleOCR (offline) + Amazon Textract (online) for Dear-Care.

PaddleOCR is lazy-loaded and explicitly unloaded to conserve RAM.
Run with: env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 ...
"""

import os
import gc
from typing import Optional, List, Tuple

from utils import get_logger, check_internet, free_memory

_ocr_instance = None
_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


# ============================================================
# PaddleOCR — offline
# ============================================================

def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        _logger().info("[OCR] Loading PaddleOCR…")
        os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"
        from paddleocr import PaddleOCR
        from config import OCR_LANG, OCR_USE_ANGLE_CLS
        _ocr_instance = PaddleOCR(use_angle_cls=OCR_USE_ANGLE_CLS, lang=OCR_LANG,
                                   show_log=False, use_gpu=False)
        _logger().info("[OCR] PaddleOCR loaded")
    return _ocr_instance


def unload_ocr():
    """Free PaddleOCR from memory."""
    global _ocr_instance
    if _ocr_instance is not None:
        _ocr_instance = None
        gc.collect()
        _logger().info("[OCR] PaddleOCR unloaded")


def _paddle_extract(image_path: str) -> str:
    ocr = _get_ocr()
    result = ocr.ocr(image_path, cls=False)
    lines = []
    if result and result[0]:
        for line in result[0]:
            if line and len(line) >= 2:
                txt = line[1]
                if isinstance(txt, tuple):
                    lines.append(txt[0])
    return "\n".join(lines)


# ============================================================
# Amazon Textract — online
# ============================================================

def _textract_extract(image_path: str) -> str:
    try:
        import boto3
        from config import AWS_REGION
        client = boto3.client("textract", region_name=AWS_REGION)
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        resp = client.detect_document_text(Document={"Bytes": img_bytes})
        lines = [b["Text"] for b in resp.get("Blocks", []) if b["BlockType"] == "LINE"]
        text = "\n".join(lines)
        _logger().info("[OCR] Textract extracted %d lines", len(lines))
        return text
    except Exception as e:
        _logger().warning("[OCR] Textract error: %s", e)
        return ""


# ============================================================
# Public API
# ============================================================

def extract_text(image_path: str, prefer_online: bool = True) -> str:
    """
    Extract text from image. Tries Textract if online, falls back to PaddleOCR.
    Always returns a string (empty on failure).
    """
    if not os.path.exists(image_path):
        _logger().warning("[OCR] Image not found: %s", image_path)
        return ""

    if prefer_online and check_internet():
        text = _textract_extract(image_path)
        if text:
            _logger().info("[OCR] PRIMARY: AWS Textract — %d chars extracted", len(text))
            return text
        _logger().info("[OCR] Textract returned empty, falling back to PaddleOCR")

    try:
        text = _paddle_extract(image_path)
        if text:
            reason = "offline" if not check_internet() else "Textract failed"
            _logger().info("[OCR] FALLBACK: PaddleOCR (reason: %s) — %d chars extracted", reason, len(text))
        return text
    except Exception as e:
        _logger().error("[OCR] PaddleOCR error: %s", e)
        return ""
    finally:
        free_memory()


def extract_text_with_details(image_path: str) -> List[Tuple[str, float, list]]:
    """Extract text with confidence and bounding boxes (PaddleOCR only)."""
    if not os.path.exists(image_path):
        return []
    try:
        ocr = _get_ocr()
        result = ocr.ocr(image_path, cls=False)
        details = []
        if result and result[0]:
            for line in result[0]:
                if line and len(line) >= 2:
                    box = line[0]
                    txt = line[1]
                    if isinstance(txt, tuple) and len(txt) >= 2:
                        details.append((txt[0], txt[1], box))
        return details
    except Exception as e:
        _logger().error("[OCR] Detail extraction error: %s", e)
        return []
