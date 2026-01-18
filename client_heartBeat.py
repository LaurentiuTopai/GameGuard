import time
import threading
import logging
import os # Avem nevoie de os pentru a inchide jocul
from .client_network import send_report

logger = logging.getLogger("CheatGuard_IS.heartbeat")

def _heartbeat_loop(config, token, stop_event):
    server = config.get("server_url")
    interval = config.get("heartbeat_interval_s", 10)
    
    if not server:
        logger.error("Nu s-a gasit niciun server; HEARTBEAT disabled")
        return
    
    while not stop_event.is_set():
        payload = {"type": "heartbeat", "token": token}
        
      
        ok, status_code = send_report(server, "/report", payload=payload)
        
       
        if status_code == 403:
            logger.critical("DISPOZITIV BANAT PERMANENT. Inchidere joc...")
            os.system("taskkill /F /IM ac_client.exe")
            os._exit(1) 
            
        logger.debug("Heartbeat: ok=%s, code=%s", ok, status_code)
        stop_event.wait(interval)

def start_heartbeat_thread(config, token):
    stop_event = threading.Event()
    t = threading.Thread(target=_heartbeat_loop, args=(config, token, stop_event), daemon=True, name="heartbeat")
    t.start()
    return stop_event