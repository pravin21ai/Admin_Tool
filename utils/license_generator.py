import os
import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

PRIVATE_KEY_FILE = "vendor_private.pem"
PUBLIC_KEY_FILE = "rms_public.pem"

def generate_keys_if_needed():
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
        print("Generating new RSA Keypair...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        public_key = private_key.public_key()
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        print(f"Keys generated: {PRIVATE_KEY_FILE}, {PUBLIC_KEY_FILE}")
        print("WARNING: KEEP YOUR PRIVATE KEY SAFE. GIVE PUBLIC KEY TO CLIENT SERVER.")

def generate_license():
    generate_keys_if_needed()
    
    print("\n--- RMS License Generator ---")
    client_name = input("Enter Client/Broker Name: ").strip()
    max_users = input("Enter Max Users [default 100]: ").strip()
    if not max_users: max_users = 100
    else: max_users = int(max_users)
    
    days_valid = input("Enter License Validity (Days) [default 365]: ").strip()
    if not days_valid: days_valid = 365
    else: days_valid = int(days_valid)
    
    print("\nBinding Type:")
    print("1. Physical Hardware (Machine ID)")
    print("2. Cloud (Domain / IP)")
    binding_choice = input("Select Option (1 or 2): ").strip()
    
    binding_type = "hardware" if binding_choice == '1' else "cloud"
    binding_value = ""
    
    if binding_type == "hardware":
        binding_value = input("Enter the client's Server Machine ID (e.g. MACH-XXXX): ").strip()
    else:
        binding_value = input("Enter the client's Server Domain or Static IP: ").strip()
        
    expiry = datetime.now(timezone.utc) + timedelta(days=days_valid)
    
    payload = {
        "client_name": client_name,
        "max_users": max_users,
        "binding_type": binding_type,
        "binding_value": binding_value,
        "exp": expiry,
        "iat": datetime.now(timezone.utc)
    }
    
    with open(PRIVATE_KEY_FILE, "rb") as f:
        private_key = f.read()
        
    # Sign JWT with RS256
    token = jwt.encode(payload, private_key, algorithm="RS256")
    
    with open("license.key", "w") as f:
        f.write(token)
        
    print("\n✅ License generated successfully: license.key")
    print(f"Details: {payload}")
    print("\nInstructions:")
    print("1. Send 'license.key' to the client.")
    print("2. Ensure 'rms_public.pem' is placed in their RMS server directory.")

if __name__ == "__main__":
    generate_license()
