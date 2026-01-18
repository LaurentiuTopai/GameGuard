import psutil
import pymem

class SignatureScanner:
    def __init__(self):
        self.signatures = [
            {
                "name": "Cheat Engine Components",
                "sig": b"\x55\x8B\xEC\x83\xEC\x08\x53\x56\x57\x8B\x45\x08", 
                "description": "Detecție bazată pe structura internă Cheat Engine"
            },
            {
                "name": "SpeedHack Pattern",
                "sig": b"\x72\x65\x61\x64\x4c\x6f\x6e\x67\x42\x65\x61\x6e",
                "description": "Pattern specific pentru modificarea vitezei"
            }
        ]

    def scan_all_processes(self):
        detected_signatures = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                
                if proc.info['name'] in ["System", "svchost.exe", "python.exe"]:
                    continue

                pm = pymem.Pymem(proc.info['pid'])
                
                memory_dump = pm.read_bytes(pm.base_address, 10000) 

                for s in self.signatures:
                    if s["sig"] in memory_dump:
                        detected_signatures.append({
                            "process": proc.info['name'],
                            "cheat": s["name"]
                        })
            except Exception:
                continue
                
        return detected_signatures