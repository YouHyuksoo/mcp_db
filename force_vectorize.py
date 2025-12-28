print("Starting Super Vectorization Script...")
import os
import sys
import asyncio
import csv
import io
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(r"d:\Project\mcp_db")

# Setup logs
log_file = project_root / "vector_log.txt"
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("SuperVector")
print(f"Logging to {log_file}")

os.chdir(project_root)
load_dotenv(project_root / ".env")

# Project imports
sys.path.append(str(project_root / "backend"))
sys.path.append(str(project_root / "mcp"))

from app.core.vector_store import VectorStore
from app.core.embedding_service import EmbeddingService
from credentials_manager import CredentialsManager
from oracle_connector import OracleConnector

database_sid = "SMVNPDBext"
schema_name = "INFINITY21_JSMES"

def generate_document_text(table_info: dict, columns: list, pks: list) -> str:
    """메타데이터 추출용 텍스트 생성 (metadata.py logic)"""
    lines = []
    lines.append(f"Table Name: {table_info.get('table_name', '')}")
    lines.append(f"Description: {table_info.get('table_comment', '')}")
    lines.append(f"Korean Name: {table_info.get('korean_name', '')}")
    
    if pks:
        lines.append(f"Primary Keys: {', '.join(pks)}")
    
    lines.append("Columns:")
    for col in columns:
        col_name = col.get('COLUMN_NAME', col.get('column_name', ''))
        col_comment = col.get('COMMENTS', col.get('column_comment', ''))
        lines.append(f"- {col_name}: {col_comment}")
    
    return "\n".join(lines)

async def run_vectorization():
    logger.info(f"Step 1: Initializing services for {database_sid}...")
    vector_store = VectorStore()
    await vector_store.initialize()
    embedding_service = EmbeddingService()
    
    # Check current count
    try:
        coll = vector_store.client.get_collection("oracle_metadata")
        count_before = coll.count()
        logger.info(f"Current items in oracle_metadata: {count_before}")
    except:
        logger.error("Could not access oracle_metadata collection")
        return

    logger.info("Step 2: Loading CSV data...")
    data_dir = project_root / "data" / database_sid / schema_name / "csv_uploads"
    table_csv = data_dir / "table_info_template.csv"
    
    if not table_csv.exists():
        logger.error(f"CSV not found at {table_csv}")
        return
        
    table_info_data = []
    # UTF-8-SIG to handle BOM
    with open(table_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        table_info_data = list(reader)
    
    logger.info(f"Loaded {len(table_info_data)} tables from CSV")
    
    logger.info("Step 3: Connecting to Oracle DB to fetch schema...")
    cm = CredentialsManager(credentials_dir=str(project_root / "data" / "credentials"))
    creds = cm.load_credentials(database_sid)
    oracle = OracleConnector(**creds)
    
    if not oracle.connect():
        logger.error("Oracle DB connection failed")
        return
    
    try:
        processed_count = 0
        for table_row in table_info_data:
            table_name = table_row.get('table_name', '').strip().upper()
            if not table_name: continue
            
            logger.info(f"Processing table: {table_name}")
            try:
                # Get columns and PKs from DB
                columns = oracle.extract_table_columns(schema_name, table_name)
                if not columns:
                    logger.warning(f"No columns found for {table_name}, skipping.")
                    continue
                    
                pks = oracle.extract_primary_keys(schema_name, table_name)
                
                # Combine metadata (simplified)
                full_metadata = {
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "table_comment": table_row.get('table_comment', ''),
                    "korean_name": table_row.get('korean_name', ''),
                    "description": table_row.get('table_comment', ''),  # Both for compatibility
                    "columns": json.dumps(columns),
                    "primary_keys": json.dumps(pks)
                }
                
                # Generate text and embed
                doc_text = generate_document_text(table_row, columns, pks)
                embedding = embedding_service.embed_text(doc_text)
                
                # Add to Vector DB
                # Note: VectorStore.add_metadata expects (table_id, summary_text, embedding, metadata)
                table_id = f"{database_sid}:{schema_name}:{table_name}"
                vector_store.add_metadata(table_id, doc_text, embedding, full_metadata)
                
                processed_count += 1
                if processed_count % 10 == 0:
                    logger.info(f"--- Processed {processed_count} tables ---")
                    
            except Exception as e:
                logger.error(f"Error processing {table_name}: {e}")
                
        logger.info(f"COMPLETED: Total {processed_count} tables vectorized.")
        
    finally:
        oracle.disconnect()

if __name__ == "__main__":
    asyncio.run(run_vectorization())
