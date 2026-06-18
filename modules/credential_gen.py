import streamlit as st
import pandas as pd
from utils.db import get_client_registry, get_client_connection
from psycopg2.extras import RealDictCursor
from utils.excel_writer import create_credentials_report
import secrets
import bcrypt

def generate_temp_password():
    return secrets.token_urlsafe(8)

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def render():
    st.header("Credential Generation & Export")

    registry = get_client_registry()
    if not registry:
        st.warning("No clients registered. Please add a client first.")
        return

    client_names = {c['client_name']: c['client_id'] for c in registry}
    selected_client_name = st.selectbox("Select Target Client", list(client_names.keys()))

    st.markdown("---")
    st.info("This module generates secure credentials for all unprovisioned users in the client's DB.")

    if st.button("Generate & Download New Credentials"):
        with st.spinner("Connecting to database and generating credentials..."):
            try:
                client_id = client_names[selected_client_name]
                conn = get_client_connection(client_id)
                cur = conn.cursor(cursor_factory=RealDictCursor)

                # Fetch all users
                cur.execute('''
                    SELECT 
                        u.user_id,
                        u.username as login_id,
                        u.role,
                        COALESCE(b.broker_name, g.group_name, c.client_name) as name,
                        COALESCE(b.email, g.email, c.email) as email
                    FROM auth_user u
                    LEFT JOIN mst_broker b ON u.broker_id = b.broker_id
                    LEFT JOIN mst_group g ON u.group_id = g.group_id
                    LEFT JOIN mst_client c ON u.client_id = c.client_id
                ''')
                users = cur.fetchall()

                if not users:
                    st.warning("No users found in the database. Please upload Master Data first.")
                    conn.close()
                    return

                records = []
                for user in users:
                    raw_pwd = generate_temp_password()
                    hashed = hash_password(raw_pwd)

                    # Update DB with new hashed password
                    cur.execute('UPDATE auth_user SET password_hash = %s, updated_at = NOW() WHERE user_id = %s', (hashed, user['user_id']))

                    records.append({
                        "Name": user['name'] or 'Unknown',
                        "Role": str(user['role']).capitalize(),
                        "Login_ID": user['login_id'],
                        "Email": user['email'] or 'N/A',
                        "Temp_Password": raw_pwd
                    })

                conn.commit()
                conn.close()

                df = pd.DataFrame(records)
                st.success(f"Successfully generated new secure credentials for {len(users)} users in the database.")
                
                excel_data = create_credentials_report(df)
                st.download_button(
                    label="Download Credentials Excel",
                    data=excel_data,
                    file_name=f"credentials_{selected_client_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            except Exception as e:
                st.error(f"Failed to generate credentials: {e}")
