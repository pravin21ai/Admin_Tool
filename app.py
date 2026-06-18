import streamlit as st
import os
from dotenv import load_dotenv
from utils.auth import check_password
from modules import client_registry

# Load environment variables
load_dotenv()

st.set_page_config(page_title="RiskEdge Admin Tool", layout="wide")

def main():
    if not check_password():
        return
        
    from utils.internal_db import init_internal_db
    init_internal_db()

    st.markdown("""
        <style>
        [data-testid="stSidebarNav"]::before {
            content: "RiskEdge Admin Tool";
            font-size: 32px;
            font-weight: 700;
            padding: 1.5rem 1.5rem 0.5rem 1.5rem;
            display: block;
            color: inherit;
        }
        </style>
    """, unsafe_allow_html=True)
    
    from modules import unified_upload, charges_upload, credential_gen, health_audit, license_gen_ui, license_dashboard
    
    # Native Streamlit navigation
    pg1 = st.Page(client_registry.render, title="Client Registry", icon="👥", url_path="client_registry")
    pg2 = st.Page(unified_upload.render, title="Unified Master Upload", icon="📁", url_path="unified_upload")
    pg3 = st.Page(charges_upload.render, title="Charges", icon="💰", url_path="charges")
    pg4 = st.Page(credential_gen.render, title="Credentials", icon="🔑", url_path="credentials")
    pg5 = st.Page(health_audit.render, title="Health & Audit", icon="🩺", url_path="health_audit")
    pg6 = st.Page(license_gen_ui.render, title="License Generator", icon="🛡️", url_path="license_generator")
    pg7 = st.Page(license_dashboard.render, title="Global License Dashboard", icon="🌍", url_path="license_dashboard")

    pg = st.navigation([pg1, pg2, pg3, pg4, pg5, pg6, pg7])
    pg.run()

if __name__ == "__main__":
    main()
