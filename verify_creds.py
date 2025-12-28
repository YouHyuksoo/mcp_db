import os
import sys
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(r"d:\Project\mcp_db")
load_dotenv(project_root / ".env")

# Add mcp to path for CredentialsManager
sys.path.append(str(project_root / "mcp"))
from credentials_manager import CredentialsManager

credentials_dir = str(project_root / "data" / "credentials")
cm = CredentialsManager(credentials_dir=credentials_dir)

try:
    creds = cm.load_credentials("SMVNPDBext")
    # Hide password for safety but show other info
    safe_creds = {k: v for k, v in creds.items() if k != 'password'}
    print(f"CREDENTIALS_FOUND: {safe_creds}")
except Exception as e:
    print(f"CREDENTIALS_ERROR: {e}")
