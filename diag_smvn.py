print("Script starting...")
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import importlib.util

print("Imports successful")

project_root = Path(r"d:\Project\mcp_db")
os.chdir(project_root)
load_dotenv(project_root / ".env")

sys.path.append(str(project_root / "mcp"))
from credentials_manager import CredentialsManager
from oracle_connector import OracleConnector

database_sid = "SMVNPDBext"
schema_name = "INFINITY21_JSMES"

async def check():
    print(f"--- Diagnostic for {database_sid}.{schema_name} ---")
    
    # 1. Credentials
    cm = CredentialsManager(credentials_dir=str(project_root / "data" / "credentials"))
    try:
        creds = cm.load_credentials(database_sid)
        print("✓ Credentials loaded")
    except Exception as e:
        print(f"✗ Credentials error: {e}")
        return

    # 2. DB Connection
    oracle = OracleConnector(**creds)
    if oracle.connect():
        print("✓ DB Connected")
        cursor = oracle.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM ALL_TABLES WHERE OWNER = '{schema_name.upper()}'")
        count = cursor.fetchone()[0]
        print(f"✓ Total tables in DB: {count}")
        oracle.disconnect()
    else:
        print("✗ DB Connection failed")
        return

    # 3. CSV Match
    csv_path = project_root / "data" / database_sid / schema_name / "csv_uploads" / "table_info_template.csv"
    if csv_path.exists():
        import csv
        import io
        try:
            # Try reading with different encodings
            content = ""
            for enc in ['utf-8-sig', 'cp949', 'utf-8']:
                try:
                    content = csv_path.read_text(encoding=enc)
                    print(f"✓ CSV read with {enc}")
                    break
                except:
                    continue
            
            if content:
                reader = csv.DictReader(io.StringIO(content))
                csv_rows = list(reader)
                print(f"✓ CSV has {len(csv_rows)} rows")
                if csv_rows:
                    print(f"  First CSV table: {csv_rows[0].get('table_name')}")
        except Exception as e:
            print(f"✗ CSV read error: {e}")
    else:
        print("✗ CSV not found")

if __name__ == "__main__":
    asyncio.run(check())
