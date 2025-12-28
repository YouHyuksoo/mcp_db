import csv
import json
import os
import sys

# Windows console encoding fix
sys.stdout.reconfigure(encoding='utf-8')

COMMON_URI = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads\common_columns_template.csv'
CODE_URI = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads\code_definitions_template.csv'
OUTPUT_URI = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads\column_definitions.csv'

def read_csv(path):
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                # Check header first line without BOM
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {path} with {enc}: {e}")
    print(f"Failed to read {path}")
    return []

def main():
    print("Reading CSV files...")
    
    if not os.path.exists(COMMON_URI):
        print(f"Error: {COMMON_URI} not found")
        return
        
    common_rows = read_csv(COMMON_URI)
    code_rows = read_csv(CODE_URI)
    
    print(f"Loaded {len(common_rows)} common definitions, {len(code_rows)} code definitions")
    
    # Process Code Definitions
    code_map = {}
    for row in code_rows:
        cname = row.get('column_name', '').strip()
        if not cname: continue
        
        if cname not in code_map:
            code_map[cname] = {}
        
        val = row.get('code_value', '')
        label = row.get('code_label', '')
        if val:
            code_map[cname][val] = label
            
    # Process Common Columns
    final_data = {} # column_name -> {korean_name, description, code_values}
    
    for row in common_rows:
        cname = row.get('column_name', '').strip()
        if not cname: continue
        
        final_data[cname] = {
            'column_name': cname,
            'korean_name': row.get('korean_name', ''),
            'description': row.get('description', ''),
            'code_values': json.dumps(code_map.get(cname, {}), ensure_ascii=False) if cname in code_map else ''
        }
        
    # Add items from code_map that weren't in common_rows (if any)
    for cname, codes in code_map.items():
        if cname not in final_data:
            final_data[cname] = {
                'column_name': cname,
                'korean_name': '',
                'description': '',
                'code_values': json.dumps(codes, ensure_ascii=False)
            }
            
    # Write Output
    print(f"Writing {len(final_data)} column definitions to {OUTPUT_URI}...")
    try:
        with open(OUTPUT_URI, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['column_name', 'korean_name', 'description', 'code_values'])
            writer.writeheader()
            writer.writerows(final_data.values())
        print("Success: column_definitions.csv generated.")
    except Exception as e:
        print(f"Error writing output: {e}")

if __name__ == '__main__':
    main()
