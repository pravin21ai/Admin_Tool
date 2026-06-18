import xlsxwriter
import os

def create_unified_master_template():
    path = os.path.join("templates", "unified_master_template.xlsx")
    wb = xlsxwriter.Workbook(path)
    
    # 1. Broker Sheet
    ws_broker = wb.add_worksheet("Broker")
    broker_cols = ['broker_code', 'broker_name', 'email', 'phone', 'login_id', 'mtm_loss', 'margin_loss', 'max_loss_limit']
    for i, col in enumerate(broker_cols):
        ws_broker.write(0, i, col)
        
    # 2. Groups Sheet
    ws_groups = wb.add_worksheet("Groups")
    groups_cols = ['group_code', 'group_name', 'email', 'phone', 'login_id', 'mtm_loss', 'margin_loss', 'max_loss_limit']
    for i, col in enumerate(groups_cols):
        ws_groups.write(0, i, col)
        
    # 3. Clients Sheet
    ws_clients = wb.add_worksheet("Clients")
    clients_cols = ['client_code', 'client_name', 'group_code', 'email', 'phone', 'login_id', 'deposit', 'margin_leverage', 'mtm_loss', 'margin_loss', 'max_loss_limit']
    for i, col in enumerate(clients_cols):
        ws_clients.write(0, i, col)
        
    # 4. NEAT_CTCL Sheet
    ws_neat = wb.add_worksheet("NEAT_CTCL")
    neat_cols = ['client_code', 'exchange', 'segment', 'neat_id', 'ctcl_id', 'auto', 'manual']
    for i, col in enumerate(neat_cols):
        ws_neat.write(0, i, col)
        
    wb.close()

def create_charges_template():
    path = os.path.join("templates", "charges_master_template.xlsx")
    wb = xlsxwriter.Workbook(path)
    ws = wb.add_worksheet("Charges")
    columns = ["entity_type", "entity_code", "brokerage_pct", "stt_pct", "txn_charge_pct", "gst_pct", "sebi_fee", "stamp_duty"]
    for i, col in enumerate(columns):
        ws.write(0, i, col)
    wb.close()

if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    create_unified_master_template()
    create_charges_template()
    print("Templates created successfully.")
