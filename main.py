import json
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from .client_logger import setup_logger
from .client_token import load_or_create_token
from .client_network import send_report
from .client_heartBeat import start_heartbeat_thread
from .client_proccessScaner import start_procscanner_thread
from .client_integrity import start_integrity_thread
from .client_network import send_report , event_queue , flush_events_queue
from .client_memoryChecker import MemoryChecker
from .client_antidebug import AntiDebug
from .client_signatureScaner import SignatureScanner
from .client_proccessScaner import start_procscanner_thread, monitor_external_handles

BASE = Path(__file__).resolve().parent
CFG_PATH = BASE / "config.json"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
def print_gameguard_banner():
    # Coduri de culori pentru terminal
    banner = r"""
    #######################################################################
    #                                                                     #
    #   ██████╗  █████╗ ███╗   ███╗███████╗ ██████╗ ██╗   ██╗ █████╗ ██████╗  #
    #  ██╔════╝ ██╔══██╗████╗ ████║██╔════╝██╔════╝ ██║   ██║██╔══██╗██╔══██╗ #
    #  ██║  ███╗███████║██╔████╔██║█████╗  ██║  ███╗██║   ██║███████║██║  ██║ #
    #  ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝  ██║   ██║██║   ██║██╔══██║██║  ██║ #
    #  ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗╚██████╔╝╚██████╔╝██║  ██║██████╔╝ #
    #   ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝  #
    #                                                                     #
    #   --- [ GAMEGUARD - SISTEM ANTI-CHEAT v1.0 ] ---                    #
    #######################################################################
    """

    print(CYAN + banner + RESET)
    print(f"{BOLD}[*] Sesiune pornita:{RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{BOLD}[*] Status Server:{RESET} {GREEN}CONECTAT (127.0.0.1:5000){RESET}")
    print(f"{BOLD}[*] Mod Operare:{RESET} {YELLOW}MONITORIZARE SI SUPRAVEGHERE ACTIVA{RESET}")
    print("-" * 71)

def load_config(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing config: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def queue_event(payload):
    try:
        with open(BASE / "events_queue.jsonl", "a", encoding="utf-8") as q:
            q.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to queue event")

def report_wrapper(payload):
    server = config.get("server_url")
    ok, _ = send_report(server,"/report",payload)
    if not ok:
        queue_event(payload)

if __name__ == "__main__":
    print_gameguard_banner()
    try:
        config = load_config(CFG_PATH)
    except Exception as e:
        print("Failed to load config:", e)
        sys.exit(1)

    logger = setup_logger(str(BASE / config.get("log_file", "client.log")))
    logger.info("IS_AntiCheat client starting (pid=%s)", os.getpid())

    token_path = BASE / config.get("token_file", "client_token.dat")
    token = load_or_create_token(str(token_path))
    logger.debug("Token: %s...", token[:8])


    
    antidebug = AntiDebug()
    mem_check = MemoryChecker()
    sig_scanner = SignatureScanner()
    # start services
    hb_stop = start_heartbeat_thread(config, token)
    ps_stop = start_procscanner_thread(config, report_wrapper)
    int_stop = start_integrity_thread(config,report_wrapper)

    logger.info("Verificare ANTIDEBUG si MEMORYCHECK ACTIVEEE")

    try:
        while True:
            if antidebug.check_flags() or antidebug.check_external_apps():
                logger.warning("Debugger detectat!")
                report_wrapper({"event": "debugger_detected", "token": token, "severity": "critical"})
                break 

           
            is_detected, reason = monitor_external_handles("ac_client.exe")
            if is_detected:
                logger.warning(f"DETECȚIE ACTIVĂ: {reason}")
                report_wrapper({
                    "event": "unauthorized_handle",
                    "details": reason,
                    "token": token
                })
                print(f"\n{RED}{BOLD}[!!!] SECURITATE COMPROMISĂ: {reason}")
                os.system("taskkill /F /IM ac_client.exe >nul 2>&1")
                os._exit(1)


            if mem_check.connect(): 
                is_cheat, reason = mem_check.check_violations()
                if is_cheat:
                    logger.warning(f"{RED}{BOLD}Memory Violation: {reason}")
                    report_wrapper({
                        "event": "memory_corruption",
                        "details": reason,
                        "token": token
                    })
                    os.system("taskkill /F /IM ac_client.exe")
                    os._exit(1)
                    
            if time.time() % 300 < 2: 
                results = sig_scanner.scan_all_processes()
                for found in results:
                    logger.warning(f"Signature Match: {found['cheat']} in {found['process']}")
                    report_wrapper({
                    "event": "signature_match",
                    "process": found['process'],
                    "details": found['cheat']
            })
            
            # 3. Trimite eventualele evenimente salvate offline când serverul revine
            flush_events_queue(config.get("server_url"), "/report")

            time.sleep(2) # Pauză pentru a nu sufoca procesorul
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    finally:
        hb_stop.set()
        ps_stop.set()
        int_stop.set()
        logger.info("IS_AntiCheat client stopped")
