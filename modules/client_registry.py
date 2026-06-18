import streamlit as st
from utils.db import get_client_registry, save_client_registry, test_connection

def render():
    st.header("Client Registry")
    
    tab1, tab2 = st.tabs(["View Clients", "Add New Client"])
    
    with tab1:
        registry = get_client_registry()
        if not registry:
            st.info("No clients registered.")
        else:
            for client in registry:
                with st.expander(f"{client['client_name']} ({client['db_name']} @ {client['db_host']})"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("Test Connection", key=f"test_{client['client_id']}"):
                            success, msg = test_connection(
                                client['db_host'], client['db_port'], client['db_name'], 
                                client['db_user'], client['db_password']
                            )
                            if success:
                                st.success("Connection Successful")
                            else:
                                st.error(f"Connection Failed: {msg}")
                    with c2:
                        edit_key = f"show_edit_{client['client_id']}"
                        if st.button("Edit Connection", key=f"btn_edit_{client['client_id']}"):
                            st.session_state[edit_key] = not st.session_state.get(edit_key, False)
                            st.rerun()
                    with c3:
                        if st.button("Remove Client", key=f"remove_{client['client_id']}", type="primary"):
                            registry = [c for c in registry if c['client_id'] != client['client_id']]
                            save_client_registry(registry)
                            st.success("Client removed.")
                            st.rerun()
                            
                    if st.session_state.get(f"show_edit_{client['client_id']}", False):
                        st.markdown("---")
                        st.markdown("**Edit Connection Details**")
                        with st.form(f"edit_{client['client_id']}"):
                            col_a, col_b = st.columns(2)
                            with col_a:
                                new_host = st.text_input("Database Host", value=client['db_host'])
                                new_port = st.text_input("Database Port", value=client['db_port'])
                                new_name = st.text_input("Database Name", value=client['db_name'])
                            with col_b:
                                new_user = st.text_input("Database User", value=client['db_user'])
                                new_password = st.text_input("Database Password", value=client['db_password'], type="password")
                                
                            if st.form_submit_button("Update Connection"):
                                if not all([new_host, new_port, new_name, new_user, new_password]):
                                    st.error("All fields are required.")
                                else:
                                    for c in registry:
                                        if c['client_id'] == client['client_id']:
                                            c['db_host'] = new_host
                                            c['db_port'] = new_port
                                            c['db_name'] = new_name
                                            c['db_user'] = new_user
                                            c['db_password'] = new_password
                                    save_client_registry(registry)
                                    msg = st.empty()
                                    msg.success("Connection updated successfully!")
                                    import time
                                    time.sleep(2)
                                    msg.empty()
                                    st.session_state[f"show_edit_{client['client_id']}"] = False
                                    st.rerun()

    with tab2:
        with st.form("add_client_form"):
            client_name = st.text_input("Client Name")
            db_host = st.text_input("Database Host", value="localhost")
            db_port = st.text_input("Database Port", value="5432")
            db_name = st.text_input("Database Name")
            db_user = st.text_input("Database User")
            db_password = st.text_input("Database Password", type="password")
            
            submitted = st.form_submit_button("Add Client")
            if submitted:
                if not all([client_name, db_host, db_port, db_name, db_user, db_password]):
                    st.error("All fields are required.")
                else:
                    client_id = client_name.lower().replace(" ", "_")
                    registry = get_client_registry()
                    if any(c['client_id'] == client_id for c in registry):
                        st.error("Client with this name already exists.")
                    else:
                        registry.append({
                            "client_id": client_id,
                            "client_name": client_name,
                            "db_host": db_host,
                            "db_port": db_port,
                            "db_name": db_name,
                            "db_user": db_user,
                            "db_password": db_password
                        })
                        save_client_registry(registry)
                        st.success("Client added successfully!")
                        st.rerun()
