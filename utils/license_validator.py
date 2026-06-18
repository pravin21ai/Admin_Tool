import os
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import platform
import uuid
import hashlib

LICENSE_FILE = "license.key"
PUBLIC_KEY_FILE = "utils/rms_public.pem"

def get_current_machine_id():
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0,8*6,8)][::-1])
    system_info = f"{platform.system()}-{platform.node()}-{mac_str}"
    machine_hash = hashlib.sha256(system_info.encode()).hexdigest()[:16].upper()
    return f"MACH-{machine_hash}"

def validate_license(conn):
    """
    Validates the license_token from the database against the rms_public.pem.
    Returns:
        dict: The license payload if valid.
        str: Error message if invalid.
    """
    if not os.path.exists(PUBLIC_KEY_FILE):
        return None, "Public key not found. Contact Vendor."
        
    try:
        cur = conn.cursor()
        # Check if column exists first to gracefully handle uninitialized DBs
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='mst_license' AND column_name='license_token'")
        if not cur.fetchone():
            return None, "License token column missing in database. Contact Vendor to generate a license."
            
        cur.execute("SELECT license_token FROM mst_license LIMIT 1")
        row = cur.fetchone()
        if not row or not row[0]:
            return None, "No license token found in database. Contact Vendor."
            
        token = row[0].strip()
        
        with open(PUBLIC_KEY_FILE, "rb") as f:
            public_key = serialization.load_pem_public_key(
                f.read(), backend=default_backend()
            )
            
        # Verify signature and expiration date
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        
        # Verify Binding
        binding_type = payload.get("binding_type", "none")
        binding_value = payload.get("binding_value", "")
        
        if binding_type == "hardware":
            current_mach_id = get_current_machine_id()
            if binding_value != current_mach_id:
                return None, f"Hardware Binding Failed. Expected {binding_value}, got {current_mach_id}"
        elif binding_type == "cloud":
            # For cloud binding, this would check domain/IP or phone home
            pass
            
        return payload, None
        
    except jwt.ExpiredSignatureError:
        return None, "License has expired. Please renew."
    except jwt.InvalidTokenError as e:
        return None, f"Invalid License Token: {e}"
    except Exception as e:
        return None, f"License validation error: {e}"
        
def get_license_max_users(conn):
    """Returns the max_users allowed, or 0 if license is invalid."""
    payload, err = validate_license(conn)
    if err or not payload:
        return 0
    return payload.get("max_users", 0)

def get_current_user_count(conn):
    """Query db to get current number of users."""
    try:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM auth_user")
        return cur.fetchone()[0]
    except Exception:
        return 0
