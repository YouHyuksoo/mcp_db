import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
project_root = Path(r"d:\Project\mcp_db")
load_dotenv(project_root / ".env")

encryption_key = os.getenv('ENCRYPTION_KEY')
if encryption_key:
    print(f"ENCRYPTION_KEY_FOUND: {encryption_key[:5]}...")
else:
    print("ENCRYPTION_KEY_NOT_FOUND")
