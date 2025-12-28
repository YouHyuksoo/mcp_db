import chromadb
from pathlib import Path

project_root = Path(r"d:\Project\mcp_db")
persist_directory = str(project_root / "data" / "vector_db")

client = chromadb.PersistentClient(path=persist_directory)
col = client.get_collection("oracle_metadata")
results = col.get()
metadatas = results['metadatas']
sids = set(m.get('database_sid') for m in metadatas)
print(f"Databases in oracle_metadata: {sids}")
