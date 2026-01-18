import requests
import logging
import time
import json
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger("CheatGuard_IS.network")
Base = Path(__file__).resolve().parent

def send_report(server_url, endpoint="/report", payload=None, timeout=5, retries=3, backoff=1.0):
    url = urljoin(server_url, endpoint.lstrip("/"))
    payload = payload or {}
    attempt = 0
    
    while attempt <= retries:
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 403:
                logger.warning("Acces interzis (Banned): %s", r.status_code)
                return False, 403
            
            r.raise_for_status() 
            logger.debug("Report sent: %s %s", url, r.status_code)
            return True, r.status_code 
            
        except requests.exceptions.HTTPError as e:
            logger.debug("HTTP Error: %s", e)
            attempt += 1
            time.sleep(backoff * attempt)
        except requests.RequestException as e:
            logger.debug("Erroare Network report: %s", e)
            attempt += 1
            time.sleep(backoff * attempt)
        except Exception as e:
            logger.exception("Erroare neasteptata in send_report: %s", e)
            break
            
    return False, None
def event_queue(event,event_file= "event_queue.json"):
     path = Base / event_file
     try:
          with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
     except Exception:
        logger.exception("Failed to queue event locally")
def flush_events_queue(server_url, events_file="events_queue.jsonl"):
    # încearcă să trimită evenimentele din coadă
    path = Base / events_file
    if not path.exists():
        return
    remaining = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                evt = json.loads(line)
            except Exception:
                continue
            ok, _ = send_report(server_url, "/report", evt)
            if not ok:
                remaining.append(evt)
    # rescrie ceea ce nu s-a trimis
    if remaining:
        with open(path, "w", encoding="utf-8") as f:
            for evt in remaining:
                f.write(json.dumps(evt, ensure_ascii=False) + "\n")
    else:
        try:
            path.unlink()
        except Exception:
            pass