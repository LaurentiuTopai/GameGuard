import time
import threading
import logging
import psutil
import os

logger = logging.getLogger("CheatGuard_IS.procscan")

def _normalize_name(n):
    return (n or "").strip().lower()

def monitor_external_handles(target_process_name="ac_client.exe"):
    SYSTEM_WHITELIST = [
        "services.exe", "lsass.exe", "svchost.exe", "csrss.exe", 
        "wininit.exe", "searchhost.exe", "runtimebroker.exe", 
        "shellexperiencehost.exe", "searchindexer.exe", "msmpeng.exe", "nimdnsresponder.exe"
    ]

    try:
        game_pid = None
        # Folosim o listă pentru a nu itera de două ori prin toate procesele
        all_processes = list(psutil.process_iter(['pid', 'name']))
        
        for proc in all_processes:
            if proc.info['name'] == target_process_name:
                game_pid = proc.info['pid']
                break
        
        # DACĂ JOCUL NU E PORNIT, returnăm un mesaj clar, nu None!
        if not game_pid:
            return False, "Jocul nu ruleaza"

        for proc in all_processes:
            try:
                p_name = (proc.info['name'] or "").lower()
                
                if p_name in [n.lower() for n in SYSTEM_WHITELIST]:
                    continue
                
                if proc.pid == os.getpid() or proc.pid == game_pid or proc.pid < 100:
                    continue
                
                suspicious_keywords = ["hack", "cheat", "esp", "aimbot", "injector", "trainer", "engine","assault.cube"]
                for word in suspicious_keywords:
                    if word in p_name:
                        # Mesaj de logare intern pentru tine
                        error_msg = f"Acces neautorizat: {proc.info['name']} (PID: {proc.pid})"
                        print(f"[DEBUG] DETECTIE: {error_msg}") 
                        return True, error_msg
            
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
                
    except Exception as e:
        logger.error(f"Eroare monitorizare handle-uri: {e}")
        return False, f"Eroare interna: {str(e)}"
    
    return False, "Sistem curat"

def scan_once(blacklist):
    found = []
    blacklist_norm = [_normalize_name(x) for x in blacklist]

    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            name = proc.info.get('name') or ""
            name_norm = _normalize_name(name)
            exe_path = _normalize_name(proc.info.get('exe') or "")

            is_blacklisted = False
            for black_item in blacklist_norm:
                if black_item and (black_item in name_norm or black_item in exe_path):
                    is_blacklisted = True
                    break

            if is_blacklisted:
                found.append({
                    "pid": proc.info.get('pid'),
                    "name": name,
                    "exe": proc.info.get('exe')
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            logger.exception("Unexpected error while iterating processes")
            
    return found

def _scanner_loop(config, report_fn, stop_event):
    interval = config.get("process_scan_interval_s", 5) 
    blacklist = config.get("blacklisted_processes", [])
    
    if not isinstance(blacklist, list):
        blacklist = []
        
    logger.info("Procesul de scanare a inceput (interval=%s)", interval)
    
    while not stop_event.is_set():
        suspects = scan_once(blacklist)
        if suspects:
            msg_lines = ["Am gasit un proces din blacklist:"]
            for p in suspects:
                msg_lines.append(f"-PID:{p['pid']}, Name:{p['name']}")
            
            full_msg = "\n".join(msg_lines)
            logger.warning(full_msg)
            
            payload = {"type": "process_alert", "details": suspects}
            try:
                report_fn(payload)
                print("\n[!!!] SECURITATE COMPROMISA. Inchidere fortata...")
                os.system("taskkill /F /IM ac_client.exe >nul 2>&1")
                os._exit(1) 
            except Exception:
                logger.exception("Eroare la raportarea alertei de proces")
        
        if stop_event.wait(interval):
            break

def start_procscanner_thread(config, report_fn):
    stop_event = threading.Event()
    t = threading.Thread(target=_scanner_loop, args=(config, report_fn, stop_event), daemon=True, name="procscanner")
    t.start()
    return stop_event