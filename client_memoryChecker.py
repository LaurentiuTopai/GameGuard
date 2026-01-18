from pymem import Pymem
import time 

class MemoryChecker:
    def __init__(self):
        self.process_name = "ac_client.exe" 
        self.pm = None
        self.base_address = None
        self.STATIC_PLAYER_BASE = 0x17E0A8
        self.OFFSETS = {
            'health': 0xEC,
            'armor': 0xF0,
            'ammo_ar': 0x140, 
            'fast_fire': 0x164
        } 

    def connect(self):
        try:
            self.pm = Pymem(self.process_name)
            self.base_address = self.pm.base_address
            return True
        except Exception:
            self.pm = None 
            return False

    def check_violations(self):
        if not self.pm:
            return False, ""

        try:
            
            player_ptr = self.pm.read_int(self.base_address + self.STATIC_PLAYER_BASE)
            
            
            if not player_ptr or player_ptr == 0:
                return False, ""

            
            health = self.pm.read_int(player_ptr + self.OFFSETS['health'])
            armor = self.pm.read_int(player_ptr + self.OFFSETS['armor'])
            ammo = self.pm.read_int(player_ptr + self.OFFSETS['ammo_ar'])

            
            if health > 100 or health < 0:
                return True, f"Health hack detectat: {health} HP"
            
            if armor > 100:
                return True, f"Armor hack detectat: {armor} AP"
            
            if ammo > 100: 
                return True, f"Infinite Ammo detectat: {ammo} gloanțe"

            return False, ""
        except Exception as e:
            
            self.pm = None
            return False, f"Eroare citire: {e}"