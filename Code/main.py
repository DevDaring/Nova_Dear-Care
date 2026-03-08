#!/usr/bin/env python3
"""
main.py - Entry point for Pocket ASHA Healthcare Assistant.

Target Platform: RDK S100 (Ubuntu 22.04, ARM64)

HOW TO RUN:
============================================================
Run Pocket ASHA:
    cd ~/Documents/AI_4_Bharat/Code
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py

Text-only mode (no mic/speaker):
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 main.py --text
============================================================
"""

import os
import sys
import gc
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
    print("\n[ASHA] Shutting down...")
    _running = False


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ============================================================
# POCKET ASHA
# ============================================================

class PocketAsha:
    """Main Pocket ASHA healthcare assistant."""

    def __init__(self, use_voice: bool = True):
        from utils import setup_logging, free_memory, get_logger
        setup_logging()
        self.log = get_logger()
        self.use_voice = use_voice

        print("=" * 60)
        print("  POCKET ASHA - Healthcare Assistant")
        print("=" * 60)
        print(f"  Voice mode: {'Enabled' if use_voice else 'Text-only'}")
        print(f"  Wake word:  'Hello Asha' / 'Ok Asha'")
        print("=" * 60)

        # State
        self.state = "idle"
        self.pending_action = None
        self.last_ocr_text = None

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
        print("[INIT] Pocket ASHA ready")
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

    def speak(self, text: str):
        """Output text via speaker and console."""
        print(f"\n  Asha: {text}")
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

        prompt = "Say 'Hello Asha' + command, or type: " if require_wake else "Listening (or type): "
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
            return "You're welcome! Say Hello Asha when you need me.", False

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

    def _measure_vitals(self) -> Tuple[str, bool]:
        self.speak("Measuring vitals now. Please wait.")
        try:
            from sensor_handler import SensorHandler
            sh = SensorHandler()
            readings = sh.read_all()

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

    def _capture_and_analyze(self) -> Tuple[str, bool]:
        self.speak("Capturing image now.")
        try:
            from camera_handler import capture_image
            img_path = capture_image()
            if not img_path:
                return "Could not capture image. Make sure the camera is running.", False

            # Save to encounter
            if self.encounter.active:
                self.encounter.save_photo(img_path)

            # OCR
            self.speak("Reading the document.")
            from ocr_handler import extract_text, unload_ocr
            text = extract_text(img_path)
            unload_ocr()
            gc.collect()

            self.last_ocr_text = text
            if not text:
                return "No text found in the image. Try with a clearer picture.", False

            # Analyze with Bedrock
            from utils import check_internet
            if check_internet():
                from aws_handler import analyze_prescription
                analysis = analyze_prescription(text)
                if analysis:
                    return analysis, False

            # Offline fallback — just read the OCR text
            return f"I read the following from the document: {text[:300]}", False
        except Exception as e:
            self.log.error("[CAPTURE] %s", e)
            return "Error during capture. Please try again.", False

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
            "Say Hello Asha followed by your command."
        )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        """Main event loop."""
        global _running
        from config import GREETING_MESSAGE, WAKE_WORD_HINT
        from utils import free_memory

        # Language selection at startup
        self._ask_language()

        self.speak(GREETING_MESSAGE)

        needs_followup = False

        while _running:
            try:
                # Get input
                command = self.get_input(require_wake=not needs_followup)

                if not command:
                    needs_followup = False
                    continue

                # If encounter is active and in DEMOGRAPHICS state, parse demographics
                if (self.encounter.active
                        and self.encounter.state.value == "demographics"
                        and self.state == "idle"):
                    info = self.encounter.parse_demographics(command)
                    if info.get("name"):
                        self.encounter.set_demographics(
                            name=info["name"], age=info.get("age", ""),
                            gender=info.get("gender", ""),
                        )
                        self.encounter.advance_from_demographics()
                        prompt = self.encounter.get_next_prompt()
                        self.speak(f"Registered {info['name']}. {prompt}")
                        needs_followup = True
                        continue

                # Process command
                response, needs_followup = self.process_command(command)
                self.speak(response)

                # Check for exit
                if self.state == "exit":
                    break

                # Periodic cleanup
                free_memory()

            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log.error("[MAIN] %s", e)
                self.speak("Something went wrong. Please try again.")
                needs_followup = False

        self._shutdown()

    def _shutdown(self):
        """Clean shutdown."""
        print("\n[ASHA] Shutting down...")
        self.sync.stop()
        if self.encounter.active:
            self.encounter.end()
        from utils import free_memory
        free_memory()
        from aws_handler import clear_chat
        clear_chat()
        print("[ASHA] Goodbye!")

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
    parser = argparse.ArgumentParser(description="Pocket ASHA Healthcare Assistant")
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
        print("  POCKET ASHA - Guided Encounter Flow")
        print("=" * 60)

        import voice_handler
        from encounter_manager import EncounterManager
        from storage_manager import StorageManager
        from sync_manager import SyncManager
        from guided_flow import GuidedFlow

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
            print("[ASHA] Goodbye!")
    else:
        app = PocketAsha(use_voice=not args.text)
        app.run()


if __name__ == "__main__":
    main()
