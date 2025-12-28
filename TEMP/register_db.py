import sys
sys.path.insert(0, 'D:\\Project\\mcp_db\\mcp')

from credentials_manager import CredentialsManager

cm = CredentialsManager('D:\\Project\\mcp_db\\data\\credentials')

credentials = {
    'host': '61.106.96.94',
    'port': 1521,
    'service_name': 'xe',
    'user': 'INFINITY21_JSMES',
    'password': 'INFINITY21_JSMES'
}

result = cm.save_credentials('ESDBext', credentials)

if result:
    print('✓ ESDBext 데이터베이스가 성공적으로 등록되었습니다.')
    print(f'  - Host: {credentials["host"]}')
    print(f'  - Port: {credentials["port"]}')
    print(f'  - Service: {credentials["service_name"]}')
    print(f'  - User: {credentials["user"]}')
else:
    print('✗ 데이터베이스 등록에 실패했습니다.')

# 등록된 DB 목록 확인
dbs = cm.list_databases()
print(f'\n현재 등록된 데이터베이스 목록: {dbs}')
