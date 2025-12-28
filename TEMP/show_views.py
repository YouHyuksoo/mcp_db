import sys
sys.path.insert(0, r'D:\Project\mcp_db\mcp')
from credentials_manager import CredentialsManager
from oracle_connector import OracleConnector

# Credentials 로드
creds_dir = r'D:\Project\mcp_db\data\credentials'
creds_mgr = CredentialsManager(credentials_dir=creds_dir)
creds = creds_mgr.load_credentials('FMS-JSIDC-XEPDB1')

# DB 연결
conn = OracleConnector(
    host=creds['host'],
    port=creds['port'],
    service_name=creds['service_name'],
    user=creds['user'],
    password=creds['password']
)

if conn.connect():
    print("✅ DB 연결 성공!")
    
    # 모든 스키마의 View 조회
    query = """
        SELECT 
            OWNER,
            VIEW_NAME,
            TEXT_LENGTH,
            READ_ONLY
        FROM ALL_VIEWS
        WHERE OWNER NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS', 
                            'WMSYS', 'EXFSYS', 'CTXSYS', 'XDB', 'ANONYMOUS', 
                            'ORDSYS', 'ORDDATA', 'MDSYS', 'OLAPSYS')
        ORDER BY OWNER, VIEW_NAME
    """
    
    result = conn.execute_select(query)
    
    if result['status'] == 'success':
        rows = result['rows']
        print(f"\n📋 View 목록 ({len(rows)}개)\n")
        print("=" * 80)
        
        current_owner = None
        for row in rows:
            owner = row['OWNER']
            view_name = row['VIEW_NAME']
            text_length = row['TEXT_LENGTH']
            read_only = row['READ_ONLY']
            
            if current_owner != owner:
                current_owner = owner
                print(f"\n## {owner}\n")
            
            print(f"  - {view_name}")
            print(f"    크기: {text_length} bytes, 읽기전용: {read_only}")
    else:
        print(f"❌ 조회 실패: {result['message']}")
    
    conn.disconnect()
else:
    print("❌ DB 연결 실패")
