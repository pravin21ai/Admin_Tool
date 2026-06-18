import uuid
import hashlib
import platform

def get_machine_id():
    """Generates a hardware ID based on MAC address and platform info."""
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
        
    system_info = f"{platform.system()}-{platform.node()}-{mac_str}"
    
    # Hash it to obfuscate the real MAC
    machine_hash = hashlib.sha256(system_info.encode()).hexdigest()[:16].upper()
    return f"MACH-{machine_hash}"

if __name__ == "__main__":
    print("=======================================")
    print("RMS Hardware Extractor")
    print("=======================================")
    print(f"Your Server Machine ID is: {get_machine_id()}")
    print("Send this ID to your vendor if you are using Hardware Binding.")
    print("=======================================")
