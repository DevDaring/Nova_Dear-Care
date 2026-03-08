#!/usr/bin/env python3
"""
storage_manager.py - Local CSV database and media storage for Pocket ASHA
"""

import os
import csv
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from config import (
    ENCOUNTERS_CSV, ENCOUNTER_DIR, CSV_HEADERS,
    DATA_RETENTION_DAYS, MAX_OFFLINE_ENCOUNTERS,
)
from utils import get_logger, get_timestamp


class StorageManager:
    """Manages local CSV database and per-encounter media folders."""

    def __init__(self):
        self.log = get_logger()
        ENCOUNTER_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_csv()

    # ---- CSV helpers ----

    def _ensure_csv(self):
        if not ENCOUNTERS_CSV.exists():
            with open(ENCOUNTERS_CSV, "w", newline="") as f:
                csv.writer(f).writerow(CSV_HEADERS)

    def _read_all(self) -> List[Dict]:
        self._ensure_csv()
        with open(ENCOUNTERS_CSV, "r", newline="") as f:
            return list(csv.DictReader(f))

    def _write_all(self, rows: List[Dict]):
        with open(ENCOUNTERS_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_HEADERS)
            w.writeheader()
            w.writerows(rows)

    # ---- Encounter CRUD ----

    def create_encounter(self, encounter_id: str, **kwargs) -> Dict:
        """Create a new encounter row and its media folders."""
        row = {h: "" for h in CSV_HEADERS}
        row["encounter_id"] = encounter_id
        row["timestamp"] = get_timestamp()
        row["sync_status"] = "pending"
        row["photo_count"] = "0"
        row["audio_count"] = "0"
        row.update({k: str(v) for k, v in kwargs.items() if k in CSV_HEADERS})

        # media dirs
        enc_dir = ENCOUNTER_DIR / encounter_id
        (enc_dir / "photos").mkdir(parents=True, exist_ok=True)
        (enc_dir / "audio").mkdir(parents=True, exist_ok=True)

        with open(ENCOUNTERS_CSV, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_HEADERS).writerow(row)

        self.log.info(f"[STORAGE] Created encounter {encounter_id}")
        return row

    def update_encounter(self, encounter_id: str, **kwargs):
        """Update fields for an existing encounter."""
        rows = self._read_all()
        for r in rows:
            if r["encounter_id"] == encounter_id:
                r.update({k: str(v) for k, v in kwargs.items() if k in CSV_HEADERS})
                break
        self._write_all(rows)

    def get_encounter(self, encounter_id: str) -> Optional[Dict]:
        for r in self._read_all():
            if r["encounter_id"] == encounter_id:
                return r
        return None

    def get_pending_encounters(self) -> List[Dict]:
        return [r for r in self._read_all() if r.get("sync_status") == "pending"]

    def get_all_encounters(self) -> List[Dict]:
        return self._read_all()

    # ---- Media paths ----

    def get_photo_path(self, encounter_id: str, name: str = None) -> str:
        if name is None:
            name = f"photo_{datetime.now().strftime('%H%M%S')}.jpg"
        return str(ENCOUNTER_DIR / encounter_id / "photos" / name)

    def get_audio_path(self, encounter_id: str, name: str = None) -> str:
        if name is None:
            name = f"audio_{datetime.now().strftime('%H%M%S')}.wav"
        return str(ENCOUNTER_DIR / encounter_id / "audio" / name)

    def increment_photo_count(self, encounter_id: str):
        rows = self._read_all()
        for r in rows:
            if r["encounter_id"] == encounter_id:
                r["photo_count"] = str(int(r.get("photo_count", 0)) + 1)
                break
        self._write_all(rows)

    def increment_audio_count(self, encounter_id: str):
        rows = self._read_all()
        for r in rows:
            if r["encounter_id"] == encounter_id:
                r["audio_count"] = str(int(r.get("audio_count", 0)) + 1)
                break
        self._write_all(rows)

    # ---- Maintenance ----

    def pending_count(self) -> int:
        return len(self.get_pending_encounters())

    def total_count(self) -> int:
        return len(self._read_all())

    def is_capacity_warning(self) -> bool:
        return self.pending_count() >= MAX_OFFLINE_ENCOUNTERS

    def cleanup_old_records(self):
        """Delete encounters older than DATA_RETENTION_DAYS."""
        cutoff = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)
        rows = self._read_all()
        keep = []
        removed = 0
        for r in rows:
            try:
                ts = datetime.fromisoformat(r.get("timestamp", ""))
                if ts < cutoff and r.get("sync_status") == "synced":
                    enc_dir = ENCOUNTER_DIR / r["encounter_id"]
                    if enc_dir.exists():
                        shutil.rmtree(enc_dir)
                    removed += 1
                    continue
            except (ValueError, TypeError):
                pass
            keep.append(r)
        if removed:
            self._write_all(keep)
            self.log.info(f"[STORAGE] Cleaned up {removed} old encounters")

    def get_encounter_folder(self, encounter_id: str) -> Path:
        return ENCOUNTER_DIR / encounter_id

    def find_by_aadhaar(self, aadhaar_number: str) -> Optional[Dict]:
        """Find an encounter by Aadhaar number. Returns latest match or None."""
        if not aadhaar_number:
            return None
        matches = [r for r in self._read_all() if r.get("aadhaar_number") == aadhaar_number]
        return matches[-1] if matches else None

    def find_all_by_aadhaar(self, aadhaar_number: str) -> List[Dict]:
        """Find ALL encounters for an Aadhaar number, ordered oldest→newest."""
        if not aadhaar_number:
            return []
        return [r for r in self._read_all() if r.get("aadhaar_number") == aadhaar_number]
