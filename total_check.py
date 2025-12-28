import os
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings

project_root = Path(r"d:\Project\mcp_db")
persist_directory = str(project_root / "data" / "vector_db")

client = chromadb.PersistentClient(path=persist_directory)
print(f"Total collections: {len(client.list_collections())}")
for col in client.list_collections():
    print(f"Collection: {col.name}, Items: {col.count()}")
