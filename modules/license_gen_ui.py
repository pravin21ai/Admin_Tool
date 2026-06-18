import streamlit as st
import os
import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

PRIVATE_KEY_FILE = "utils/vendor_private.pem"
PUBLIC_KEY_FILE = "utils/rms_public.pem"

def generate_keys_if_needed():
    os.makedirs("utils", exist_ok=True)
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):
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
        return True
    return False

def render():
    st.header("RMS License Generator")
    st.markdown("Run the hardware extractor script on the client's server to generate their Machine ID.")
    
    with st.expander("🛠️ Client Utilities (Download & Send to Client)"):
        st.write("If you are using **Physical Hardware Binding**, the client must run this script on their server to generate their Machine ID. They will send the resulting ID back to you.")
        try:
            with open("utils/hardware_extractor.py", "rb") as f:
                extractor_code = f.read()
            st.download_button(
                label="⬇️ Download hardware_extractor.py",
                data=extractor_code,
                file_name="hardware_extractor.py",
                mime="text/x-python"
            )
        except Exception as e:
            st.error("Extractor script not found.")
    
    if generate_keys_if_needed():
        st.success("New Master RSA Keypair generated automatically!")
        
    from utils.db import get_client_registry, get_client_connection
    clients = get_client_registry()
    if not clients:
        st.warning("No clients registered in the Admin Tool. Please add a client first.")
        return
        
    client_ids = [""] + [c["client_id"] for c in clients]
    selected_client_id = st.selectbox("Select Target Client Database", client_ids, format_func=lambda x: "--- Select a Client ---" if x == "" else next((c["client_name"] for c in clients if c["client_id"] == x), x))

    if not selected_client_id:
        st.info("Please select a client from the dropdown above to generate a license.")
        return

    with st.container():
        client_name = next((c["client_name"] for c in clients if c["client_id"] == selected_client_id), "Unknown")
        st.info(f"Targeting Database for: **{client_name}**")
        
        plan_choice = st.selectbox("Select License Plan", ["Essential (50 Users)", "Prime (100 Users)", "Elite (250 Users)", "Apex (500 Users)", "Infinity (Unlimited)", "Custom Plan"])
        
        col1, col2 = st.columns(2)
        with col1:
            if "Essential" in plan_choice:
                max_users = st.number_input("Max Users", value=50, disabled=True)
            elif "Prime" in plan_choice:
                max_users = st.number_input("Max Users", value=100, disabled=True)
            elif "Elite" in plan_choice:
                max_users = st.number_input("Max Users", value=250, disabled=True)
            elif "Apex" in plan_choice:
                max_users = st.number_input("Max Users", value=500, disabled=True)
            elif "Infinity" in plan_choice:
                max_users = st.number_input("Max Users (Unlimited)", value=999999, disabled=True)
            else:
                max_users = st.number_input("Max Users", min_value=1, value=100, step=10)
        with col2:
            validity_period = st.selectbox("Validity Period", ["Weekly", "Monthly", "Quarterly", "Yearly", "Custom (Days)"], index=3)
            days_valid = 365
            if validity_period == "Weekly": days_valid = 7
            elif validity_period == "Monthly": days_valid = 30
            elif validity_period == "Quarterly": days_valid = 90
            elif validity_period == "Yearly": days_valid = 365
            elif validity_period == "Custom (Days)":
                days_valid = st.number_input("Enter Custom Days", min_value=1, value=365, step=1)
            
        st.markdown("#### Server Binding")
        binding_choice = st.radio("Select how to lock the server:", 
                                 ["Physical Hardware (Machine ID)", "Cloud Server (Domain / IP)", "No Binding (Portable)"])
        
        binding_value = ""
        if "Physical" in binding_choice:
            binding_type = "hardware"
            binding_value = st.text_input("Enter the client's Server Machine ID (e.g. MACH-XXXX):")
        elif "Cloud" in binding_choice:
            binding_type = "cloud"
            binding_value = st.text_input("Enter the client's Server Domain or Static IP:")
        else:
            binding_type = "none"
            
        submitted = st.button("Generate License Key", type="primary")
        
        if submitted:
            if not client_name:
                st.error("Client Name is required.")
                return
            if binding_type != "none" and not binding_value:
                st.error("Binding Value is required for the selected binding type.")
                return
                
            expiry = datetime.now(timezone.utc) + timedelta(days=days_valid)
            
            payload = {
                "client_name": client_name,
                "max_users": max_users,
                "binding_type": binding_type,
                "binding_value": binding_value,
                "exp": expiry,
                "iat": datetime.now(timezone.utc)
            }
            
            try:
                with open(PRIVATE_KEY_FILE, "rb") as f:
                    private_key = f.read()
                    
                token = jwt.encode(payload, private_key, algorithm="RS256")
                
                # --- DB INJECTION LOGIC ---
                conn = get_client_connection(selected_client_id)
                cur = conn.cursor()
                
                # Ensure the license_token column exists in their mst_license table
                cur.execute("""
                    DO $$ 
                    BEGIN 
                        BEGIN
                            ALTER TABLE mst_license ADD COLUMN license_token TEXT;
                        EXCEPTION
                            WHEN duplicate_column THEN RAISE NOTICE 'column license_token already exists in mst_license.';
                        END;
                    END;
                    $$
                """)
                
                # Check if they already have a license row
                cur.execute("SELECT count(*) FROM mst_license")
                row_count = cur.fetchone()[0]
                
                plan_name_clean = plan_choice.split()[0]
                if row_count == 0:
                    # Fetch a broker_id to satisfy the NOT NULL constraint
                    cur.execute("SELECT broker_id FROM mst_broker LIMIT 1")
                    broker_row = cur.fetchone()
                    broker_id = broker_row[0] if broker_row else 1
                    
                    cur.execute("INSERT INTO mst_license (broker_id, plan_name, start_date, end_date, status, license_token, created_at) VALUES (%s, %s, CURRENT_DATE, %s, 'ACTIVE', %s, NOW())", (broker_id, plan_name_clean, expiry, token))
                else:
                    cur.execute("UPDATE mst_license SET plan_name=%s, end_date=%s, license_token=%s WHERE license_id = (SELECT license_id FROM mst_license LIMIT 1)", (plan_name_clean, expiry, token))
                
                conn.commit()
                conn.close()
                
                # --- LOG TO INTERNAL DB ---
                from utils.internal_db import log_license_generation
                log_license_generation(
                    client_id=selected_client_id,
                    client_name=client_name,
                    plan_name=plan_name_clean,
                    max_users=max_users,
                    expiry_date=expiry.strftime('%Y-%m-%d %H:%M:%S')
                )
                
                st.success(f"✅ License generated and instantly pushed to **{client_name}'s** Database!")
                
                with st.expander("View License Payload Details"):
                    st.json(payload)
                    
            except Exception as e:
                st.error(f"Error generating and pushing license: {e}")
