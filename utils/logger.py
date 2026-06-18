from datetime import datetime
import csv
import os

LOG_FILE = "audit_log.csv"

def log_action(admin_username, client_id, action, status="SUCCESS", details=""):
    file_exists = os.path.exists(LOG_FILE)
    
    with open(LOG_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Admin", "Client ID", "Action", "Status", "Details"])
        
        writer.writerow([
            datetime.now().isoformat(),
            admin_username,
            client_id,
            action,
            status,
            details
        ])

def get_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        return list(reader)
