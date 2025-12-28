import sys
import os

# 환경 변수 설정
os.environ['ENCRYPTION_KEY'] = 'vbyI1_o9ho1Ayv_bTsLXdpEWqGnDdIgMGDSKMDLHHNU='

sys.path.insert(0, 'D:\\Project\\mcp_db\\mcp')

from credentials_manager import CredentialsManager
from oracle_connector import OracleConnector

try:
    # Credentials 로드
    cm = CredentialsManager('D:\\Project\\mcp_db\\data\\credentials')
    creds = cm.load_credentials('SMVNPDBext')
    
    # DB 연결
    connector = OracleConnector(
        host=creds['host'],
        port=creds['port'],
        service_name=creds['service_name'],
        user=creds['user'],
        password=creds['password']
    )
    
    connector.connect()
    
    # View 목록 조회
    sql = """
    SELECT view_name
    FROM all_views
    WHERE owner = :owner
    ORDER BY view_name
    """
    
    result = connector.execute_query(sql, {'owner': creds['user']})
    
    print(f"=== {creds['user']} 스키마의 View 목록 ===\n")
    
    if result:
        for i, row in enumerate(result, 1):
            print(f"{i:3d}. {row[0]}")
        print(f"\n총 {len(result)}개의 View가 있습니다.")
    else:
        print("View가 없습니다.")
    
    connector.disconnect()
    
except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
