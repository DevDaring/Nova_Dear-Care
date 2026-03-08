#!/usr/bin/env python3
"""
guided_flow.py - Sequential guided encounter flow for Pocket ASHA.

Flow: Language → Wake Word → Aadhaar → Patient Lookup → Health Inquiry →
      Prescription Capture Loop → Pulse Sensor → Environment Sensor →
      Final AI Analysis → Save & Wrap Up
"""

import gc
import re
import time
from typing import Optional, Tuple

from utils import get_logger, check_internet, free_memory

_log = None


def _logger():
    global _log
    if _log is None:
        _log = get_logger()
    return _log


class GuidedFlow:
    """Guided sequential encounter flow."""

    def __init__(self, voice_handler, encounter_manager, storage_manager, sync_manager,
                 use_voice: bool = True):
        self.vh = voice_handler       # voice_handler module
        self.enc = encounter_manager  # EncounterManager instance
        self.sm = storage_manager     # StorageManager instance
        self.sync = sync_manager      # SyncManager instance
        self.use_voice = use_voice
        self.aadhaar = ""
        self.symptoms = ""
        self.prescriptions = ""
        self.vitals = {}
        self.env_data = {}
        self._running = True

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def _speak(self, text: str):
        print(f"\n  Asha: {text}")
        if self.use_voice:
            try:
                self.vh.speak(text)
            except Exception as e:
                _logger().error("[GF-TTS] %s", e)

    def _listen(self, prompt: str = "", duration: int = 7) -> str:
        """Get user input via voice or text fallback."""
        import sys
        import select

        if prompt:
            print(f"\n  > {prompt}", end="", flush=True)
        else:
            print("\n  > Listening... ", end="", flush=True)

        # Check for text input first
        text_input = ""
        try:
            if select.select([sys.stdin], [], [], 0.3)[0]:
                text_input = sys.stdin.readline().strip()
        except Exception:
            pass

        if text_input:
            print(f"\n  You (text): {text_input}")
            return text_input

        if self.use_voice:
            try:
                resp = self.vh.listen(duration=duration)
                if resp:
                    print(f"\n  You: {resp}")
                return resp or ""
            except Exception as e:
                _logger().error("[GF-STT] %s", e)
        return ""

    def _confirm(self, prompt: str) -> bool:
        """Ask yes/no question. Returns True for yes."""
        self._speak(prompt)
        resp = self._listen(duration=5)
        if not resp:
            return False
        lower = resp.lower().strip()
        return any(w in lower.split() for w in ["yes", "yeah", "yep", "ok", "okay", "sure", "haan", "ji", "ha", "confirm"])

    # ------------------------------------------------------------------
    # Flow stages
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """Execute the full guided flow. Returns True if completed."""
        _logger().info("[GF] Starting guided flow")
        try:
            self._select_language()
            if not self._running:
                return False

            self._wait_for_wake()
            if not self._running:
                return False

            # Start encounter
            eid = self.enc.start()
            _logger().info("[GF] Encounter %s started", eid)

            self._collect_aadhaar()
            self._lookup_patient()
            self._health_inquiry()
            self._prescription_loop()
            self._pulse_reading()
            self._environment_reading()
            self._final_analysis()
            self._save_and_wrap()

            return True
        except KeyboardInterrupt:
            _logger().info("[GF] Interrupted by user")
            return False
        except Exception as e:
            _logger().error("[GF] Flow error: %s", e)
            self._speak("Something went wrong. Your data has been saved locally.")
            return False

    # --- Stage 1: Language Selection ---

    def _select_language(self):
        from language_handler import LANGUAGES, set_language, get_language_info

        current = get_language_info()
        lang_list = ", ".join(info["name"] for info in LANGUAGES.values())
        self._speak(f"Welcome! I currently speak {current['name']}. Available languages: {lang_list}. "
                     "Which language do you prefer? Say skip to keep current.")
        resp = self._listen(duration=7)
        if not resp or "skip" in resp.lower():
            _logger().info("[GF] Language kept: %s", current["name"])
            return

        for code, info in LANGUAGES.items():
            if info["name"].lower() in resp.lower():
                set_language(code)
                self._speak(f"Language set to {info['name']}.")
                _logger().info("[GF] Language set to %s", info["name"])
                return
        _logger().info("[GF] No language match, keeping %s", current["name"])

    # --- Stage 2: Wake Word ---

    def _wait_for_wake(self):
        self._speak("Say Hello Asha when you are ready to begin the checkup.")
        max_attempts = 30  # ~2.5 min of waiting
        for _ in range(max_attempts):
            if not self._running:
                return
            if self.use_voice:
                try:
                    detected, _ = self.vh.listen_for_wake_word()
                    if detected:
                        self._speak("Yes, I'm ready. Let's begin the patient checkup.")
                        return
                except Exception:
                    pass
            else:
                resp = self._listen("Type 'hello asha' to begin: ", duration=5)
                if resp and "asha" in resp.lower():
                    self._speak("Let's begin the patient checkup.")
                    return
        self._speak("Starting the checkup now.")

    # --- Stage 3: Collect Aadhaar ---

    def _collect_aadhaar(self):
        self._speak("Please tell me the patient's 12-digit Aadhaar number.")
        for attempt in range(3):
            resp = self._listen(duration=10)
            if not resp:
                if attempt < 2:
                    self._speak("I didn't hear that. Please say the Aadhaar number again.")
                continue

            # Try Bedrock extraction first
            aadhaar = ""
            if check_internet():
                try:
                    from aws_handler import extract_aadhaar_llm
                    aadhaar = extract_aadhaar_llm(resp)
                    if aadhaar:
                        _logger().info("[GF] Aadhaar extracted via Bedrock: %s...%s", aadhaar[:4], aadhaar[-4:])
                except Exception as e:
                    _logger().warning("[GF] Bedrock Aadhaar extraction failed: %s", e)

            # Offline fallback: regex
            if not aadhaar:
                digits = re.sub(r"\D", "", resp)
                if len(digits) == 12:
                    aadhaar = digits
                    _logger().info("[GF] Aadhaar extracted via regex: %s...%s", aadhaar[:4], aadhaar[-4:])

            if aadhaar:
                masked = aadhaar[:4] + " **** " + aadhaar[-4:]
                if self._confirm(f"I heard Aadhaar number {masked}. Is that correct?"):
                    self.aadhaar = aadhaar
                    self.enc.data["aadhaar_number"] = aadhaar
                    self._speak("Aadhaar recorded.")
                    return
                else:
                    self._speak("Let me try again.")
                    continue
            else:
                self._speak("I couldn't find a 12-digit number. Please try again.")

        self._speak("Continuing without Aadhaar number.")
        _logger().warning("[GF] Could not collect Aadhaar after 3 attempts")

    # --- Stage 4: Patient Lookup ---

    def _lookup_patient(self):
        if not self.aadhaar:
            self._collect_demographics()
            return

        existing = self.sm.find_by_aadhaar(self.aadhaar)
        if existing:
            name = existing.get("patient_name", "")
            age = existing.get("age", "")
            gender = existing.get("gender", "")
            self._speak(f"I found a previous record for {name}, age {age}.")
            if self._confirm("Is this the same patient?"):
                self.enc.set_demographics(name=name, age=age, gender=gender)
                self.enc.data["aadhaar_number"] = self.aadhaar
                _logger().info("[GF] Patient matched from previous encounter: %s", name)
                return

        self._collect_demographics()

    def _collect_demographics(self):
        self._speak("Please tell me the patient's name, age, and gender.")
        resp = self._listen(duration=10)
        if resp:
            info = self.enc.parse_demographics(resp)
            self.enc.set_demographics(
                name=info.get("name", ""),
                age=info.get("age", ""),
                gender=info.get("gender", ""),
            )
            name = info.get("name", "the patient")
            self._speak(f"Registered {name}.")
        else:
            self._speak("No demographics captured. Continuing.")

    # --- Stage 5: Health Inquiry ---

    def _health_inquiry(self):
        self._speak("What symptoms or health concerns does the patient have?")
        resp = self._listen(duration=15)
        if resp:
            self.symptoms = resp
            self.enc.data["notes"] = (self.enc.data.get("notes", "") + " Symptoms: " + resp).strip()
            self._speak("Symptoms noted.")
            _logger().info("[GF] Symptoms: %s", resp[:100])
        else:
            self._speak("No symptoms reported. Continuing.")

    # --- Stage 6: Prescription Capture Loop ---

    def _prescription_loop(self):
        self._speak("Do you have any prescriptions or medical documents to scan?")
        resp = self._listen(duration=5)
        if not resp or not any(w in resp.lower().split() for w in
                               ["yes", "yeah", "yep", "ok", "haan", "ha", "ji"]):
            self._speak("Skipping prescription capture.")
            return

        all_text = []
        photo_num = 0

        while self._running:
            self._speak("Place the document in front of the camera. Capturing now.")
            time.sleep(1)

            try:
                from camera_handler import capture_image
                img_path = capture_image()
                if not img_path:
                    self._speak("Could not capture. Check the camera connection.")
                    break

                self.enc.save_photo(img_path)
                photo_num += 1

                # OCR
                self._speak("Reading the document.")
                from ocr_handler import extract_text, unload_ocr
                text = extract_text(img_path)
                unload_ocr()
                gc.collect()

                if text:
                    all_text.append(text)
                    # Try Bedrock analysis
                    if check_internet():
                        from aws_handler import analyze_prescription
                        analysis = analyze_prescription(text)
                        if analysis:
                            self._speak(analysis)
                        else:
                            self._speak(f"I read: {text[:200]}")
                    else:
                        self._speak(f"I read: {text[:200]}")
                else:
                    self._speak("No text found. Try with a clearer picture.")

                free_memory()

            except Exception as e:
                _logger().error("[GF] Prescription capture error: %s", e)
                self._speak("Error during capture.")

            if not self._confirm("Do you have another document to scan?"):
                break

        self.prescriptions = "\n---\n".join(all_text)
        _logger().info("[GF] Captured %d prescriptions", photo_num)

    # --- Stage 7: Pulse Oximeter Reading ---

    def _pulse_reading(self):
        self._speak("Now let's measure the patient's pulse and oxygen level. "
                     "Please attach the pulse oximeter to the patient's finger.")

        if not self._confirm("Is the sensor attached? Say yes when ready."):
            self._speak("Skipping pulse measurement.")
            return

        self._speak("Measuring now. Please hold still for 15 seconds.")
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            readings = sh.read_vitals(duration=15)

            spo2 = readings.get("spo2")
            hr = readings.get("heart_rate")

            if spo2 is not None or hr is not None:
                self.vitals["spo2"] = spo2
                self.vitals["heart_rate"] = hr
                self.enc.set_vitals(spo2=spo2, heart_rate=hr)

                report_parts = []
                if spo2 is not None:
                    report_parts.append(f"Oxygen level: {spo2:.0f}%")
                if hr is not None:
                    report_parts.append(f"Heart rate: {hr:.0f} beats per minute")
                self._speak(". ".join(report_parts) + ".")
                _logger().info("[GF] Vitals — SpO2: %s, HR: %s", spo2, hr)
            else:
                self._speak("Could not get a reading. Check sensor placement and try again.")
        except Exception as e:
            _logger().error("[GF] Pulse reading error: %s", e)
            self._speak("Error reading pulse sensor.")

    # --- Stage 8: Environment Sensor (BMP280) ---

    def _environment_reading(self):
        self._speak("Reading environmental conditions.")
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            readings = sh.read_all()

            temp = readings.get("temperature")
            pressure = readings.get("pressure")

            if temp is not None:
                self.env_data["temperature"] = temp
                self.vitals["temperature"] = temp
                self.enc.set_vitals(temperature=temp)

            if pressure is not None:
                self.env_data["pressure"] = pressure

            parts = []
            if temp is not None:
                parts.append(f"Temperature: {temp:.1f} degrees Celsius")
            if pressure is not None:
                parts.append(f"Pressure: {pressure:.0f} hectopascals")

            if parts:
                self._speak(". ".join(parts) + ".")
                _logger().info("[GF] Environment — Temp: %s, Pressure: %s", temp, pressure)
            else:
                self._speak("No environmental readings available.")
        except Exception as e:
            _logger().error("[GF] Environment reading error: %s", e)
            self._speak("Could not read environmental sensor.")

    # --- Stage 9: Final AI Analysis ---

    def _final_analysis(self):
        # Run on-device triage first
        try:
            triage_result = self.enc.run_triage(symptoms=self.symptoms)
            self._speak(f"On-device assessment: {triage_result.summary()}")
        except Exception as e:
            _logger().warning("[GF] On-device triage error: %s", e)

        # Bedrock consolidated analysis
        if check_internet():
            try:
                from aws_handler import analyze_health_summary
                summary = analyze_health_summary(
                    symptoms=self.symptoms,
                    prescriptions=self.prescriptions,
                    vitals=self.vitals,
                    env_data=self.env_data,
                )
                if summary:
                    self._speak("AI health summary: " + summary)
                    self.enc.data["notes"] = (
                        self.enc.data.get("notes", "") + " AI Summary: " + summary[:300]
                    ).strip()
                    _logger().info("[GF] Bedrock health summary generated")
                    return
            except Exception as e:
                _logger().warning("[GF] Bedrock analysis error: %s", e)

        self._speak("AI analysis unavailable offline. Data saved for later review.")

    # --- Stage 10: Save & Wrap Up ---

    def _save_and_wrap(self):
        summary = self.enc.end()
        if not summary:
            self._speak("Error saving encounter.")
            return

        patient = summary.get("patient_name", "the patient")
        triage = summary.get("triage_level", "")
        msg = f"Encounter complete for {patient}."
        if triage:
            msg += f" Triage level: {triage}."

        # Try immediate sync
        if check_internet():
            self._speak(msg + " Syncing data now.")
            result = self.sync.sync_now()
            if result.get("synced", 0) > 0:
                self._speak("Data synced to the cloud successfully.")
                # Trigger Lambda for clinical notes + health summary
                try:
                    from aws_handler import invoke_lambda
                    eid = summary.get("encounter_id", "")
                    for action in ["generate_notes", "health_summary"]:
                        resp = invoke_lambda({"encounter_id": eid, "action": action})
                        if resp and resp.get("statusCode") == 200:
                            _logger().info("[GF] Lambda %s completed for %s", action, eid)
                        else:
                            _logger().warning("[GF] Lambda %s failed for %s", action, eid)
                except Exception as e:
                    _logger().warning("[GF] Lambda invocation error: %s", e)
            else:
                self._speak("Sync pending. Data saved locally and will sync later.")
        else:
            self._speak(msg + " Data saved locally. It will sync when internet is available.")

        _logger().info("[GF] Encounter complete: %s", summary.get("encounter_id", ""))
        free_memory()

    def stop(self):
        """Signal the flow to stop."""
        self._running = False
