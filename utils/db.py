import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

REGISTRY_FILE = "client_registry.json"

def get_client_registry():
    if not os.path.exists(REGISTRY_FILE):
        return []
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_client_registry(registry):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=4)

def test_connection(host, port, dbname, user, password):
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=5
        )
        conn.close()
        return True, "SUCCESS"
    except Exception as e:
        return False, str(e)

def get_client_connection(client_id):
    registry = get_client_registry()
    client = next((c for c in registry if c['client_id'] == client_id), None)
    if not client:
        raise ValueError(f"Client {client_id} not found.")
    
    return psycopg2.connect(
        host=client['db_host'],
        port=client['db_port'],
        dbname=client['db_name'],
        user=client['db_user'],
        password=client['db_password']
    )
