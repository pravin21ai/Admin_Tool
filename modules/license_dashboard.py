import streamlit as st
import pandas as pd
from utils.db import get_client_registry, get_client_connection
from utils.license_validator import validate_license
from datetime import datetime, timezone

def render():
    st.header("🌍 Global License Dashboard")
    st.markdown("View the license status of all registered clients at a glance.")
    
    clients = get_client_registry()
    
    tab1, tab2 = st.tabs(["🔴 Live Status Monitor", "📜 Generation History Log"])
    
    with tab1:
        st.write("This tool securely pings each client's remote database in real-time to cryptographically verify their current license.")
        if not clients:
            st.warning("No clients registered in the Admin Tool. Please add a client first.")
            return
            
        if st.button("🔄 Fetch Global License Data", type="primary"):
            with st.spinner("Connecting to all client databases..."):
                dashboard_data = []
                for c in clients:
                    client_name = c["client_name"]
                    client_id = c["client_id"]
                    try:
                        conn = get_client_connection(client_id)
                        cur = conn.cursor()
                        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'mst_license')")
                        if not cur.fetchone()[0]:
                            dashboard_data.append({"Client": client_name, "Status": "⚠️ No License Table", "Plan": "-", "Max Users": "-", "Expiry": "-"})
                        else:
                            payload, err = validate_license(conn)
                            
                            cur.execute("SELECT plan_name FROM mst_license LIMIT 1")
                            db_plan = cur.fetchone()
                            plan_display = db_plan[0] if db_plan else "Unknown"
                            
                            if err:
                                dashboard_data.append({"Client": client_name, "Status": "🔴 EXPIRED / INVALID", "Plan": plan_display, "Max Users": "-", "Expiry": err})
                            else:
                                users_limit = payload.get("max_users", 0)
                                exp_timestamp = payload.get("exp", 0)
                                exp_date = datetime.fromtimestamp(exp_timestamp, timezone.utc).strftime('%Y-%m-%d')
                                
                                dashboard_data.append({"Client": client_name, "Status": "🟢 ACTIVE", "Plan": plan_display, "Max Users": users_limit, "Expiry": exp_date})
                        conn.close()
                    except Exception as e:
                        dashboard_data.append({"Client": client_name, "Status": "❌ Connection Error", "Plan": "-", "Max Users": "-", "Expiry": "-"})
                
                if dashboard_data:
                    df = pd.DataFrame(dashboard_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No clients to display.")

    with tab2:
        st.write("This local ledger keeps a permanent record of every license you have ever generated.")
        
        try:
            from utils.internal_db import get_license_history
            history_data = get_license_history()
            
            if not history_data:
                st.info("No licenses have been generated yet.")
            else:
                history_df = pd.DataFrame(history_data)
                
                # Format the columns for display
                history_df = history_df.rename(columns={
                    "history_id": "Log ID",
                    "client_name": "Client Name",
                    "plan_name": "Plan",
                    "max_users": "Max Users",
                    "expiry_date": "Expiry Date",
                    "generated_at": "Generated At"
                })
                # Drop the raw client_id column from the UI
                history_df = history_df.drop(columns=["client_id"])
                
                st.dataframe(history_df, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Could not load generation history: {e}")
