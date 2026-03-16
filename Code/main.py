#!/usr/bin/env python3
"""
main.py - Entry point for Dear-Care Healthcare Assistant.

Target Platform: RDK S100 (Ubuntu 22.04, ARM64)
Hackathon: Amazon Nova Devpost | Voice AI Track

HOW TO RUN:
============================================================
Run Dear-Care:
    cd ~/Documents/dear-care/Code
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py

Text-only mode (no mic/speaker):
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
============================================================
"""

import os
import sys
import gc
import json
import time
import signal
import argparse
from typing import Tuple, Optional

# ============================================================
# Globals
# ============================================================
_running = True


def _signal_handler(sig, frame):
    global _running
    print("\n[KAMAL] Shutting down...")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ============================================================
# DEAR-CARE
# ============================================================

class DearCare:
    """Main Dear-Care healthcare assistant."""

    def __init__(self, use_voice: bool = True):
        from utils import setup_logging, free_memory, get_logger
        setup_logging()
        self.log = get_logger()
        self.use_voice = use_voice

        print("=" * 60)
        print("   DEAR-CARE — AI Health Assistant")
        print("   Powered by Amazon Nova Lite")
        print("   Amazon Nova Hackathon | DevDaring")
        print("=" * 60)
        print(f"  Persona  : Kamal")
        print(f"  Platform : RDK S100 (ARM64)")
        print(f"  LLM      : Amazon Nova Lite (Reasoning)")
        print(f"  TTS      : Amazon Polly Neural")
        print(f"  STT      : Amazon Transcribe Streaming")
        print(f"  Mode     : {'Voice Enabled' if use_voice else 'Text-only'}")
        print("=" * 60)

        # State
        self.state = "idle"
        self.pending_action = None
        self.last_ocr_text = None
        self.vitals_data = {}
        self.env_data = {}
        self.prescriptions = ""

        # Encounter manager
        from encounter_manager import EncounterManager
        self.encounter = EncounterManager()

        # Sync manager
        from sync_manager import SyncManager
        self.sync = SyncManager()

        # Hardware checks
        self._check_hardware()

        # Start background sync
        self.sync.start()

        free_memory()
        from utils import cleanup_temp
        cleanup_temp()
        print("[INIT] Dear-Care ready")
        print("-" * 60)

    # ------------------------------------------------------------------
    # Hardware
    # ------------------------------------------------------------------

    def _check_hardware(self):
        """Detect available hardware."""
        # Audio
        try:
            from voice_handler import check_audio_devices
            devs = check_audio_devices()
            if devs.get("mic"):
                print("[INIT] Microphone: Ready")
            else:
                print("[INIT] Microphone: Not found")
            if devs.get("speaker"):
                print(f"[INIT] Speaker: Ready")
            else:
                print("[INIT] Speaker: Not found")
        except Exception as e:
            print(f"[INIT] Audio check: {e}")

        # Camera
        try:
            from camera_handler import check_camera_available
            if check_camera_available():
                print("[INIT] Camera: MIPI available")
            else:
                print("[INIT] Camera: Not detected (check MIPI cable)")
        except Exception:
            print("[INIT] Camera: Check skipped")

        # Sensors
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            avail = sh.detect_sensors()
            for name, ok in avail.items():
                status = "connected" if ok else "not connected"
                print(f"[INIT] Sensor {name}: {status}")
        except Exception:
            print("[INIT] Sensors: Not available")

        # AWS
        from utils import check_internet
        if check_internet():
            print("[INIT] Network: Online")
        else:
            print("[INIT] Network: Offline (will work locally)")

    # ------------------------------------------------------------------
    # Voice I/O
    # ------------------------------------------------------------------

    def _beep(self):
        """Play a short beep sound."""
        try:
            from voice_handler import _play_beep
            _play_beep()
        except Exception:
            pass

    def speak(self, text: str):
        """Output text via speaker and console."""
        print(f"\n  Kamal: {text}")
        if self.use_voice:
            try:
                from voice_handler import speak
                speak(text)
            except Exception as e:
                self.log.error("[TTS] %s", e)

    def listen_for_wake(self) -> Tuple[bool, str]:
        """Listen for wake word. Returns (detected, command)."""
        if not self.use_voice:
            return False, ""
        try:
            from voice_handler import listen_for_wake_word
            return listen_for_wake_word()
        except Exception as e:
            self.log.error("[LISTEN] %s", e)
            return False, ""

    def listen_response(self, duration: int = 7) -> str:
        """Listen without wake word (for follow-up)."""
        if not self.use_voice:
            return ""
        try:
            from voice_handler import listen
            return listen(duration=duration)
        except Exception as e:
            self.log.error("[LISTEN] %s", e)
            return ""

    def get_input(self, require_wake: bool = True) -> str:
        """Get input via voice or text. Text always takes priority."""
        import select
        import threading

        prompt = "Say 'Hello Kamal' + command, or type: " if require_wake else "Listening (or type): "
        print(f"\n  > {prompt}", end="", flush=True)

        # Quick non-blocking stdin check
        text_input = ""
        def _read():
            nonlocal text_input
            try:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    text_input = sys.stdin.readline().strip()
            except Exception:
                pass

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=0.5)

        if text_input:
            print(f"\n  You (text): {text_input}")
            return text_input

        # Voice
        if self.use_voice:
            if require_wake:
                detected, cmd = self.listen_for_wake()
                if detected and cmd:
                    print(f"  You: {cmd}")
                    return cmd
                elif detected:
                    self.speak("Yes, I'm listening.")
                    resp = self.listen_response(duration=10)
                    if resp:
                        print(f"  You: {resp}")
                        return resp
                    # If still nothing, try once more
                    self.speak("I didn't catch that. Please say your command.")
                    resp = self.listen_response(duration=10)
                    if resp:
                        print(f"  You: {resp}")
                        return resp
                return ""
            else:
                resp = self.listen_response()
                if resp:
                    print(f"  You: {resp}")
                return resp or ""
        return ""

    # ------------------------------------------------------------------
    # Command processing
    # ------------------------------------------------------------------

    def process_command(self, command: str) -> Tuple[str, bool]:
        """Process command. Returns (response, needs_followup)."""
        from intent_handler import classify, Intent

        intent, confidence = classify(command)
        self.log.info("[INTENT] %s (%.0f%%) for: %s", intent.value, confidence * 100, command[:50])

        # EXIT
        if intent == Intent.EXIT:
            self.state = "exit"
            from config import FAREWELL_MESSAGE
            return FAREWELL_MESSAGE, False

        # START ENCOUNTER
        if intent == Intent.START_ENCOUNTER:
            return self._start_encounter()

        # CAPTURE IMAGE
        if intent == Intent.CAPTURE_IMAGE:
            return self._capture_and_analyze()

        # MEASURE VITALS
        if intent == Intent.MEASURE_VITALS:
            return self._measure_vitals()

        # RECORD AUDIO
        if intent == Intent.RECORD_AUDIO:
            return self._record_audio()

        # CONFIRM
        if intent == Intent.CONFIRM:
            if self.pending_action:
                return self._handle_confirmation()
            if self.encounter.active and self.encounter.state.value == "review":
                return self._end_encounter()
            return "Nothing to confirm right now.", False

        # DENY
        if intent == Intent.DENY:
            if self.pending_action:
                self.pending_action = None
                self.state = "idle"
                return "Cancelled.", False
            if self.encounter.active:
                return "Encounter still active. Say exit encounter to cancel.", False
            return "Nothing to cancel.", False

        # SYNC
        if intent == Intent.SYNC_DATA:
            return self._sync_data()

        # SET LANGUAGE
        if intent == Intent.SET_LANGUAGE:
            return self._set_language(command)

        # HELP
        if intent == Intent.HELP:
            return self._help_text(), False

        # GREETING
        if intent == Intent.GREETING:
            from config import GREETING_MESSAGE
            return GREETING_MESSAGE, False

        # THANKS
        if intent == Intent.THANKS:
            return "You're welcome! Say Hello Kamal when you need me.", False

        # HEALTH QUESTION — use Bedrock
        if intent == Intent.HEALTH_QUESTION:
            return self._health_question(command)

        # UNKNOWN — try Bedrock
        return self._general_question(command)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start_encounter(self) -> Tuple[str, bool]:
        if self.encounter.active:
            return "An encounter is already in progress. Say end encounter to finish it first.", False
        eid = self.encounter.start()
        from config import ENCOUNTER_START
        return f"Encounter {eid} started. {ENCOUNTER_START}", True

    def _end_encounter(self) -> Tuple[str, bool]:
        summary = self.encounter.end()
        if not summary:
            return "No active encounter.", False
        voice = f"Encounter saved. Patient {summary.get('patient_name', 'unknown')}. "
        triage = summary.get("triage_level")
        if triage:
            voice += f"Triage: {triage}. "
        voice += "Data will sync when online."
        return voice, False

    def _measure_pulse(self):
        """Measure pulse and SpO2 with voice prompts and beeps."""
        self.speak("Now let's measure your pulse and oxygen level. "
                   "Please place your finger on the pulse sensor.")
        self._beep()
        time.sleep(3)

        self.speak("Measuring now. Please hold still for 15 seconds.")
        sh = None
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            sh.max30102.connect()
            readings = sh.read_vitals(duration=15)

            if not readings:
                self._beep()
                self.speak("Could not get a reading. Check sensor placement.")
                return

            spo2 = readings.get("spo2")
            hr = readings.get("heart_rate")
            self._beep()  # measurement complete

            if spo2 is not None or hr is not None:
                self.vitals_data["spo2"] = spo2
                self.vitals_data["heart_rate"] = hr
                if self.encounter.active:
                    self.encounter.set_vitals(spo2=spo2, heart_rate=hr)

                parts = []
                if spo2 is not None:
                    parts.append(f"Oxygen level: {spo2:.0f} percent")
                if hr is not None:
                    parts.append(f"Heart rate: {hr:.0f} beats per minute")
                self.speak(". ".join(parts) + ".")
            else:
                self._beep()
                self.speak("Could not get a reading. Check sensor placement.")
        except Exception as e:
            self.log.error("[PULSE] %s", e)
            self.speak("Error reading pulse sensor.")
        finally:
            if sh:
                try:
                    sh.close()
                except Exception:
                    pass

    def _measure_environment(self):
        """Measure temperature and pressure automatically with beeps."""
        self.speak("Now reading environmental conditions.")
        self._beep()
        time.sleep(2)
        sh = None
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            sh.bme280.connect()
            readings = sh.read_environment()

            if not readings:
                self._beep()
                self.speak("No environmental readings available.")
                return

            temp = readings.get("temperature")
            pressure = readings.get("pressure")

            if temp is not None:
                self.env_data["temperature"] = temp
                self.vitals_data["temperature"] = temp
                if self.encounter.active:
                    self.encounter.set_vitals(temperature=temp)

            if pressure is not None:
                self.env_data["pressure"] = pressure

            self._beep()  # measurement complete

            parts = []
            if temp is not None:
                parts.append(f"Temperature: {temp:.1f} degrees Celsius")
            if pressure is not None:
                parts.append(f"Pressure: {pressure:.0f} hectopascals")
            if parts:
                self.speak(". ".join(parts) + ".")
            else:
                self.speak("No environmental readings available.")
        except Exception as e:
            self.log.error("[ENV] %s", e)
            self.speak("Could not read environmental sensor.")
        finally:
            if sh:
                try:
                    sh.close()
                except Exception:
                    pass

    def _measure_vitals(self) -> Tuple[str, bool]:
        self.speak("Measuring vitals now. Please wait.")
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            sh.detect_sensors()
            readings = sh.read_all()
            sh.close()

            if not readings:
                return "No sensors detected. Please connect the pulse oximeter or thermometer.", False

            spo2 = readings.get("spo2")
            hr = readings.get("heart_rate")
            temp = readings.get("temperature")

            # Store in encounter if active
            if self.encounter.active:
                self.encounter.set_vitals(spo2=spo2, heart_rate=hr, temperature=temp)

            # Format report
            from triage_engine import format_vitals_report
            report = format_vitals_report(spo2, hr, temp, readings.get("humidity"))

            # Auto-triage if encounter active
            if self.encounter.active:
                result = self.encounter.run_triage()
                report += f" Assessment: {result.summary()}"

            return report, False
        except Exception as e:
            self.log.error("[VITALS] %s", e)
            return "Error reading vitals. Please check sensor connections.", False

    def _capture_prescription(self):
        """Capture prescription image with voice prompts and beeps."""
        self.speak("Please place your prescription or medical document in front of the camera.")
        self._beep()
        time.sleep(3)  # give user time to position document

        try:
            from camera_handler import capture_image
            img_path = capture_image()
            self._beep()  # capture complete

            if not img_path:
                self.speak("Could not capture image. Check the camera connection.")
                return

            # Save to encounter
            if self.encounter.active:
                self.encounter.save_photo(img_path)

            # OCR
            self.speak("Image captured. Reading the document now.")
            from ocr_handler import extract_text, unload_ocr
            text = extract_text(img_path)
            unload_ocr()
            gc.collect()

            self.last_ocr_text = text
            if not text:
                self.speak("No text found in the image. Try with a clearer picture.")
                return

            self.prescriptions = text

            # Analyze with Bedrock
            from utils import check_internet
            if check_internet():
                from aws_handler import analyze_prescription
                analysis = analyze_prescription(text)
                if analysis:
                    self.speak(analysis)
                    if self.encounter.active:
                        self.encounter.data["notes"] = (
                            self.encounter.data.get("notes", "") + " Prescription: " + analysis[:300]
                        ).strip()
                    return

            self.speak(f"I read the following from the document: {text[:300]}")
        except Exception as e:
            self.log.error("[CAPTURE] %s", e)
            self.speak("Error during capture. Please try again.")

    def _capture_and_analyze(self) -> Tuple[str, bool]:
        self._capture_prescription()
        return "", False

    def _record_audio(self) -> Tuple[str, bool]:
        self.speak("Recording now. Please speak or cough.")
        try:
            from voice_handler import record_audio
            from config import TEMP_DIR
            path = str(TEMP_DIR / "symptom_recording.wav")
            record_audio(output_path=path, duration=10)

            if self.encounter.active:
                self.encounter.save_audio(path)
                return "Audio recorded and saved to the encounter.", False
            return "Audio recorded.", False
        except Exception as e:
            self.log.error("[AUDIO] %s", e)
            return "Error recording audio.", False

    def _handle_confirmation(self) -> Tuple[str, bool]:
        action = self.pending_action
        self.pending_action = None
        self.state = "idle"
        if action == "capture":
            return self._capture_and_analyze()
        return "Done.", False

    def _sync_data(self) -> Tuple[str, bool]:
        self.speak("Syncing data now.")
        result = self.sync.sync_now()
        if not result["online"]:
            return f"No internet connection. {result['pending']} encounters pending.", False
        return (
            f"Sync complete. {result['synced']} uploaded, "
            f"{result['failed']} failed, {result['pending']} still pending."
        ), False

    def _set_language(self, command: str) -> Tuple[str, bool]:
        from language_handler import set_language, LANGUAGES
        lower = command.lower()
        for code, info in LANGUAGES.items():
            if info["name"].lower() in lower:
                set_language(code)
                return f"Language set to {info['name']}.", False
        return "Which language? I support: " + ", ".join(
            info["name"] for info in LANGUAGES.values()
        ), True

    def _health_question(self, command: str) -> Tuple[str, bool]:
        from utils import check_internet
        if check_internet():
            from aws_handler import chat
            resp = chat(command)
            if resp:
                return resp, False
        return "I'm offline right now and can't answer health questions. Please try when internet is available.", False

    def _general_question(self, command: str) -> Tuple[str, bool]:
        from utils import check_internet
        if check_internet():
            from aws_handler import chat
            resp = chat(command)
            if resp:
                return resp, False
        return "I didn't understand that. Say help for a list of commands.", False

    def _help_text(self) -> str:
        return (
            "I can help with: "
            "Start a patient encounter. "
            "Take a picture of a prescription. "
            "Measure vital signs. "
            "Record cough or symptoms. "
            "Answer health questions. "
            "Sync data to the cloud. "
            "Change language. "
            "Say Hello Kamal followed by your command."
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Aadhaar Collection
    # ------------------------------------------------------------------

    def _collect_aadhaar(self) -> str:
        """Ask for Aadhaar number. Returns 12-digit string or empty."""
        import re
        self.speak("Please tell me the patient's 12 digit Aadhaar number.")

        for attempt in range(3):
            resp = self.listen_response(duration=15)
            if not resp:
                if attempt < 2:
                    self.speak("I didn't hear that. Please say the Aadhaar number again.")
                continue

            # Try Bedrock extraction first
            aadhaar = ""
            from utils import check_internet
            if check_internet():
                try:
                    from aws_handler import extract_aadhaar_llm
                    aadhaar = extract_aadhaar_llm(resp)
                except Exception as e:
                    self.log.warning("[AADHAAR] Bedrock extraction failed: %s", e)

            # Regex fallback
            if not aadhaar:
                digits = re.sub(r"\D", "", resp)
                if len(digits) == 12:
                    aadhaar = digits

            if aadhaar:
                masked = aadhaar[:4] + " **** " + aadhaar[-4:]
                self.speak(f"I heard Aadhaar number {masked}. Is that correct?")
                confirm = self.listen_response(duration=5)
                if confirm and any(w in confirm.lower() for w in
                                   ["yes", "yeah", "haan", "ha", "ji", "ok", "correct", "right"]):
                    return aadhaar
                else:
                    self.speak("Let me try again.")
                    continue
            else:
                self.speak("I couldn't find a 12 digit number. Please try again.")

        self.speak("Continuing without Aadhaar number.")
        return ""

    def _lookup_patient(self, aadhaar: str) -> Optional[dict]:
        """Look up patient by Aadhaar in local database. Returns patient record or None."""
        if not aadhaar:
            return None
        from storage_manager import StorageManager
        sm = StorageManager()
        return sm.find_by_aadhaar(aadhaar)

    # ------------------------------------------------------------------
    # Health Consultation (Transcribe STT → Nova Lite → Polly TTS)
    # ------------------------------------------------------------------

    def _health_consultation(self):
        """Run an interactive health consultation.
        Records user's voice via Transcribe STT, reasons via Nova Lite, speaks via Polly TTS."""
        self.speak("Starting health consultation. Please speak your health concern after the beep. "
                   "Say stop or goodbye when you are done.")

        consultation_notes = []
        # Build context from the collected data
        context_parts = []
        if self.encounter.data.get("patient_name"):
            context_parts.append(f"Patient: {self.encounter.data['patient_name']}")
        if self.vitals_data.get("spo2"):
            context_parts.append(f"SpO2: {self.vitals_data['spo2']}%")
        if self.vitals_data.get("heart_rate"):
            context_parts.append(f"Heart Rate: {self.vitals_data['heart_rate']} bpm")
        if self.vitals_data.get("temperature"):
            context_parts.append(f"Temperature: {self.vitals_data['temperature']}°C")
        if self.prescriptions:
            context_parts.append(f"Prescription: {self.prescriptions[:200]}")
        patient_context = ". ".join(context_parts) if context_parts else "No prior data collected."

        for turn in range(10):  # max 10 turns of conversation
            self._beep()
            # Record user's speech via Transcribe STT
            resp = self.listen_response(duration=15)
            if not resp:
                self.speak("I didn't hear anything. Would you like to continue the consultation?")
                confirm = self.listen_response(duration=5)
                if not confirm or any(w in confirm.lower() for w in ["no", "nahi", "stop", "bye", "goodbye"]):
                    break
                continue

            # Check for stop words
            lower = resp.lower()
            if any(w in lower for w in ["stop", "bye", "goodbye", "that's all", "thank you", "done"]):
                break

            consultation_notes.append(f"Patient: {resp}")

            # Reason via Nova Lite, speak via Polly TTS
            prompt = (f"Patient context: {patient_context}\n"
                      f"Patient says: {resp}\n"
                      f"Respond as Kamal, a caring healthcare assistant. "
                      f"Give brief, helpful medical guidance in 2-3 sentences.")
            try:
                from aws_handler import chat
                text_resp = chat(prompt)
                if text_resp:
                    self.speak(text_resp)
                    consultation_notes.append(f"Kamal: {text_resp}")
                else:
                    self.speak("I'm having trouble connecting. Please try again.")
            except Exception as e:
                self.log.error("[CONSULT] %s", e)
                self.speak("Error during consultation.")

        self._beep()
        self.speak("Consultation ended.")

        # Save consultation notes to encounter
        if consultation_notes and self.encounter.active:
            notes_text = " | ".join(consultation_notes)
            self.encounter.data["notes"] = (
                self.encounter.data.get("notes", "") + " Consultation: " + notes_text[:500]
            ).strip()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Sequential healthcare flow: Aadhaar → patient lookup → prescription → 
        pulse → environment → analysis → upload → Lambda → consultation."""
        global _running
        from utils import free_memory, check_internet

        # Language selection at startup
        self._ask_language()

        self.speak("Namaste! I am Kamal, your healthcare assistant. "
                   "I will guide you through the checkup step by step.")

        while _running:
            try:
                # Reset state for each patient
                self.vitals_data = {}
                self.env_data = {}
                self.prescriptions = ""
                self.last_ocr_text = None
                self.aadhaar = ""

                # Start encounter
                from encounter_manager import EncounterManager
                self.encounter = EncounterManager()
                eid = self.encounter.start()
                self.log.info("[MAIN] Encounter %s started", eid)

                # --- Step 1: Collect Aadhaar ---
                self.aadhaar = self._collect_aadhaar()
                if self.aadhaar:
                    self.encounter.data["aadhaar_number"] = self.aadhaar

                    # Look up patient in database
                    existing = self._lookup_patient(self.aadhaar)
                    if existing and existing.get("patient_name"):
                        name = existing["patient_name"]
                        age = existing.get("age", "")
                        gender = existing.get("gender", "")
                        self.encounter.set_demographics(name=name, age=age, gender=gender)

                        gender_text = "Male" if gender == "M" else "Female" if gender == "F" else gender
                        self.speak(f"Welcome back, {name}! "
                                   f"I found your records. Name: {name}, "
                                   f"Age: {age}, Gender: {gender_text}.")
                    else:
                        # New patient — ask for name
                        self.speak("Aadhaar recorded. Please tell me the patient's name.")
                        name_resp = self.listen_response(duration=8)
                        if name_resp:
                            import re
                            name_words = [w for w in name_resp.split()
                                          if re.sub(r'[^a-zA-Z]', '', w)]
                            patient_name = " ".join(name_words[:3]).strip()
                            if patient_name:
                                self.encounter.set_demographics(name=patient_name)
                                self.speak(f"Registered {patient_name}.")

                if not _running:
                    break

                # --- Step 2: Prescription Capture ---
                self.speak("Do you have any prescriptions or medical documents to scan?")
                resp = self.listen_response(duration=5)
                if resp and any(w in resp.lower() for w in ["yes", "yeah", "haan", "ha", "ji", "ok"]):
                    self._capture_prescription()
                    free_memory()

                    # Ask for more prescriptions
                    while _running:
                        self.speak("Do you have another prescription to scan?")
                        resp = self.listen_response(duration=5)
                        if resp and any(w in resp.lower() for w in ["yes", "yeah", "haan", "ha", "ji", "ok"]):
                            self._capture_prescription()
                            free_memory()
                        else:
                            break
                else:
                    self.speak("Skipping prescription capture.")

                if not _running:
                    break

                # --- Step 3: Pulse / SpO2 ---
                self._measure_pulse()
                free_memory()
                if not _running:
                    break

                # --- Step 4: Environment (automatic) ---
                self._measure_environment()
                free_memory()
                if not _running:
                    break

                # --- Step 5: Save & Upload to AWS Lambda ---
                lambda_output = self._save_and_upload()

                # --- Step 6: Speak Lambda output if available ---
                if lambda_output:
                    self.speak("Here is the report from the cloud. " + lambda_output)

                free_memory()

                # --- Step 7: Ask for consultation ---
                self.speak("Would you like a health consultation?")
                resp = self.listen_response(duration=5)
                if resp and any(w in resp.lower() for w in
                               ["yes", "yeah", "haan", "ha", "ji", "ok", "consultation", "consult"]):
                    self._health_consultation()
                    # Re-save encounter with consultation notes
                    if self.encounter.active:
                        from storage_manager import StorageManager
                        sm = StorageManager()
                        sm.update_encounter(eid, **{k: v for k, v in self.encounter.data.items()
                                                    if k != 'encounter_id'})

                free_memory()

                # Ask for another patient
                self.speak("Would you like to check another patient?")
                resp = self.listen_response(duration=5)
                if not resp or not any(w in resp.lower() for w in ["yes", "yeah", "haan", "ha", "ji", "ok"]):
                    break

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.error("[MAIN] %s", e)
                self.speak("Something went wrong. Your data has been saved locally.")
                break

        self._shutdown()

    def _save_and_upload(self) -> str:
        """Save encounter, upload to AWS Lambda, return Lambda output."""
        from utils import check_internet
        lambda_output = ""

        # End encounter (saves to CSV)
        summary = self.encounter.end()
        if not summary:
            self.speak("Error saving encounter data.")
            return ""

        patient = summary.get("patient_name", "the patient")
        self.speak(f"Encounter complete for {patient}. Uploading data to the cloud.")

        # Upload to cloud
        if check_internet():
            try:
                result = self.sync.sync_now()
                if result.get("synced", 0) > 0:
                    self.speak("Data uploaded successfully. Processing in the cloud now.")

                    # Trigger Lambda for processing
                    try:
                        from aws_handler import invoke_lambda
                        eid = summary.get("encounter_id", "")

                        # Build payload with all collected data
                        payload = {
                            "encounter_id": eid,
                            "action": "process_encounter",
                            "patient_name": summary.get("patient_name", ""),
                            "aadhaar_number": summary.get("aadhaar_number", ""),
                            "age": summary.get("age", ""),
                            "gender": summary.get("gender", ""),
                            "spo2": summary.get("spo2", ""),
                            "heart_rate": summary.get("heart_rate", ""),
                            "temperature": summary.get("temperature", ""),
                            "prescriptions": self.prescriptions[:1000] if self.prescriptions else "",
                            "notes": summary.get("notes", ""),
                            "env_pressure": str(self.env_data.get("pressure", "")),
                        }
                        resp = invoke_lambda(payload)
                        if resp:
                            status = resp.get("statusCode", 0)
                            if status == 200:
                                body = resp.get("body", "")
                                if isinstance(body, str):
                                    try:
                                        body_data = json.loads(body)
                                        lambda_output = body_data.get("summary", body_data.get("message", body))
                                    except (json.JSONDecodeError, ValueError):
                                        lambda_output = body
                                elif isinstance(body, dict):
                                    lambda_output = body.get("summary", body.get("message", str(body)))
                                else:
                                    lambda_output = str(body) if body else ""
                                self.log.info("[MAIN] Lambda processed encounter %s", eid)
                            else:
                                self.log.warning("[MAIN] Lambda returned status %s for %s", status, eid)
                        else:
                            self.log.warning("[MAIN] Lambda returned None for %s", eid)

                        # Also trigger clinical notes generation
                        for action in ["generate_notes", "health_summary"]:
                            try:
                                invoke_lambda({"encounter_id": eid, "action": action})
                            except Exception:
                                pass

                    except Exception as e:
                        self.log.warning("[MAIN] Lambda invocation error: %s", e)

                    # Notify Fit-U mobile app with Lambda results
                    if lambda_output:
                        try:
                            from fitu_client import FituClient
                            fitu = FituClient()
                            if fitu.is_available():
                                worker_id = summary.get("worker_id", "")
                                fitu.notify_fitu_verdict_ready(
                                    worker_id=worker_id,
                                    encounter_id=eid,
                                    triage_level=summary.get("triage_level", "ROUTINE"),
                                    summary=lambda_output
                                )
                                self.log.info("[MAIN] Lambda result sent to mobile app")
                        except Exception as e:
                            self.log.warning("[MAIN] Fit-U notification error: %s", e)

                else:
                    self.speak("Upload pending. Data saved locally.")
            except Exception as e:
                self.log.error("[UPLOAD] %s", e)
                self.speak("Upload failed. Data saved locally.")
        else:
            self.speak("No internet. Data saved locally and will upload when online.")

        return lambda_output

    def _shutdown(self):
        """Clean shutdown."""
        print("\n[KAMAL] Shutting down...")
        self.sync.stop()
        if self.encounter.active:
            self.encounter.end()
        from utils import free_memory
        free_memory()
        from aws_handler import clear_chat
        clear_chat()
        print("[KAMAL] Goodbye!")

    def _ask_language(self):
        """Ask user to select language at startup."""
        from language_handler import LANGUAGES, set_language
        # Show top languages with numbers
        top_langs = [("en", "English"), ("hi", "Hindi"), ("bn", "Bengali"),
                     ("ta", "Tamil"), ("te", "Telugu"), ("mr", "Marathi")]
        print("\n  Please choose your language:")
        for i, (code, name) in enumerate(top_langs, 1):
            print(f"    {i}. {name}")
        print(f"    0. More languages")

        self.speak("Please choose your language. Say English, Hindi, Bengali, Tamil, Telugu, or Marathi.")
        resp = ""
        if self.use_voice:
            resp = self.listen_response(duration=7)
        if not resp:
            # Text fallback
            try:
                import select
                print("\n  > Enter language (or press Enter for English): ", end="", flush=True)
                if select.select([sys.stdin], [], [], 10)[0]:
                    resp = sys.stdin.readline().strip()
            except Exception:
                pass

        if resp:
            resp_l = resp.lower().strip()
            # Check for number input
            if resp_l in ("1", "2", "3", "4", "5", "6") and int(resp_l) <= len(top_langs):
                code, name = top_langs[int(resp_l) - 1]
                set_language(code)
                self.speak(f"Language set to {name}.")
                return
            # Check by name
            for code, info in LANGUAGES.items():
                if info["name"].lower() in resp_l or info.get("name_local", "") in resp:
                    set_language(code)
                    self.speak(f"Language set to {info['name']}.")
                    return

        # Default to English
        set_language("en")
        print("  [Using English]")


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Dear-Care Healthcare Assistant")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no microphone/speaker)")
    parser.add_argument("--guided", action="store_true", help="Run guided encounter flow")
    args = parser.parse_args()

    if args.guided:
        # Guided sequential flow
        from utils import setup_logging, get_logger
        setup_logging()
        log = get_logger()
        use_voice = not args.text

        print("=" * 60)
        print("   DEAR-CARE — Guided Encounter Flow")
        print("   Amazon Nova Hackathon | DevDaring")
        print("=" * 60)

        import voice_handler
        from encounter_manager import EncounterManager
        from storage_manager import StorageManager
        from sync_manager import SyncManager
        from guided_flow import GuidedFlow

        # Hardware diagnostics
        try:
            from voice_handler import check_audio_devices
            devs = check_audio_devices()
            print(f"  Mic: {'Ready' if devs.get('mic') else 'Not found'}")
            print(f"  Speaker: {'Ready' if devs.get('speaker') else 'Not found'}")
        except Exception:
            pass
        try:
            from sensor_handler import SensorHandler
            _sh = SensorHandler()
            _avail = _sh.detect_sensors()
            for _name, _ok in _avail.items():
                print(f"  Sensor {_name}: {'connected' if _ok else 'not connected'}")
            _sh.close()
        except Exception:
            pass
        from utils import check_internet
        print(f"  Network: {'Online' if check_internet() else 'Offline'}")
        print("=" * 60)

        enc = EncounterManager()
        sm = StorageManager()
        sync = SyncManager()
        sync.start()

        flow = GuidedFlow(voice_handler, enc, sm, sync, use_voice=use_voice)

        try:
            while _running:
                flow.run()
                # Ask if another encounter
                print("\n  > Start another encounter? (yes/no): ", end="", flush=True)
                import sys
                try:
                    ans = sys.stdin.readline().strip().lower()
                except Exception:
                    ans = ""
                if ans not in ("yes", "y", "haan", "ha"):
                    break
                enc = EncounterManager()
                flow = GuidedFlow(voice_handler, enc, sm, sync, use_voice=use_voice)
        except KeyboardInterrupt:
            pass
        finally:
            sync.stop()
            print("[KAMAL] Goodbye!")
    else:
        app = DearCare(use_voice=not args.text)
        app.run()


if __name__ == "__main__":
    main()
