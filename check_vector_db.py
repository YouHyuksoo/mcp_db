import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

# Path to vector db
project_root = Path(r"d:\Project\mcp_db")
persist_directory = str(project_root / "data" / "vector_db")

client = chromadb.PersistentClient(
    path=persist_directory,
    settings=Settings(anonymized_telemetry=False)
)

print(f"Checking collections in {persist_directory}...")
collections = client.list_collections()
for col in collections:
    print(f"Collection: {col.name}, Count: {col.count()}")
    if col.name == "oracle_metadata":
        results = col.get(where={"database_sid": "SMVNPDBext"})
        print(f"  - SMVNPDBext count: {len(results['ids'])}")
        if results['ids']:
            print(f"  - First few IDs: {results['ids'][:5]}")
