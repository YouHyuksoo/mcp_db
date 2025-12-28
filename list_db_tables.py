import os
import sys
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(r"d:\Project\mcp_db")
load_dotenv(project_root / ".env")

sys.path.append(str(project_root / "mcp"))
from credentials_manager import CredentialsManager
from oracle_connector import OracleConnector

db_sid = "SMVNPDBext"
schema_name = "INFINITY21_JSMES"

try:
    cm = CredentialsManager(credentials_dir=str(project_root / "data" / "credentials"))
    creds = cm.load_credentials(db_sid)
    oracle = OracleConnector(**creds)
    if oracle.connect():
        tables = oracle.extract_tables(schema_name)
        with open(project_root / "db_tables.txt", "w") as f:
            for t in sorted(tables):
                f.write(f"{t}\n")
        print(f"Saved {len(tables)} tables to db_tables.txt")
        oracle.disconnect()
    else:
        print("Connection failed")
except Exception as e:
    print(f"Error: {e}")
