import os
import sys

# Force unbuffered stdout
sys.stdout.reconfigure(encoding='utf-8')

print("Start Debug")
path = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads\common_columns_template.csv'
print(f"Checking path: {path}")

if os.path.exists(path):
    print("Path exists.")
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            print("Opened file.")
            content = f.read(100)
            print(f"Content head: {content}")
    except Exception as e:
        print(f"Error reading: {e}")
else:
    print("Path does NOT exist.")

print("Done Debug")
