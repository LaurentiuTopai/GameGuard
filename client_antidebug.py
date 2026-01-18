from ctypes import *
import psutil
import sys

ProcessDebugPort = 7

class AntiDebug:
    def __init__(self):
        self.kernel32 = windll.kernel32
        self.ntdll = windll.ntdll
        self.black_list = [
            "x64dbg.exe", "ollydbg.exe", "cheatengine-x64.exe", 
            "idaq64.exe", "ghidra.exe", "wireshark.exe", "scylla.exe"
        ]

    def check_flags(self):
        # 1. IsDebuggerPresent
        if self.kernel32.IsDebuggerPresent():
            return True

        # 2. CheckRemoteDebuggerPresent
        is_remote_debugged = c_bool(False)
        self.kernel32.CheckRemoteDebuggerPresent(self.kernel32.GetCurrentProcess(), byref(is_remote_debugged))
        if is_remote_debugged.value:
            return True

        #3. NtQueryInformationProcess
        debug_port = c_uint32(0)
        status = self.ntdll.NtQueryInformationProcess(
            self.kernel32.GetCurrentProcess(),
            ProcessDebugPort,
            byref(debug_port),
            sizeof(debug_port),
            None
        )
        if status == 0 and debug_port.value != 0:
            return True

        return False

    def check_external_apps(self):
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in [app.lower() for app in self.black_list]:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

ad = AntiDebug()
if ad.check_flags() or ad.check_external_apps():
    print("CRITICAL: Debugger detectat! Se aplică măsuri...")
    sys.exit(1)
else:
    print("Sistem curat.")