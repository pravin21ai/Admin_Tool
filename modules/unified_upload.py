import streamlit as st
import pandas as pd
from utils.db import get_client_registry, get_client_connection
from utils.excel_parser import parse_excel

def render():
    st.header("Unified Master Upload (Broker, Group, Client)")

    registry = get_client_registry()
    if not registry:
        st.warning("No clients registered. Please add a client first.")
        return

    client_names = {c['client_name']: c['client_id'] for c in registry}
    selected_client_name = st.selectbox("Select Target Client", list(client_names.keys()))
    client_id = client_names[selected_client_name]

    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col2:
        st.markdown("**Danger Zone**")
        if "delete_confirm" not in st.session_state:
            st.session_state.delete_confirm = False

        if not st.session_state.delete_confirm:
            if st.button("🗑️ Delete All Existing Data"):
                st.session_state.delete_confirm = True
                if hasattr(st, 'rerun'):
                    st.rerun()
                else:
                    st.experimental_rerun()
        else:
            st.warning("Are you sure? This will permanently wipe the database.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Delete", type="primary"):
                    try:
                        conn = get_client_connection(client_id)
                        cur = conn.cursor()
                        cur.execute('TRUNCATE TABLE mst_broker CASCADE;')
                        cur.execute('TRUNCATE TABLE mst_alert_rule CASCADE;')
                        cur.execute('TRUNCATE TABLE rms_audit_log CASCADE;')
                        conn.commit()
                        conn.close()
                        msg = st.empty()
                        msg.success("Database cleared successfully!")
                        import time
                        time.sleep(2)
                        msg.empty()
                        st.session_state.delete_confirm = False
                        if hasattr(st, 'rerun'):
                            st.rerun()
                        else:
                            st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Failed to clear database: {e}")
            with c2:
                if st.button("❌ Cancel"):
                    st.session_state.delete_confirm = False
                    if hasattr(st, 'rerun'):
                        st.rerun()
                    else:
                        st.experimental_rerun()

    with col1:
        uploaded_file = st.file_uploader("Upload Unified Master Excel", type=["xlsx"])

    if uploaded_file:
        try:
            st.info("Parsing unified file...")
            
            # Parse all sheets
            broker_df = parse_excel(uploaded_file, sheet_name="Broker")
            groups_df = parse_excel(uploaded_file, sheet_name="Groups")
            clients_df = parse_excel(uploaded_file, sheet_name="Clients")
            try:
                neat_df = parse_excel(uploaded_file, sheet_name="NEAT_CTCL", dtype=str)
                st.success("File parsed successfully. All four sheets found.")
            except Exception:
                neat_df = pd.DataFrame()
                st.success("File parsed successfully. Main sheets found (NEAT_CTCL not present).")
            
            # Business Validations
            if len(broker_df) > 1:
                st.error("Validation Error: Only one broker is allowed in the uploaded file.")
                return
                
            def check_compulsory(df, entity_name):
                code_col = f"{entity_name.lower()}_code"
                name_col = f"{entity_name.lower()}_name"
                if code_col in df.columns and (df[code_col].isnull().any() or (df[code_col] == '').any()):
                    return f"{entity_name} Code"
                if name_col in df.columns and (df[name_col].isnull().any() or (df[name_col] == '').any()):
                    return f"{entity_name} Name"
                if 'login_id' in df.columns and (df['login_id'].isnull().any() or (df['login_id'] == '').any()):
                    return f"Login ID for {entity_name}"
                return None

            errs = [e for e in [check_compulsory(broker_df, "Broker"), check_compulsory(groups_df, "Group"), check_compulsory(clients_df, "Client")] if e]
            if errs:
                st.error(f"Validation Error: Compulsory fields missing. Please provide: {', '.join(errs)}")
                return
            
            st.subheader("Validation Preview")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Broker Details", "Groups Details", "Clients Details", "Terminals Details"])
            with tab1:
                st.dataframe(broker_df.head())
            with tab2:
                st.dataframe(groups_df.head())
            with tab3:
                st.dataframe(clients_df.head())
            with tab4:
                st.dataframe(neat_df.head())

            st.write(f"Total Rows parsed: {len(broker_df)} Brokers | {len(groups_df)} Groups | {len(clients_df)} Clients | {len(neat_df)} Terminals")
                
            # Real Confirm & Insert
            if st.button("Confirm & Insert Records Now"):
                conn = None
                try:
                    conn = get_client_connection(client_id)
                    cur = conn.cursor()
                    
                    st.info("Starting database transaction...")
                    
                    from utils.license_validator import get_license_max_users, get_current_user_count
                    max_users = get_license_max_users(conn)
                    current_users = get_current_user_count(conn)
                    incoming_users = len(broker_df) + len(groups_df) + len(clients_df)
                    
                    if max_users > 0:
                        available_slots = max_users - current_users
                        if available_slots <= 0:
                            st.error(f"License Limit Reached! You have {current_users} users (Max: {max_users}). Cannot insert more users.")
                            conn.close()
                            return
                        
                        if incoming_users > available_slots:
                            allowed_clients = available_slots - len(broker_df) - len(groups_df)
                            if allowed_clients < 0:
                                st.error(f"Not enough license slots ({available_slots} left) to even insert the required Brokers/Groups.")
                                conn.close()
                                return
                                
                            st.warning(f"License Limit Hit: Only {available_slots} slots left out of {max_users}. Inserting first {allowed_clients} clients, and ignoring the remaining {len(clients_df) - allowed_clients}.")
                            clients_df = clients_df.head(allowed_clients)
                    
                    broker_id_map = {}
                    group_id_map = {}
                    
                    import bcrypt
                    import secrets
                    from datetime import datetime

                    def get_temp_pwd():
                        pwd = secrets.token_urlsafe(8)
                        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        return pwd, hashed

                    # 1. Brokers
                    for _, row in broker_df.iterrows():
                        cur.execute('''
                            INSERT INTO mst_broker (broker_code, broker_name, email, mobile_no, status, created_at, updated_at) 
                            VALUES (%s, %s, %s, %s, 'ACTIVE', NOW(), NOW()) RETURNING broker_id
                        ''', (row.get('broker_code'), row.get('broker_name'), row.get('email'), row.get('phone')))
                        b_id = cur.fetchone()[0]
                        broker_id_map[row.get('broker_code')] = b_id
                        
                        # Auth
                        pwd, hashed = get_temp_pwd()
                        cur.execute('''
                            INSERT INTO auth_user (username, password_hash, role, broker_id, status, created_at, updated_at)
                            VALUES (%s, %s, 'broker', %s, 'ACTIVE', NOW(), NOW())
                        ''', (row.get('login_id'), hashed, b_id))
                        
                        # Alerts
                        for col in ['mtm_loss', 'margin_loss', 'max_loss_limit']:
                            if pd.notna(row.get(col)):
                                cur.execute('''
                                    INSERT INTO mst_alert_rule (entity_type, alert_name, alert_category, severity, threshold_operator, threshold_value, is_active, created_at, updated_at)
                                    VALUES ('BROKER', %s, %s, 'CRITICAL', '>=', %s, TRUE, NOW(), NOW())
                                ''', (f"{row.get('broker_code')}_{col}", col, row.get(col)))

                    # 2. Groups
                    for _, row in groups_df.iterrows():
                        # We assume the group belongs to the first broker in the file if broker_code isn't in Groups sheet
                        b_id = list(broker_id_map.values())[0] if broker_id_map else None
                        
                        cur.execute('''
                            INSERT INTO mst_group (broker_id, group_code, group_name, email, mobile_no, status, created_at, updated_at, mtm_loss, margin_loss, max_loss) 
                            VALUES (%s, %s, %s, %s, %s, 'ACTIVE', NOW(), NOW(), %s, %s, %s) RETURNING group_id
                        ''', (b_id, row.get('group_code'), row.get('group_name'), row.get('email'), row.get('phone'), row.get('mtm_loss') or 0, row.get('margin_loss') or 0, row.get('max_loss_limit') or 0))
                        g_id = cur.fetchone()[0]
                        group_id_map[row.get('group_code')] = g_id
                        
                        # Auth
                        pwd, hashed = get_temp_pwd()
                        cur.execute('''
                            INSERT INTO auth_user (username, password_hash, role, broker_id, group_id, status, created_at, updated_at)
                            VALUES (%s, %s, 'group', %s, %s, 'ACTIVE', NOW(), NOW())
                        ''', (row.get('login_id'), hashed, b_id, g_id))
                        
                        # Alerts
                        for col in ['mtm_loss', 'margin_loss', 'max_loss_limit']:
                            if pd.notna(row.get(col)):
                                cur.execute('''
                                    INSERT INTO mst_alert_rule (entity_type, alert_name, alert_category, severity, threshold_operator, threshold_value, is_active, created_at, updated_at)
                                    VALUES ('GROUP', %s, %s, 'CRITICAL', '>=', %s, TRUE, NOW(), NOW())
                                ''', (f"{row.get('group_code')}_{col}", col, row.get(col)))

                    # 3. Clients
                    client_id_map = {}
                    for _, row in clients_df.iterrows():
                        b_id = list(broker_id_map.values())[0] if broker_id_map else None
                        g_id = group_id_map.get(row.get('group_code'))
                        
                        if not g_id:
                            raise ValueError(f"Group code {row.get('group_code')} for Client {row.get('client_code')} not found in Groups sheet.")

                        deposit = float(row.get('deposit', 0) or 0)
                        margin_leverage = float(row.get('margin_leverage', 0) or 0)
                        allocated_margin = deposit * margin_leverage

                        cur.execute('''
                            INSERT INTO mst_client (broker_id, group_id, client_code, client_name, email, mobile_no, deposit_amount, margin_leverage, allocated_margin, status, created_at, updated_at, mtm_loss, margin_loss, max_loss) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE', NOW(), NOW(), %s, %s, %s) RETURNING client_id
                        ''', (b_id, g_id, row.get('client_code'), row.get('client_name'), row.get('email'), row.get('phone'), deposit, margin_leverage, allocated_margin, row.get('mtm_loss') or 0, row.get('margin_loss') or 0, row.get('max_loss_limit') or 0))
                        c_id = cur.fetchone()[0]
                        client_id_map[str(row.get('client_code')).strip()] = (c_id, g_id)
                        
                        # Auth
                        pwd, hashed = get_temp_pwd()
                        cur.execute('''
                            INSERT INTO auth_user (username, password_hash, role, broker_id, group_id, client_id, status, created_at, updated_at)
                            VALUES (%s, %s, 'client', %s, %s, %s, 'ACTIVE', NOW(), NOW())
                        ''', (row.get('login_id'), hashed, b_id, g_id, c_id))
                        
                        # Alerts
                        for col in ['mtm_loss', 'margin_loss', 'max_loss_limit']:
                            if pd.notna(row.get(col)):
                                cur.execute('''
                                    INSERT INTO mst_alert_rule (entity_type, alert_name, alert_category, severity, threshold_operator, threshold_value, is_active, created_at, updated_at)
                                    VALUES ('CLIENT', %s, %s, 'CRITICAL', '>=', %s, TRUE, NOW(), NOW())
                                ''', (f"{row.get('client_code')}_{col}", col, row.get(col)))

                    # 4. NEAT_CTCL Terminals
                    for _, row in neat_df.iterrows():
                        c_code = str(row.get('client_code', '')).strip()
                        c_info = client_id_map.get(c_code)
                        if not c_info:
                            continue
                            
                        c_id, g_id = c_info
                        b_id = list(broker_id_map.values())[0] if broker_id_map else None
                        
                        exchange = str(row.get('exchange', ''))
                        segment = str(row.get('segment', ''))
                        neat_id = str(row.get('neat_id', '')).replace('.0', '')
                        ctcl_id = str(row.get('ctcl_id', '')).replace('.0', '')
                        auto_val = str(row.get('auto', '')).replace('.0', '')
                        manual_val = str(row.get('manual', '')).replace('.0', '')
                        
                        if exchange.lower() == 'nan': exchange = ''
                        if segment.lower() == 'nan': segment = ''
                        if neat_id.lower() == 'nan': neat_id = ''
                        if ctcl_id.lower() == 'nan': ctcl_id = ''
                        
                        neat_ctcl_type = (exchange + segment).upper()
                        
                        # Row 1: Auto
                        if auto_val and auto_val.lower() != 'nan':
                            neat_ctcl_id_auto = neat_id + ctcl_id + auto_val
                            cur.execute('''
                                INSERT INTO mst_trading_terminal (broker_id, group_id, client_id, exchange, segment, ctcl_id, neat_id, client_code, neat_ctcl_id, neat_ctcl_type, is_active, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                            ''', (b_id, g_id, c_id, exchange, segment, ctcl_id, neat_id, c_code, neat_ctcl_id_auto, neat_ctcl_type))
                            
                        # Row 2: Manual
                        if manual_val and manual_val.lower() != 'nan':
                            neat_ctcl_id_manual = neat_id + ctcl_id + manual_val
                            cur.execute('''
                                INSERT INTO mst_trading_terminal (broker_id, group_id, client_id, exchange, segment, ctcl_id, neat_id, client_code, neat_ctcl_id, neat_ctcl_type, is_active, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW(), NOW())
                            ''', (b_id, g_id, c_id, exchange, segment, ctcl_id, neat_id, c_code, neat_ctcl_id_manual, neat_ctcl_type))

                    conn.commit()
                    conn.close()
                    st.success("Broker, Groups, Clients, and Terminals successfully validated and inserted into target DB (Transaction Committed).")
                except Exception as db_err:
                    if conn:
                        conn.rollback()
                        conn.close()
                    st.error(f"Database Transaction Failed! Details: {db_err}")
                    
        except ValueError as e:
            st.error(f"Error reading sheets. Ensure 'Broker', 'Groups', and 'Clients' sheets exist. Details: {e}")
        except Exception as e:
            st.error(f"Failed to process file: {e}")
