#!/usr/bin/env python3
"""
guided_flow.py - Sequential guided encounter flow for Dear-Care.

Flow: Language → Wake Word → Aadhaar → Patient Lookup → Health Inquiry →
      Prescription Capture Loop → Pulse Sensor → Environment Sensor →
      Final AI Analysis → Save & Wrap Up
"""

import gc
import re
import time
from typing import Optional, Tuple

from utils import get_logger, check_internet, free_memory, cleanup_temp

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
        self._prescriptions_done = False
        self.fitu_data = {}  # Fit-U companion app data

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def _speak(self, text: str):
        try:
            print(f"\n  Kamal: {text}")
        except BrokenPipeError:
            pass
        if self.use_voice:
            try:
                self.vh.speak(text)
            except Exception as e:
                _logger().error("[GF-TTS] %s", e)

    def _listen(self, prompt: str = "", duration: int = 7) -> str:
        """Get user input via voice or text fallback.
        User can type on terminal and press Enter, or speak after the beep."""
        import sys
        import select

        if prompt:
            try:
                print(f"\n  > {prompt} (or type & press Enter)", end="", flush=True)
            except BrokenPipeError:
                pass
        else:
            try:
                print("\n  > Listening... (or type & press Enter)", end="", flush=True)
            except BrokenPipeError:
                pass

        # Check for text input — wait up to 3 seconds for typing
        text_input = ""
        try:
            if select.select([sys.stdin], [], [], 3.0)[0]:
                text_input = sys.stdin.readline().strip()
        except Exception:
            pass

        if text_input:
            try:
                print(f"\n  You (text): {text_input}")
            except BrokenPipeError:
                pass
            return text_input

        if self.use_voice:
            try:
                resp = self.vh.listen(duration=duration)
                if resp:
                    try:
                        print(f"\n  You: {resp}")
                    except BrokenPipeError:
                        pass
                return resp or ""
            except Exception as e:
                try:
                    _logger().error("[GF-STT] %s", e)
                except Exception:
                    pass
        return ""

    def _confirm(self, prompt: str) -> bool:
        """Ask yes/no question. Returns True for yes."""
        self._speak(prompt)
        resp = self._listen(duration=5)
        if not resp:
            return False
        lower = resp.lower().strip()
        # Strip punctuation from each word before matching
        words = [re.sub(r'[^\w]', '', w) for w in lower.split() if re.sub(r'[^\w]', '', w)]
        # Check for affirmative words
        if any(w in words for w in ["yes", "yeah", "yep", "ok", "okay", "sure",
                                     "haan", "ji", "ha", "confirm", "correct",
                                     "right", "absolutely", "affirmative"]):
            return True
        # Check for affirmative phrases
        if any(p in lower for p in ["that is correct", "that's correct", "that's right",
                                     "that is right", "is correct", "sounds right",
                                     "sounds correct", "go ahead"]):
            return True
        # Explicit denial
        if any(w in words for w in ["no", "nope", "nah", "nahi", "na", "wrong", "galat"]):
            return False
        # Default: if no denial words found and response is non-empty, treat as yes
        return True

    # ------------------------------------------------------------------
    # Flow stages
    # ------------------------------------------------------------------

    def run(self) -> bool:
        """Execute the full guided flow. Returns True if completed."""
        _logger().info("[GF] Starting guided flow")
        cleanup_temp()
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
            self.enc.advance_from_demographics()

            self._health_inquiry()

            if not self._prescriptions_done:
                self._prescription_loop()
            self.enc.advance_from_photo()

            self._pulse_reading()
            self._environment_reading()
            self.enc.advance_from_vitals()

            # Fetch Fit-U companion app data before final analysis
            self._fetch_fitu_data()

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
        self._speak("Say Hello Kamal when you are ready to begin the checkup.")
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
                resp = self._listen("Type 'hello kamal' to begin: ", duration=5)
                if resp and ("kamal" in resp.lower() or "dear care" in resp.lower() or "dear-care" in resp.lower()):
                    self._speak("Let's begin the patient checkup.")
                    return
        self._speak("Starting the checkup now.")

    # --- Stage 3: Collect Aadhaar ---

    def _collect_aadhaar(self):
        self._speak("Please tell me the patient's 12-digit Aadhaar number. "
                     "Say all 12 digits clearly, without pausing.")
        for attempt in range(3):
            resp = self._listen(duration=15)
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

            # If we got some digits but not 12, try SpeechRecognition for a second opinion
            # on the SAME audio file (don't re-record)
            if not aadhaar:
                digits_found = re.sub(r"\D", "", resp)
                if len(digits_found) >= 4:
                    _logger().info("[GF] Got %d digits ('%s'), trying SpeechRecognition for second opinion",
                                   len(digits_found), digits_found)
                    try:
                        from voice_handler import _try_speech_recognition
                        from config import TEMP_AUDIO_INPUT
                        text2, _ = _try_speech_recognition(str(TEMP_AUDIO_INPUT))
                        if text2:
                            digits2 = re.sub(r"\D", "", text2)
                            if len(digits2) == 12:
                                aadhaar = digits2
                                _logger().info("[GF] Aadhaar from SpeechRecognition fallback: %s...%s",
                                               aadhaar[:4], aadhaar[-4:])
                            elif check_internet():
                                aadhaar2 = ""
                                try:
                                    from aws_handler import extract_aadhaar_llm
                                    aadhaar2 = extract_aadhaar_llm(text2)
                                except Exception:
                                    pass
                                if aadhaar2:
                                    aadhaar = aadhaar2
                                    _logger().info("[GF] Aadhaar from SpeechRecognition+Bedrock: %s...%s",
                                                   aadhaar[:4], aadhaar[-4:])
                    except Exception as e:
                        _logger().warning("[GF] SpeechRecognition second opinion failed: %s", e)

            if aadhaar:
                masked = aadhaar[:4] + " **** " + aadhaar[-4:]
                if self._confirm(f"I heard Aadhaar number {masked}. Is that correct?"):
                    self.aadhaar = aadhaar
                    self.enc.data["aadhaar_number"] = aadhaar

                    # Check if patient already exists in database
                    existing = self.sm.find_by_aadhaar(aadhaar)
                    if existing and existing.get("patient_name"):
                        name = existing["patient_name"]
                        age = existing.get("age", "")
                        gender = existing.get("gender", "")
                        self.enc.set_demographics(name=name, age=age, gender=gender)
                        self.enc.data["aadhaar_number"] = aadhaar
                        details = f"Name: {name}"
                        if age:
                            details += f", Age: {age}"
                        if gender:
                            details += f", Gender: {'Male' if gender == 'M' else 'Female' if gender == 'F' else gender}"
                        self._speak(f"Welcome back, {name}! I found your records. {details}.")
                        _logger().info("[GF] Returning patient matched: %s", name)
                        return

                    # New patient — ask for name
                    self._speak("Aadhaar recorded. Please tell me the patient's name.")
                    name_resp = self._listen(duration=8)
                    if name_resp:
                        import re as _re
                        name_words = [w for w in name_resp.split()
                                      if _re.sub(r'[^a-zA-Z]', '', w)]
                        patient_name = " ".join(name_words[:3]).strip()
                        if patient_name:
                            self.enc.data["patient_name"] = patient_name
                            self._speak(f"Thank you. Registered {patient_name} with Aadhaar {masked}.")
                            _logger().info("[GF] Name '%s' stored with Aadhaar", patient_name)
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

        # If patient was already matched during Aadhaar collection, skip redundant lookup
        if self.enc.data.get("patient_name"):
            _logger().info("[GF] Patient already identified during Aadhaar collection, skipping lookup")
            return

        existing = self.sm.find_by_aadhaar(self.aadhaar)
        if existing:
            name = existing.get("patient_name", "")
            age = existing.get("age", "")
            gender = existing.get("gender", "")
            if name:
                self._speak(f"Welcome back, {name}! I found your previous records.")
                self.enc.set_demographics(name=name, age=age, gender=gender)
                self.enc.data["aadhaar_number"] = self.aadhaar
                _logger().info("[GF] Returning patient auto-matched: %s", name)
                return

        self._collect_demographics()

    def _collect_demographics(self):
        # Ask name
        self._speak("Please tell me the patient's name.")
        name_resp = self._listen(duration=8)
        patient_name = ""
        if name_resp:
            import re as _re
            name_words = [w for w in name_resp.split()
                          if _re.sub(r'[^a-zA-Z]', '', w) and w.lower() not in
                          {"years", "year", "old", "male", "female", "patient", "name", "age", "gender", "my", "is", "i", "am"}]
            patient_name = " ".join(name_words[:3]).strip()

        # Ask age
        self._speak("What is the patient's age?")
        age_resp = self._listen(duration=5)
        age = ""
        if age_resp:
            age_match = re.search(r'(\d{1,3})', age_resp)
            if age_match:
                age = age_match.group(1)

        # Ask gender
        self._speak("What is the patient's gender? Male or female?")
        gender_resp = self._listen(duration=5)
        gender = ""
        if gender_resp:
            lower = gender_resp.lower()
            if any(w in lower for w in ["female", "woman", "girl", "mahila", "lady", "aurat"]):
                gender = "F"
            elif any(w in lower for w in ["male", "man", "boy", "aadmi"]):
                gender = "M"

        self.enc.set_demographics(name=patient_name, age=age, gender=gender)
        if patient_name:
            self._speak(f"Registered {patient_name}, age {age or 'unknown'}, gender {gender or 'unknown'}.")
        else:
            self._speak("Demographics saved.")

    def _collect_demographics_remaining(self):
        """Collect age and gender when name was already captured with Aadhaar."""
        name = self.enc.data.get("patient_name", "")
        self._speak(f"I have the name {name}. Please tell me the patient's age and gender.")
        resp = self._listen(duration=8)
        if resp:
            info = self.enc.parse_demographics(resp)
            self.enc.set_demographics(
                name=name,
                age=info.get("age", ""),
                gender=info.get("gender", ""),
            )
            self._speak(f"Details updated for {name}.")
        else:
            self._speak(f"Continuing with {name}.")

    # --- Stage 5: Health Inquiry ---

    def _health_inquiry(self):
        self._speak("What symptoms or health concerns does the patient have? Please describe in detail.")
        resp = self._listen(duration=15)
        if resp:
            # Check if the user is asking for prescription capture instead of reporting symptoms
            lower = resp.lower()
            prescription_words = ["prescription", "snap", "capture", "photo", "picture",
                                  "camera", "scan", "document", "look at", "take", "image"]
            if any(w in lower for w in prescription_words):
                self._speak("It sounds like you want to capture a prescription. Let me do that.")
                _logger().info("[GF] Health inquiry redirected to prescription capture")
                self._prescription_loop_direct()
                self._prescriptions_done = True
                return

            # If symptoms are too short/incomplete, ask to elaborate
            word_count = len(resp.split())
            if word_count < 5:
                _logger().info("[GF] Symptoms too short (%d words: '%s'), asking to elaborate", word_count, resp)
                self._speak(f"I heard: {resp}. Can you tell me more about your symptoms?")
                resp2 = self._listen(duration=15)
                if resp2 and len(resp2.split()) > 2:
                    resp = resp + ". " + resp2
                    _logger().info("[GF] Symptoms extended: %s", resp[:150])

            self.symptoms = resp
            self.enc.data["notes"] = (self.enc.data.get("notes", "") + " Symptoms: " + resp).strip()
            self._speak("Symptoms noted.")
            _logger().info("[GF] Symptoms: %s", resp[:100])
        else:
            self._speak("No symptoms reported. Continuing.")

    # --- Stage 6: Prescription Capture Loop ---

    def _beep(self):
        """Play a beep sound to signal upcoming capture/measurement."""
        from voice_handler import _play_beep
        _play_beep()

    def _prescription_loop_direct(self):
        """Directly start prescription capture (skip the 'do you have prescriptions?' question)."""
        all_text = []
        photo_num = 0

        while self._running:
            self._speak("Place the document in front of the camera.")
            self._beep()
            time.sleep(3)

            try:
                from camera_handler import capture_image
                img_path = capture_image()
                self._beep()  # signal capture complete
                if not img_path:
                    self._speak("Could not capture. Check the camera connection.")
                    break

                self.enc.save_photo(img_path)
                photo_num += 1

                self._speak("Reading the document.")
                from ocr_handler import extract_text, unload_ocr
                text = extract_text(img_path)
                unload_ocr()
                gc.collect()

                if text:
                    all_text.append(text)
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
        _logger().info("[GF] Captured %d prescriptions (direct)", photo_num)

    def _prescription_loop(self):
        self._speak("Do you have any prescriptions or medical documents to scan?")
        resp = self._listen(duration=5)
        words = [re.sub(r'[^\w]', '', w) for w in (resp or "").lower().split() if re.sub(r'[^\w]', '', w)]
        if not resp or not any(w in words for w in
                               ["yes", "yeah", "yep", "ok", "haan", "ha", "ji"]):
            self._speak("Skipping prescription capture.")
            return

        all_text = []
        photo_num = 0

        while self._running:
            self._speak("Place the document in front of the camera.")
            self._beep()
            time.sleep(3)

            try:
                from camera_handler import capture_image
                img_path = capture_image()
                self._beep()  # signal capture complete
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
        self._beep()
        time.sleep(3)

        self._speak("Measuring now. Please hold still for 15 seconds.")
        sh = None
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            sh.max30102.connect()
            readings = sh.read_vitals(duration=15)

            if not readings:
                self._beep()
                self._speak("Could not get a reading. Check sensor placement and try again.")
                return

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
                self._beep()  # signal measurement complete
                self._speak(". ".join(report_parts) + ".")
                _logger().info("[GF] Vitals — SpO2: %s, HR: %s", spo2, hr)
            else:
                self._beep()
                self._speak("Could not get a reading. Check sensor placement and try again.")
        except Exception as e:
            _logger().error("[GF] Pulse reading error: %s", e)
            self._speak("Error reading pulse sensor.")
        finally:
            if sh:
                try:
                    sh.close()
                except Exception:
                    pass

    # --- Stage 8: Environment Sensor (BMP280) ---

    def _environment_reading(self):
        self._speak("Reading environmental conditions.")
        self._beep()
        time.sleep(3)
        sh = None
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            sh.bme280.connect()
            readings = sh.read_environment()

            if not readings:
                self._beep()
                self._speak("No environmental readings available.")
                return

            temp = readings.get("temperature")
            pressure = readings.get("pressure")

            if temp is not None:
                self.env_data["temperature"] = temp
                self.vitals["temperature"] = temp
                self.enc.set_vitals(temperature=temp)

            if pressure is not None:
                self.env_data["pressure"] = pressure

            self._beep()  # signal measurement complete

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
        finally:
            if sh:
                try:
                    sh.close()
                except Exception:
                    pass

    # --- Stage 9: Final AI Analysis ---

    def _fetch_fitu_data(self):
        """Fetch Fit-U companion app health data before analysis."""
        try:
            # Get worker ID - you may want to store this earlier in the flow
            # For now, use a default or get from encounter data
            worker_id = self.enc.data.get("worker_id", "DC_WK_001")
            self.fitu_data = self.enc.fetch_fitu_data(worker_id)
            if self.fitu_data:
                _logger().info("[GF] Fit-U data loaded for analysis")
            else:
                _logger().info("[GF] No Fit-U data available - proceeding without mobility context")
        except Exception as e:
            _logger().warning("[GF] Fit-U data fetch failed: %s", e)
            self.fitu_data = {}

    def _final_analysis(self):
        # Run on-device triage (always runs, even offline)
        triage_summary = ""
        try:
            triage_result = self.enc.run_triage(symptoms=self.symptoms)
            triage_summary = triage_result.summary()
            _logger().info("[GF] On-device triage: %s", triage_summary)
        except Exception as e:
            _logger().warning("[GF] On-device triage error: %s", e)

        # Build historical context from previous encounters
        history_text = "No previous visits found."
        try:
            if self.aadhaar:
                past = self.sm.find_all_by_aadhaar(self.aadhaar)
                # Exclude the current encounter
                current_eid = self.enc.data.get("encounter_id", "")
                past = [r for r in past if r.get("encounter_id") != current_eid]
                if past:
                    parts = []
                    for r in past[-3:]:  # last 3 encounters max
                        ts = r.get("timestamp", "unknown date")
                        notes = r.get("notes", "")
                        vitals_str = ""
                        if r.get("spo2"): vitals_str += f"SpO2:{r['spo2']}% "
                        if r.get("heart_rate"): vitals_str += f"HR:{r['heart_rate']} "
                        if r.get("temperature"): vitals_str += f"Temp:{r['temperature']}°C "
                        triage = r.get("triage_level", "")
                        parts.append(f"  - {ts}: {vitals_str.strip()} Triage:{triage} Notes:{notes[:100]}")
                    history_text = "\n".join(parts)
                    _logger().info("[GF] Found %d historical encounters for analysis", len(past))
        except Exception as e:
            _logger().warning("[GF] Historical lookup error: %s", e)

        # Bedrock consolidated analysis (includes triage + history + Fit-U data)
        if check_internet():
            try:
                from aws_handler import analyze_health_summary
                summary = analyze_health_summary(
                    symptoms=self.symptoms,
                    prescriptions=self.prescriptions,
                    vitals=self.vitals,
                    env_data=self.env_data,
                    triage=triage_summary,
                    history=history_text,
                    fitu_data=self.fitu_data,
                )
                if summary:
                    self._speak("Health summary: " + summary)
                    self.enc.data["notes"] = (
                        self.enc.data.get("notes", "") + " AI Summary: " + summary[:300]
                    ).strip()
                    # Store AI summary for Fit-U notification
                    self.enc.data["ai_summary"] = summary[:500]
                    _logger().info("[GF] Bedrock health summary generated")
                    return
            except Exception as e:
                _logger().warning("[GF] Bedrock analysis error: %s", e)

        # Fallback: speak on-device triage only when Bedrock is unavailable
        if triage_summary:
            self._speak(f"On-device assessment: {triage_summary}")
        else:
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
                # Confirm what was uploaded
                updated_parts = []
                if int(summary.get("photo_count", 0)) > 0:
                    updated_parts.append("prescriptions")
                if summary.get("spo2") or summary.get("heart_rate"):
                    updated_parts.append("pulse and oxygen readings")
                if summary.get("temperature"):
                    updated_parts.append("temperature")
                if summary.get("notes"):
                    updated_parts.append("health notes")

                if updated_parts:
                    items = ", ".join(updated_parts)
                    self._speak(f"Data synced successfully. {patient}'s {items} have been updated in the database.")
                else:
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
