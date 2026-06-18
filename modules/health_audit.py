import streamlit as st
import pandas as pd
from utils.db import get_client_registry, test_connection
from utils.logger import get_logs

def render():
    st.header("Health & Audit Log")
    
    tab1, tab2 = st.tabs(["Connection Health", "Audit Logs"])
    
    with tab1:
        st.subheader("Live Database Health")
        registry = get_client_registry()
        if not registry:
            st.info("No clients registered.")
        else:
            for c in registry:
                success, msg = test_connection(c['db_host'], c['db_port'], c['db_name'], c['db_user'], c['db_password'])
                if success:
                    st.success(f"{c['client_name']} ({c['db_name']}): Connected")
                else:
                    st.error(f"{c['client_name']} ({c['db_name']}): Failed - {msg}")

    with tab2:
        st.subheader("Action Audit Logs")
        logs = get_logs()
        if not logs:
            st.info("No actions logged yet.")
        else:
            df = pd.DataFrame(logs)
            st.dataframe(df)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Logs as CSV",
                csv,
                "audit_logs.csv",
                "text/csv"
            )
