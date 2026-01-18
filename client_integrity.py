import threading
import time
import json
import os
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger("CheatGuard_IS.integrity")

BASE = Path(__file__).resolve().parent
HASHLIST_PATH = BASE / "hashlist.json"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_hashlist():
    if not HASHLIST_PATH.exists():
        logger.debug("No hashlist found at %s", HASHLIST_PATH)
        return {}
    try:
        return json.loads(HASHLIST_PATH.read_text(encoding="utf-8"))
    except Exception:
        logger.exception("Failed to load hashlist.json")
        return {}

def verify_once(report_fn):
    expected = load_hashlist()
    problems = []
    for path, expected_hash in expected.items():
        try:
            if not os.path.exists(path):
                problems.append({"path": path, "issue": "missing"})
                continue
            current = sha256_file(path)
            if current != expected_hash:
                problems.append({
                    "path": path,
                    "issue": "mismatch",
                    "expected": expected_hash,
                    "current": current
                })
        except Exception as e:
            logger.exception("Error while checking %s", path)
            problems.append({"path": path, "issue": "error", "error": str(e)})
    if problems:
        # Logăm compact
        lines = ["Integrity issues found:"]
        for p in problems:
            lines.append(f"- {p['path']}: {p['issue']}")
        logger.warning("\n".join(lines))
        try:
            report_fn({"type": "integrity_alert", "details": problems})
        except Exception:
            logger.exception("Failed to report integrity issues")
    return problems

def _loop(config, report_fn, stop_event):
    interval = config.get("integrity_check_interval_s", 30)
    logger.info("Integrity checker started (interval=%s)", interval)
    while not stop_event.is_set():
        try:
            verify_once(report_fn)
        except Exception:
            logger.exception("Unexpected error in integrity loop")
        stop_event.wait(interval)

def start_integrity_thread(config, report_fn):
    stop_event = threading.Event()
    t = threading.Thread(target=_loop, args=(config, report_fn, stop_event), daemon=True, name="integrity")
    t.start()
    return stop_event
