import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Setup paths
project_root = Path(r"d:\Project\mcp_db")
os.chdir(project_root)
load_dotenv(project_root / ".env")

# Mock FastAPI Request app state
class MockApp:
    def __init__(self, vector_store):
        self.state = type('obj', (object,), {'vector_store': vector_store})

async def main():
    database_sid = "SMVNPDBext"
    schema_name = "INFINITY21_JSMES"
    
    print(f"Force processing {database_sid}.{schema_name}...")
    
    # 1. Initialize services
    sys.path.append(str(project_root / "backend"))
    from app.core.vector_store import VectorStore
    from app.core.embedding_service import EmbeddingService
    
    vector_store = VectorStore()
    await vector_store.initialize()
    embedding_service = EmbeddingService()
    
    # 2. Get uploaded files
    data_dir = project_root / "data" / database_sid / schema_name
    csv_dir = data_dir / "csv_uploads"
    
    def read_csv(filename):
        path = csv_dir / filename
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Remove BOM
            if content.startswith('\ufeff'):
                content = content[1:]
            import csv
            import io
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)

    print("Reading CSVs...")
    table_info_data = read_csv("table_info_template.csv")
    common_columns_data = read_csv("common_columns_template.csv")
    code_definitions_data = read_csv("code_definitions_template.csv")
    
    if not table_info_data:
        print("✗ Could not find table_info_template.csv")
        return

    # 3. Connect to DB to get schema
    sys.path.append(str(project_root / "mcp"))
    from credentials_manager import CredentialsManager
    from oracle_connector import OracleConnector
    
    cm = CredentialsManager(credentials_dir=str(project_root / "data" / "credentials"))
    creds = cm.load_credentials(database_sid)
    oracle = OracleConnector(**creds)
    
    print(f"Connecting to DB {database_sid}...")
    if not oracle.connect():
        print("✗ DB Connection failed")
        return
    
    print("Extracting DB schema...")
    # This might take time
    tables = oracle.extract_tables(schema_name)
    print(f"Found {len(tables)} tables in DB")
    
    # Simple match check
    csv_tables = [r['table_name'] for r in table_info_data if r.get('table_name')]
    matched = set(tables) & set(csv_tables)
    print(f"Matched {len(matched)} tables between CSV and DB")
    
    if not matched:
        print("✗ No tables matched. Check table names or schema.")
        oracle.disconnect()
        return

    # 4. Process (simplified version of metadata.py logic)
    # We'll just do a few tables for testing if it's too many
    to_process = list(matched)[:5]
    print(f"Processing first {len(to_process)} tables: {to_process}")
    
    # ... (skipping actual loop for now, just diagnostic)
    oracle.disconnect()
    print("Done (Diagnostic only)")

if __name__ == "__main__":
    asyncio.run(main())
