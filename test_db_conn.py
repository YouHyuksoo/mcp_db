import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import importlib.util

# Setup
project_root = Path(r"d:\Project\mcp_db")
os.chdir(project_root)
load_dotenv(project_root / ".env")

# Import OracleConnector
mcp_path = project_root / "mcp"
oracle_connector_spec = importlib.util.spec_from_file_location(
    "oracle_connector", mcp_path / "oracle_connector.py"
)
oracle_connector_module = importlib.util.module_from_spec(oracle_connector_spec)
oracle_connector_spec.loader.exec_module(oracle_connector_module)
OracleConnector = oracle_connector_module.OracleConnector

# Import CredentialsManager
credentials_manager_spec = importlib.util.spec_from_file_location(
    "credentials_manager", mcp_path / "credentials_manager.py"
)
credentials_manager_module = importlib.util.module_from_spec(credentials_manager_spec)
credentials_manager_spec.loader.exec_module(credentials_manager_module)
CredentialsManager = credentials_manager_module.CredentialsManager

# Test Connection
db_sid = "SMVNPDBext"
schema_name = "INFINITY21_JSMES"

try:
    cm = CredentialsManager(credentials_dir=str(project_root / "data" / "credentials"))
    creds = cm.load_credentials(db_sid)
    
    # Force use of cx_Oracle or oracledb if available
    oracle = OracleConnector(**creds)
    print(f"Connecting to {db_sid}...")
    if oracle.connect():
        print("✓ Connected successfully")
        
        # Check tables
        tables = oracle.extract_tables(schema_name)
        print(f"✓ Found {len(tables)} tables in schema {schema_name}")
        if tables:
            print(f"Sample tables: {tables[:10]}")
            
        oracle.disconnect()
    else:
        print("✗ Connection failed")
except Exception as e:
    print(f"✗ Error: {e}")
