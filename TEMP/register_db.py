import sys
import os
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, 'D:\\Project\\mcp_db')
os.chdir('D:\\Project\\mcp_db')

# .env 파일 로드
load_dotenv()

# 환경 변수 확인
encryption_key = os.getenv('ENCRYPTION_KEY')
print(f'ENCRYPTION_KEY 로드: {encryption_key[:20]}...' if encryption_key else 'ENCRYPTION_KEY 없음')

from mcp.credentials_manager import CredentialsManager

try:
    # CredentialsManager 초기화
    manager = CredentialsManager(credentials_dir='./data/credentials')
    print('✅ CredentialsManager 초기화 성공')
    
    # DB 접속 정보
    credentials = {
        'host': '121.78.112.214',
        'port': 1521,
        'service_name': 'XEPDB1',
        'user': 'INFINITY21_JSFMS',
        'password': 'INFINITY21_JSFMS'
    }
    
    # DB 등록
    result = manager.save_credentials(
        database_sid='FMS-JSIDC-XEPDB1',
        credentials=credentials
    )
    
    if result:
        print('✅ DB 등록 성공: FMS-JSIDC-XEPDB1')
        print(f'저장 위치: data/credentials/FMS-JSIDC-XEPDB1.json.enc')
    else:
        print('❌ DB 등록 실패')
        
except Exception as e:
    print(f'❌ 에러 발생: {e}')
    import traceback
    traceback.print_exc()
