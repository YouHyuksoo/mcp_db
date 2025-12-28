import chardet
from pathlib import Path

csv_path = Path(r"d:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads\table_info_template.csv")

with open(csv_path, 'rb') as f:
    rawdata = f.read(10000)
    result = chardet.detect(rawdata)
    with open("encoding_result.txt", "w") as out:
        out.write(str(result))
