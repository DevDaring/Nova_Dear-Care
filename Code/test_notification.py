#!/usr/bin/env python3
"""
test_notification.py — Test that the verdict server starts
and serves verdicts to the Fit-U Flutter app.

Steps:
  1. Start verdict HTTP server on port 8080
  2. Add a test verdict
  3. Poll /api/health to verify server is running
  4. Poll /api/verdicts?worker_id=DC-KOUSHIK-001 to verify verdict delivery
  5. Verify the response contains the test verdict

Run:
    cd ~/Documents/AI_4_Bharat/Code
    env -u LD_LIBRARY_PATH -u LD_PRELOAD python3 test_notification.py
"""

import json
import sys
import time
import urllib.request

# Add Code directory to path
sys.path.insert(0, ".")

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
PORT = 8080
BASE = f"http://127.0.0.1:{PORT}"
WORKER_ID = "DC-KOUSHIK-001"

results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append(condition)
    msg = f"  {status}  {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    return condition


def main():
    print("=" * 60)
    print("  NOTIFICATION PUSH TEST")
    print("=" * 60)

    # --- Step 1: Start verdict server ---
    print("\n[1/5] Starting verdict server...")
    from verdict_server import start_server, add_verdict
    server = start_server(PORT)
    time.sleep(0.5)
    check("Verdict server started", server is not None, f"port {PORT}")

    # --- Step 2: Health check ---
    print("\n[2/5] Health check...")
    try:
        req = urllib.request.Request(f"{BASE}/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            check("Health endpoint responds", resp.status == 200, f"status={data.get('status')}")
            check("Verdict count is 0", data.get("verdicts") == 0)
    except Exception as e:
        check("Health endpoint responds", False, str(e))

    # --- Step 3: Add test verdict ---
    print("\n[3/5] Adding test verdict...")
    test_verdict = {
        "encounter_id": "TEST-ENC-001",
        "worker_id": WORKER_ID,
        "triage_level": "ROUTINE",
        "summary": "Test notification: Patient vitals normal. SpO2 98%, HR 72 bpm.",
        "timestamp": "2026-03-16T12:00:00",
        "s3_path": "encounters/test/TEST-ENC-001.json",
    }
    add_verdict(test_verdict)
    check("Test verdict added", True, f"encounter_id={test_verdict['encounter_id']}")

    # --- Step 4: Poll verdicts endpoint ---
    print("\n[4/5] Polling /api/verdicts?worker_id=DC-KOUSHIK-001 ...")
    try:
        url = f"{BASE}/api/verdicts?worker_id={WORKER_ID}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            check("Verdicts endpoint responds", resp.status == 200)
            check("Response is a list", isinstance(body, list), f"len={len(body)}")
            check("Contains 1 verdict", len(body) == 1)
            if body:
                v = body[0]
                check("encounter_id matches", v.get("encounter_id") == "TEST-ENC-001")
                check("worker_id matches", v.get("worker_id") == WORKER_ID)
                check("triage_level is ROUTINE", v.get("triage_level") == "ROUTINE")
                check("summary present", len(v.get("summary", "")) > 0, v.get("summary", "")[:60])
    except Exception as e:
        check("Verdicts endpoint responds", False, str(e))

    # --- Step 5: Verify filtering ---
    print("\n[5/5] Verify worker_id filtering...")
    try:
        url = f"{BASE}/api/verdicts?worker_id=NONEXISTENT"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
            check("Filter returns empty for wrong worker", len(body) == 0, "correctly filtered")
    except Exception as e:
        check("Filter returns empty for wrong worker", False, str(e))

    # Summary
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 60)
    if passed == total:
        print(f"  \033[92mALL {total} CHECKS PASSED\033[0m — Notification pipeline ready!")
        print(f"  Flutter app can poll http://<DEVICE_IP>:{PORT}/api/verdicts")
    else:
        print(f"  \033[91m{total - passed}/{total} CHECKS FAILED\033[0m")
    print("=" * 60)

    server.shutdown()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
