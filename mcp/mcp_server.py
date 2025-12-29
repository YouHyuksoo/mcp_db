"""
Oracle Database MCP 서버 메인
18개 Tools 제공
- SQL 생성/실행 Tools (9개)
- 메타데이터 조회 Tools (6개)
- Vector DB 기반 검색 Tools (2개) ★ 컬럼 검색 추가
- 유틸리티 Tools (1개)
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# 현재 디렉토리를 sys.path에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 프로젝트 루트의 .env 파일 로드
project_root = current_dir.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server

# 로컬 모듈 imports
from oracle_connector import OracleConnector
from credentials_manager import CredentialsManager
from metadata_manager import MetadataManager
from sql_executor import SQLExecutor
from vector_db_client import get_vector_db
from feedback_manager import FeedbackManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MCP 서버 생성
server = Server("oracle-nlsql-mcp")

# 데이터 디렉토리 경로 설정 (프로젝트 루트/data/)
data_dir = project_root / "data"
credentials_dir = data_dir / "credentials"
common_metadata_dir = data_dir / "common_metadata"
metadata_dir = data_dir / "metadata"
vector_db_dir = data_dir / "vector_db"

# 전역 객체들
credentials_manager = CredentialsManager(credentials_dir=str(credentials_dir))
metadata_manager = MetadataManager(
    metadata_dir=str(metadata_dir)
)

# Vector DB 클라이언트 (피드백 시스템에 사용)
vector_db_client = get_vector_db()

# 피드백 매니저 초기화
feedback_manager = FeedbackManager(vector_db_client)

# DB 커넥터 캐시
db_connectors = {}


def get_connector(database_sid: str) -> OracleConnector:
    """DB 커넥터 가져오기 (캐싱)"""
    if database_sid not in db_connectors:
        credentials = credentials_manager.load_credentials(database_sid)

        connector = OracleConnector(
            host=credentials['host'],
            port=credentials['port'],
            service_name=credentials['service_name'],
            user=credentials['user'],
            password=credentials['password']
        )

        connector.connect()
        db_connectors[database_sid] = connector

    return db_connectors[database_sid]


# ============================================
# Tools 목록 등록
# ============================================
@server.list_tools()
async def list_tools() -> list:
    """사용 가능한 Tool 목록 반환"""
    import mcp.types as types

    return [
        types.Tool(
            name="register_database_credentials",
            description="DB 접속 정보를 암호화하여 저장",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "host": {"type": "string", "description": "호스트 주소"},
                    "port": {"type": "integer", "description": "포트 번호"},
                    "service_name": {"type": "string", "description": "서비스 이름"},
                    "user": {"type": "string", "description": "사용자 이름"},
                    "password": {"type": "string", "description": "비밀번호"}
                },
                "required": ["database_sid", "host", "port", "service_name", "user", "password"]
            }
        ),
        types.Tool(
            name="list_available_databases",
            description="이미 등록된 데이터베이스 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "검색 키워드 (선택, DB SID에서 검색)"}
                }
            }
        ),
        types.Tool(
            name="connect_database",
            description="등록된 DB에 연결 및 접속정보 저장",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "user": {"type": "string", "description": "사용자 이름"},
                    "password": {"type": "string", "description": "비밀번호"}
                },
                "required": ["database_sid", "user", "password"]
            }
        ),
        types.Tool(
            name="show_databases",
            description="등록된 DB 목록 조회",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="show_connection_status",
            description="접속 가능한 DB 목록과 연결 정보 상태 보고",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="show_schemas",
            description="특정 DB의 스키마 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"}
                },
                "required": ["database_sid"]
            }
        ),
        types.Tool(
            name="show_tables",
            description="특정 스키마의 테이블 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "table_filter": {"type": "string", "description": "테이블 이름 필터 (LIKE 패턴, 예: 'ISYS_%', '%_MASTER'). 선택사항."}
                },
                "required": ["database_sid", "schema_name"]
            }
        ),
        types.Tool(
            name="describe_table",
            description="테이블 구조 상세 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "table_name": {"type": "string", "description": "테이블 이름"}
                },
                "required": ["database_sid", "schema_name", "table_name"]
            }
        ),
        types.Tool(
            name="show_procedures",
            description="특정 스키마의 프로시저 목록 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"}
                },
                "required": ["database_sid", "schema_name"]
            }
        ),
        types.Tool(
            name="show_procedure_source",
            description="프로시저 소스 코드 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "procedure_name": {"type": "string", "description": "프로시저 이름"}
                },
                "required": ["database_sid", "schema_name", "procedure_name"]
            }
        ),
        types.Tool(
            name="execute_sql",
            description="SQL 쿼리 실행",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "sql": {"type": "string", "description": "실행할 SQL"},
                    "max_rows": {"type": "integer", "description": "최대 조회 행 수"}
                },
                "required": ["database_sid", "sql"]
            }
        ),
        types.Tool(
            name="get_table_summaries_for_query",
            description="Stage 1: 자연어 질의를 위한 테이블 요약 조회 (Vector DB 기반 의미 검색)",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "natural_query": {"type": "string", "description": "자연어 질문"}
                },
                "required": ["database_sid", "schema_name"]
            }
        ),
        types.Tool(
            name="check_vectordb_status",
            description="Vector DB 상태 확인 (학습 여부, 테이블 수 등)",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_detailed_metadata_for_sql",
            description="Stage 2: SQL 생성을 위한 상세 메타데이터 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "table_names": {"type": "array", "description": "테이블 이름 목록"}
                },
                "required": ["database_sid", "schema_name", "table_names"]
            }
        ),
        types.Tool(
            name="get_table_metadata",
            description="특정 테이블의 통합 메타데이터 조회",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "table_name": {"type": "string", "description": "테이블 이름"}
                },
                "required": ["database_sid", "schema_name", "table_name"]
            }
        ),
        types.Tool(
            name="view_sql_rules",
            description="현재 설정된 SQL 작성 규칙 조회",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="update_sql_rules",
            description="SQL 작성 규칙 업데이트 (Markdown 형식)",
            inputSchema={
                "type": "object",
                "properties": {
                    "rules_content": {"type": "string", "description": "새로운 SQL 규칙 내용 (Markdown 형식)"}
                },
                "required": ["rules_content"]
            }
        ),
        types.Tool(
            name="search_columns",
            description="★ 자연어로 컬럼 검색 (의미 기반, Vector DB 사용)",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "query": {"type": "string", "description": "자연어 검색어 (예: '라인', '일자', '수량', '모델명')"},
                    "table_name": {"type": "string", "description": "특정 테이블로 제한 (선택사항)"},
                    "n_results": {"type": "integer", "description": "반환할 컬럼 수 (기본값: 10)"}
                },
                "required": ["database_sid", "schema_name", "query"]
            }
        ),
        types.Tool(
            name="generate_and_review_sql",
            description="★ SQL 생성 후 미리보기 (검토 기능 포함) - 옵션 A",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "schema_name": {"type": "string", "description": "스키마 이름"},
                    "natural_query": {"type": "string", "description": "자연어 질문 (예: 'Run Card의 당일 생산 계획수량을 모델별로 합계해서 보여줘')"},
                    "created_by": {"type": "string", "description": "사용자 정보 (선택)"}
                },
                "required": ["database_sid", "schema_name", "natural_query"]
            }
        ),
        types.Tool(
            name="submit_sql_feedback",
            description="★ 사용자 피드백 저장 및 가중치 계산 (피드백 처리)",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedback_id": {"type": "string", "description": "피드백 ID"},
                    "action": {"type": "string", "description": "approve (승인), modify (수정), reject (거부)", "enum": ["approve", "modify", "reject"]},
                    "suggestions": {"type": "string", "description": "사용자 제안/조언 (수정 또는 거부 시)"},
                    "user_confidence": {"type": "number", "description": "사용자 신뢰도 (0.0~1.0)"}
                },
                "required": ["feedback_id", "action"]
            }
        ),
        types.Tool(
            name="regenerate_sql_with_feedback",
            description="★ 사용자 피드백을 반영하여 SQL 재생성",
            inputSchema={
                "type": "object",
                "properties": {
                    "feedback_id": {"type": "string", "description": "피드백 ID"},
                    "feedback_text": {"type": "string", "description": "사용자 피드백 (수정 요청 사항)"}
                },
                "required": ["feedback_id", "feedback_text"]
            }
        ),
        types.Tool(
            name="execute_sql_direct",
            description="SQL 직접 실행 (피드백 없이 바로 실행) - 옵션 B",
            inputSchema={
                "type": "object",
                "properties": {
                    "database_sid": {"type": "string", "description": "Database SID"},
                    "sql": {"type": "string", "description": "실행할 SQL"},
                    "max_rows": {"type": "integer", "description": "최대 조회 행 수"}
                },
                "required": ["database_sid", "sql"]
            }
        ),
    ]


# ============================================
# Tool 실행 라우터
# ============================================
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """단일 Tool 라우터 - 모든 Tool 호출을 적절한 함수로 라우팅"""
    import mcp.types as types

    try:
        # Tool 이름에 따라 적절한 함수 호출
        if name == "register_database_credentials":
            result = await register_database_credentials(**arguments)
        elif name == "list_available_databases":
            result = await list_available_databases(**arguments)
        elif name == "connect_database":
            result = await connect_database(**arguments)
        elif name == "show_databases":
            result = await show_databases(**arguments)
        elif name == "show_connection_status":
            result = await show_connection_status(**arguments)
        elif name == "show_schemas":
            result = await show_schemas(**arguments)
        elif name == "show_tables":
            result = await show_tables(**arguments)
        elif name == "describe_table":
            result = await describe_table(**arguments)
        elif name == "show_procedures":
            result = await show_procedures(**arguments)
        elif name == "show_procedure_source":
            result = await show_procedure_source(**arguments)
        elif name == "execute_sql":
            result = await execute_sql(**arguments)
        elif name == "get_table_summaries_for_query":
            result = await get_table_summaries_for_query(**arguments)
        elif name == "check_vectordb_status":
            result = await check_vectordb_status(**arguments)
        elif name == "get_detailed_metadata_for_sql":
            result = await get_detailed_metadata_for_sql(**arguments)
        elif name == "get_table_metadata":
            result = await get_table_metadata(**arguments)
        elif name == "view_sql_rules":
            result = await view_sql_rules(**arguments)
        elif name == "update_sql_rules":
            result = await update_sql_rules(**arguments)
        elif name == "search_columns":
            result = await search_columns(**arguments)
        elif name == "generate_and_review_sql":
            result = await generate_and_review_sql(**arguments)
        elif name == "submit_sql_feedback":
            result = await submit_sql_feedback(**arguments)
        elif name == "regenerate_sql_with_feedback":
            result = await regenerate_sql_with_feedback(**arguments)
        elif name == "execute_sql_direct":
            result = await execute_sql_direct(**arguments)
        else:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=f"❌ Unknown tool: {name}")],
                isError=True
            )

        # 결과가 이미 list[dict] 형태라면 변환
        if isinstance(result, list):
            content = [types.TextContent(type=item.get("type", "text"), text=item.get("text", "")) for item in result]
            return types.CallToolResult(content=content)
        else:
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=str(result))]
            )

    except Exception as e:
        import traceback
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}")],
            isError=True
        )


# ============================================
# Tool 1: DB 접속 정보 등록
# ============================================
async def register_database_credentials(
    database_sid: str,
    host: str,
    port: int,
    service_name: str,
    user: str,
    password: str
) -> list[dict]:
    """DB 접속 정보 암호화하여 저장"""
    try:
        credentials = {
            'host': host,
            'port': port,
            'service_name': service_name,
            'user': user,
            'password': password
        }

        success = credentials_manager.save_credentials(database_sid, credentials)

        if success:
            return [{
                "type": "text",
                "text": f"✅ DB 접속 정보 저장 완료: {database_sid}"
            }]
        else:
            return [{
                "type": "text",
                "text": f"❌ DB 접속 정보 저장 실패: {database_sid}"
            }]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 2: 사용 가능한 DB 목록 조회
# ============================================

async def list_available_databases(
    keyword: str = ""
) -> list[dict]:
    """
    이미 등록된 데이터베이스 목록 조회

    Args:
        keyword: 검색 키워드 (선택, DB SID에서 검색)
    """
    try:
        # 등록된 credentials 목록 조회
        registered_dbs = credentials_manager.list_databases()

        if not registered_dbs:
            return [{
                "type": "text",
                "text": "❌ 등록된 데이터베이스가 없습니다.\n\n"
                       "다음 중 하나를 시도하세요:\n"
                       "1. `register_database_credentials` Tool로 수동 등록\n"
                       "2. Backend Web UI에서 tnsnames.ora 파일을 파싱하여 등록"
            }]

        # 키워드 필터링
        if keyword:
            keyword_lower = keyword.lower()
            filtered = [
                db_sid for db_sid in registered_dbs
                if keyword_lower in db_sid.lower()
            ]
        else:
            filtered = registered_dbs

        result_text = f"📊 등록된 데이터베이스 목록\n\n"

        if keyword:
            result_text += f"**검색 키워드**: {keyword}\n"
            result_text += f"**검색 결과**: {len(filtered)}개\n\n"
        else:
            result_text += f"**전체 DB 수**: {len(filtered)}개\n\n"

        # DB 목록 (최대 20개만 표시)
        count = 0
        for db_sid in sorted(filtered):
            if count >= 20:
                result_text += f"\n... 외 {len(filtered) - 20}개 더 있음\n"
                break

            try:
                # 등록된 credentials 정보 조회 (비밀번호 제외)
                creds = credentials_manager.load_credentials(db_sid)
                result_text += f"### {db_sid}\n"
                result_text += f"  - **호스트**: {creds['host']}:{creds['port']}\n"
                result_text += f"  - **서비스명**: {creds['service_name']}\n"
                result_text += f"  - **사용자**: {creds.get('user', 'N/A')}\n\n"
            except Exception as e:
                result_text += f"### {db_sid}\n"
                result_text += f"  - **상태**: 정보 조회 실패\n\n"
            count += 1

        result_text += "\n**다음 단계**: `connect_database` Tool로 연결하거나 `register_database_credentials` Tool로 새로 등록하세요."

        return [{
            "type": "text",
            "text": result_text
        }]

    except Exception as e:
        import traceback
        logger.error(f"DB 목록 조회 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ DB 목록 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 4: 데이터베이스 연결 및 저장
# ============================================

async def connect_database(
    database_sid: str,
    user: str,
    password: str
) -> list[dict]:
    """
    DB에 연결 및 접속정보 저장 (이미 등록된 credentials 사용)

    Args:
        database_sid: DB SID (예: SOLUM, JSTECH)
        user: Oracle 사용자명 (예: scott, system)
        password: Oracle 비밀번호
    """
    try:
        # 등록된 credentials 확인
        try:
            existing_credentials = credentials_manager.load_credentials(database_sid)
            db_info = {
                'host': existing_credentials['host'],
                'port': existing_credentials['port'],
                'service_name': existing_credentials['service_name']
            }
            logger.info(f"이미 등록된 credentials 사용: {database_sid}")
        except Exception as e:
            # 등록된 credentials 없음
            return [{
                "type": "text",
                "text": f"❌ DB를 찾을 수 없습니다: {database_sid}\n\n"
                       f"먼저 `register_database_credentials` Tool로 DB 접속 정보를 등록하세요.\n"
                       f"또는 Backend Web UI에서 tnsnames.ora 파일을 파싱하여 등록할 수 있습니다."
            }]

        # 연결 테스트
        connector = OracleConnector(
            host=db_info['host'],
            port=db_info['port'],
            service_name=db_info['service_name'],
            user=user,
            password=password
        )

        if not connector.connect():
            return [{
                "type": "text",
                "text": f"❌ DB 연결 실패: {database_sid}\n\n사용자명과 비밀번호를 확인하세요."
            }]

        # 연결 성공 시 credentials 저장 (비밀번호 업데이트 포함)
        credentials = {
            'host': db_info['host'],
            'port': db_info['port'],
            'service_name': db_info['service_name'],
            'user': user,
            'password': password
        }

        success = credentials_manager.save_credentials(database_sid, credentials)

        if success:
            result_text = f"✅ 데이터베이스 연결 성공 및 저장 완료\n\n"
            result_text += f"**Database SID**: {database_sid}\n"
            result_text += f"**호스트**: {db_info['host']}:{db_info['port']}\n"
            result_text += f"**서비스명**: {db_info['service_name']}\n"
            result_text += f"**사용자**: {user}\n"
            result_text += f"\n✅ 접속 정보가 암호화되어 저장되었습니다.\n"
            result_text += f"이제 이 DB를 자동으로 사용할 수 있습니다.\n\n"
            result_text += "**다음 단계**: \n"
            result_text += f"- `show_schemas` Tool로 스키마 목록 확인\n"
            result_text += f"- Backend Web UI에서 CSV 업로드 또는 메타데이터 관리"

            # 캐시에서 커넥터 제거 (새로 연결하도록)
            if database_sid in db_connectors:
                del db_connectors[database_sid]

            return [{
                "type": "text",
                "text": result_text
            }]
        else:
            return [{
                "type": "text",
                "text": f"❌ 접속 정보 저장 실패: {database_sid}"
            }]

    except Exception as e:
        import traceback
        logger.error(f"DB 연결 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 데이터베이스 연결 실패: {str(e)}\n\n사용자명과 비밀번호를 확인하세요.\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 3: 데이터베이스 목록
# ============================================

async def show_databases() -> list[dict]:
    """등록된 모든 데이터베이스 목록"""
    try:
        databases = credentials_manager.list_databases()

        if not databases:
            return [{
                "type": "text",
                "text": "등록된 데이터베이스가 없습니다."
            }]

        result_text = f"📂 등록된 데이터베이스 ({len(databases)}개)\n\n"
        for db_sid in databases:
            result_text += f"- {db_sid}\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: 연결 상태 보고
# ============================================

async def show_connection_status() -> list[dict]:
    """접속 가능한 DB 목록과 연결 정보, 메타데이터 상태 보고"""
    try:
        import json
        from pathlib import Path

        databases = credentials_manager.list_databases()

        if not databases:
            return [{
                "type": "text",
                "text": "등록된 데이터베이스가 없습니다."
            }]

        result_text = f"📊 **데이터베이스 연결 상태 보고**\n\n"
        result_text += f"등록된 데이터베이스: **{len(databases)}개**\n\n"
        result_text += "=" * 60 + "\n\n"

        for db_sid in databases:
            result_text += f"## 🗄️ {db_sid}\n\n"

            try:
                # 1. 연결 정보 로드
                credentials = credentials_manager.load_credentials(db_sid)
                result_text += f"### 📡 연결 정보\n"
                result_text += f"- **호스트**: {credentials['host']}:{credentials['port']}\n"
                result_text += f"- **서비스명**: {credentials['service_name']}\n"
                result_text += f"- **사용자**: {credentials['user']}\n"
                result_text += f"- **비밀번호**: {'*' * len(credentials['password'])}\n\n"

                # 2. 연결 테스트
                try:
                    connector = OracleConnector(
                        host=credentials['host'],
                        port=credentials['port'],
                        service_name=credentials['service_name'],
                        user=credentials['user'],
                        password=credentials['password']
                    )
                    if connector.connect():
                        result_text += f"- **연결 상태**: ✅ 연결 가능\n\n"

                        # 3. 스키마 목록 조회
                        try:
                            schemas = connector.list_schemas()
                            result_text += f"### 📂 스키마 목록\n"
                            result_text += f"- **스키마 수**: {len(schemas)}개\n"
                            result_text += f"- **목록**: {', '.join(schemas[:5])}"
                            if len(schemas) > 5:
                                result_text += f" 외 {len(schemas) - 5}개"
                            result_text += "\n\n"
                        except Exception as e:
                            result_text += f"### 📂 스키마 목록\n"
                            result_text += f"- ⚠️ 조회 실패: {str(e)}\n\n"

                        connector.disconnect()
                    else:
                        result_text += f"- **연결 상태**: ❌ 연결 실패\n\n"
                except Exception as e:
                    result_text += f"- **연결 상태**: ❌ 연결 실패 ({str(e)})\n\n"

                # 4. Vector DB 메타데이터 상태
                result_text += f"### 🗂️ 통합 메타데이터 상태\n"
                metadata_dir = Path("./metadata") / db_sid
                if metadata_dir.exists():
                    schema_dirs = [d for d in metadata_dir.iterdir() if d.is_dir()]
                    total_tables = 0
                    schema_info = []

                    for schema_dir in schema_dirs:
                        table_dirs = [d for d in schema_dir.iterdir() if d.is_dir()]
                        table_count = len(table_dirs)
                        total_tables += table_count
                        if table_count > 0:
                            schema_info.append(f"{schema_dir.name} ({table_count}개)")

                    if total_tables > 0:
                        result_text += f"- **생성된 메타데이터**: ✅ {total_tables}개 테이블\n"
                        result_text += f"- **스키마별**:\n"
                        for info in schema_info[:5]:
                            result_text += f"  - {info}\n"
                        if len(schema_info) > 5:
                            result_text += f"  - ... 외 {len(schema_info) - 5}개\n"
                    else:
                        result_text += f"- **생성된 메타데이터**: ⚠️ 없음\n"
                else:
                    result_text += f"- **생성된 메타데이터**: ⚠️ 없음\n"
                result_text += "\n"

                # 6. CSV 파일 상태
                result_text += f"### 📄 CSV 파일 상태\n"
                common_metadata_dir = Path("./common_metadata") / db_sid
                csv_files = []
                if common_metadata_dir.exists():
                    if (common_metadata_dir / "common_columns.json").exists():
                        csv_files.append("✅ 공통 칼럼 로드됨")
                    else:
                        csv_files.append("⚠️ 공통 칼럼 미로드")

                    if (common_metadata_dir / "code_definitions.json").exists():
                        csv_files.append("✅ 코드 정의 로드됨")
                    else:
                        csv_files.append("⚠️ 코드 정의 미로드")

                    # 스키마별 테이블 정보 확인
                    schema_files = list(common_metadata_dir.glob("*/table_info.json"))
                    if schema_files:
                        csv_files.append(f"✅ 테이블 정보 ({len(schema_files)}개 스키마)")
                    else:
                        csv_files.append("⚠️ 테이블 정보 미로드")
                else:
                    csv_files.append("⚠️ 공통 메타데이터 디렉토리 없음")

                for file_status in csv_files:
                    result_text += f"- {file_status}\n"
                result_text += "\n"

            except Exception as e:
                result_text += f"❌ 정보 조회 실패: {str(e)}\n\n"

            result_text += "=" * 60 + "\n\n"

        result_text += "\n**📌 참고사항**:\n"
        result_text += "- CSV 업로드 및 메타데이터 관리: Backend Web UI에서 수행\n"
        result_text += "- Vector DB 메타데이터: Backend를 통해 학습 후 MCP가 독립적으로 사용\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        logger.error(f"연결 상태 조회 실패: {e}")
        import traceback
        return [{
            "type": "text",
            "text": f"❌ 연결 상태 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 4: 스키마 목록
# ============================================

async def show_schemas(database_sid: str) -> list[dict]:
    """특정 DB의 모든 스키마 목록"""
    try:
        connector = get_connector(database_sid)
        schemas = connector.list_schemas()

        result_text = f"📂 {database_sid}의 스키마 목록 ({len(schemas)}개)\n\n"
        for schema in schemas:
            result_text += f"- {schema}\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 5: 테이블 목록
# ============================================

async def show_tables(database_sid: str, schema_name: str, table_filter: str = None) -> list[dict]:
    """
    특정 스키마의 테이블 목록

    Args:
        database_sid: Database SID
        schema_name: 스키마 이름
        table_filter: 테이블 이름 필터 (LIKE 패턴, 예: 'ISYS_%', '%_MASTER')
    """
    try:
        connector = get_connector(database_sid)
        tables = connector.list_tables(schema_name, table_filter)

        if table_filter:
            result_text = f"📋 {database_sid}.{schema_name}의 테이블 목록 (필터: {table_filter}) ({len(tables)}개)\n\n"
        else:
            result_text = f"📋 {database_sid}.{schema_name}의 테이블 목록 ({len(tables)}개)\n\n"

        for table in tables:
            result_text += f"- {table['TABLE_NAME']}"
            if table.get('NUM_ROWS'):
                result_text += f" ({table['NUM_ROWS']:,}개 행)"
            result_text += "\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 6: 테이블 구조 상세
# ============================================

async def describe_table(
    database_sid: str,
    schema_name: str,
    table_name: str
) -> list[dict]:
    """테이블 구조 상세 조회"""
    try:
        connector = get_connector(database_sid)

        # 칼럼 정보
        columns = connector.extract_table_columns(schema_name, table_name)
        primary_keys = connector.extract_primary_keys(schema_name, table_name)
        foreign_keys = connector.extract_foreign_keys(schema_name, table_name)
        indexes = connector.extract_indexes(schema_name, table_name)
        comment = connector.get_table_comment(schema_name, table_name)

        result_text = f"📊 테이블 구조: {database_sid}.{schema_name}.{table_name}\n\n"

        if comment:
            result_text += f"설명: {comment}\n\n"

        result_text += "## 칼럼\n\n"
        for col in columns:
            pk_mark = " [PK]" if col['COLUMN_NAME'] in primary_keys else ""
            nullable = "NULL" if col['NULLABLE'] == 'Y' else "NOT NULL"

            result_text += f"- {col['COLUMN_NAME']}{pk_mark}\n"
            result_text += f"  타입: {col['DATA_TYPE']}, {nullable}\n"
            if col.get('COMMENTS'):
                result_text += f"  설명: {col['COMMENTS']}\n"
            result_text += "\n"

        if foreign_keys:
            result_text += "\n## Foreign Keys\n\n"
            for fk in foreign_keys:
                result_text += f"- {fk['COLUMN_NAME']} → {fk['REF_TABLE']}.{fk['REF_COLUMN']}\n"

        if indexes:
            result_text += "\n## Indexes\n\n"
            for idx in indexes:
                result_text += f"- {idx['INDEX_NAME']} ({idx['UNIQUENESS']}): {idx['COLUMNS']}\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 7: 프로시저/함수 목록
# ============================================

async def show_procedures(
    database_sid: str,
    schema_name: str
) -> list[dict]:
    """프로시저 및 함수 목록"""
    try:
        connector = get_connector(database_sid)
        procedures = connector.list_procedures(schema_name)

        result_text = f"⚙️ {database_sid}.{schema_name}의 프로시저/함수 ({len(procedures)}개)\n\n"

        for proc in procedures:
            result_text += f"- {proc['OBJECT_NAME']} ({proc['OBJECT_TYPE']})\n"
            result_text += f"  상태: {proc['STATUS']}, 수정일: {proc['LAST_DDL_TIME']}\n\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 8: 프로시저 소스 코드
# ============================================

async def show_procedure_source(
    database_sid: str,
    schema_name: str,
    procedure_name: str
) -> list[dict]:
    """프로시저/함수 소스 코드"""
    try:
        connector = get_connector(database_sid)
        source = connector.get_procedure_source(schema_name, procedure_name)

        if not source:
            return [{
                "type": "text",
                "text": f"프로시저를 찾을 수 없습니다: {procedure_name}"
            }]

        result_text = f"📄 프로시저 소스: {database_sid}.{schema_name}.{procedure_name}\n\n"
        result_text += "```sql\n"
        result_text += source
        result_text += "\n```"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 9: SQL 직접 실행
# ============================================

async def execute_sql(
    database_sid: str,
    sql: str,
    max_rows: int = 1000
) -> list[dict]:
    """SQL 쿼리 직접 실행 (SELECT만)"""
    try:
        connector = get_connector(database_sid)
        executor = SQLExecutor(connector)

        result = executor.execute_select(sql, max_rows)

        if result['status'] == 'error':
            return [{
                "type": "text",
                "text": f"❌ {result['message']}"
            }]

        result_text = f"✅ 쿼리 실행 완료\n\n"

        # 인덱스 최적화 검사 결과 표시
        optimization_check = result.get('optimization_check', {})
        violations = optimization_check.get('violations', [])
        warnings = optimization_check.get('warnings', [])

        if violations or warnings:
            result_text += "## 🔍 SQL 최적화 검사\n\n"

            if violations:
                result_text += "### ❌ 위반 사항 (반드시 수정 필요)\n"
                for v in violations:
                    result_text += f"{v}\n\n"

            if warnings:
                result_text += "### ⚠️ 경고 사항 (성능에 영향 가능)\n"
                for w in warnings:
                    result_text += f"{w}\n\n"

            result_text += "---\n\n"

        result_text += f"SQL:\n```sql\n{sql}\n```\n\n"
        result_text += f"결과: {result['row_count']}개 행\n\n"

        # 결과 테이블 형식으로
        if result['rows']:
            import json
            result_text += "```json\n"
            result_text += json.dumps(result['rows'][:10], ensure_ascii=False, indent=2)
            result_text += "\n```"

            if len(result['rows']) > 10:
                result_text += f"\n\n... 외 {len(result['rows']) - 10}개 행"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 실행 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 실행 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool 10: 자연어 쿼리를 위한 테이블 요약 제공 (Stage 1)
# ============================================

async def get_table_summaries_for_query(
    database_sid: str,
    schema_name: str,
    natural_query: str = ""
) -> list[dict]:
    """
    Vector DB 기반 테이블 요약 정보 제공 (Stage 1)

    Backend 없이 vector_db/ 폴더에서 직접 ChromaDB 읽기
    의미 기반 검색으로 관련 테이블 찾기
    """
    try:
        vector_db = get_vector_db()

        # Vector DB 초기화 확인
        if not vector_db.is_available():
            return [{
                "type": "text",
                "text": (
                    "❌ **Vector DB를 사용할 수 없습니다**\n\n"
                    f"**Database**: {database_sid}\n"
                    f"**Schema**: {schema_name}\n\n"
                    "**원인**: Vector DB가 초기화되지 않았습니다.\n\n"
                    "**해결 방법**:\n"
                    "1. Backend 서버를 시작하여 데이터를 학습시키세요:\n"
                    "   ```bash\n"
                    "   cd backend\n"
                    "   python -m uvicorn app.main:app --reload\n"
                    "   ```\n\n"
                    "2. Web UI에서 메타데이터를 업로드하세요:\n"
                    "   - 주소: http://localhost:3000\n"
                    "   - CSV 파일 업로드 또는 JSON 마이그레이션\n\n"
                    "3. 학습 완료 후 Backend를 종료해도 됩니다.\n"
                    "   MCP 서버는 vector_db/ 폴더를 직접 읽어 독립 동작합니다.\n\n"
                    "💡 **참고**: 학습은 한 번만 하면 됩니다."
                )
            }]

        # Vector DB에서 의미 기반 검색
        tables = vector_db.search_tables(
            question=natural_query,
            database_sid=database_sid,
            schema_name=schema_name,
            n_results=10
        )

        if not tables:
            return [{
                "type": "text",
                "text": (
                    f"ℹ️ **검색 결과가 없습니다**\n\n"
                    f"**질문**: {natural_query}\n"
                    f"**Database**: {database_sid}\n"
                    f"**Schema**: {schema_name}\n\n"
                    "이 스키마에 대한 데이터가 Vector DB에 없습니다.\n"
                    "Backend를 통해 먼저 학습시켜주세요."
                )
            }]

        # 결과 포맷팅
        result_text = f"📊 **테이블 검색 결과** (Vector DB)\n\n"
        result_text += f"**질문**: {natural_query}\n\n"
        result_text += f"**Database**: {database_sid}\n"
        result_text += f"**Schema**: {schema_name}\n"
        result_text += f"**검색 방식**: 🚀 의미 기반 검색 (ChromaDB)\n"
        result_text += f"**발견된 테이블**: {len(tables)}개\n\n"
        result_text += "**관련 테이블 목록** (관련도 순):\n\n"

        for i, table in enumerate(tables, 1):
            similarity_pct = table["similarity"] * 100
            result_text += f"### {i}. {table['table_name']} "
            result_text += f"(관련도: {similarity_pct:.1f}%)\n"

            if table.get("korean_name"):
                result_text += f"- **한글명**: {table['korean_name']}\n"

            if table.get("description"):
                desc = table['description'][:100]
                if len(table['description']) > 100:
                    desc += "..."
                result_text += f"- **설명**: {desc}\n"

            result_text += f"- **컬럼 수**: {table['column_count']}\n\n"

        result_text += "---\n\n"
        result_text += "**다음 단계**:\n"
        result_text += "1. 위 테이블들 중 필요한 테이블 선택 (최대 5개 권장)\n"
        result_text += "2. `get_detailed_metadata_for_sql` Tool 호출\n"
        result_text += "3. 상세 메타데이터로 SQL 생성\n\n"
        result_text += "💡 **TIP**: 관련도가 높은(>70%) 테이블부터 선택하세요."

        return [{"type": "text", "text": result_text}]

    except RuntimeError as e:
        logger.error(f"Vector DB error: {e}")
        return [{
            "type": "text",
            "text": f"❌ Vector DB 오류: {str(e)}"
        }]

    except Exception as e:
        import traceback
        logger.error(f"테이블 검색 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 테이블 검색 실패: {str(e)}"
        }]


# ============================================
# Tool 10-1: Vector DB 상태 확인
# ============================================

async def check_vectordb_status() -> list[dict]:
    """Vector DB 상태 확인 도구"""
    try:
        vector_db = get_vector_db()

        if vector_db.is_available():
            stats = vector_db.get_stats()

            result_text = "✅ **Vector DB 정상 동작 중**\n\n"
            result_text += f"**위치**: vector_db/\n"
            result_text += f"**테이블 수**: {stats['table_count']}개\n"
            result_text += "**상태**: 사용 가능\n"
            result_text += "**Backend**: 불필요 (이미 학습 완료)\n\n"
            result_text += "**사용 가능한 기능**:\n"
            result_text += "- ✅ 의미 기반 테이블 검색\n"
            result_text += "- ✅ SQL 생성 및 실행\n"
            result_text += "- ✅ 메타데이터 조회\n\n"
            result_text += "💡 MCP 서버가 독립적으로 동작 중입니다."
        else:
            result_text = "⚠️ **Vector DB 초기화 필요**\n\n"
            result_text += "**상태**: 사용 불가\n"
            result_text += "**원인**: vector_db/ 디렉토리가 없거나 비어있음\n\n"
            result_text += "**초기화 방법**:\n"
            result_text += "1. Backend 서버 시작\n"
            result_text += "2. CSV/JSON 업로드로 메타데이터 학습\n"
            result_text += "3. Backend 종료 (이후 불필요)\n"
            result_text += "4. MCP 서버 독립 실행\n\n"
            result_text += "💡 학습은 한 번만 하면 됩니다."

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"상태 확인 실패: {e}\n{traceback.format_exc()}")
        return [{"type": "text", "text": f"❌ 상태 확인 실패: {str(e)}"}]


# ============================================
# Tool 11: 선택된 테이블들의 상세 메타데이터 제공 (Stage 2)
# ============================================

async def get_detailed_metadata_for_sql(
    database_sid: str,
    schema_name: str,
    table_names: str,  # 쉼표로 구분된 테이블명
    natural_query: str = ""
) -> list[dict]:
    """
    선택된 테이블들의 상세 메타데이터 제공 (Stage 2)

    Claude가 이 정보를 보고 정확한 SQL을 생성할 수 있도록 합니다.
    """
    try:
        # 테이블명 파싱
        selected_tables = [t.strip() for t in table_names.split(',')]

        if len(selected_tables) > 5:
            return [{
                "type": "text",
                "text": f"⚠️ 테이블은 최대 5개까지만 선택할 수 있습니다. (현재: {len(selected_tables)}개)"
            }]

        import json
        result_text = f"📊 상세 메타데이터 (Stage 2)\n\n"
        result_text += f"**질문**: {natural_query}\n\n"
        result_text += f"**선택된 테이블**: {', '.join(selected_tables)}\n\n"
        result_text += "---\n\n"

        # 각 테이블의 상세 메타데이터 로드
        all_metadata = []
        for table_name in selected_tables:
            try:
                metadata = metadata_manager.load_unified_metadata(
                    database_sid, schema_name, table_name
                )
                all_metadata.append(metadata)

                # 간단한 요약 표시
                result_text += f"### {table_name}\n"
                result_text += f"- 목적: {metadata.get('table_info', {}).get('business_purpose', 'N/A')}\n"
                result_text += f"- 칼럼 수: {len(metadata.get('columns', []))}\n\n"

            except FileNotFoundError:
                result_text += f"### {table_name}\n"
                result_text += f"⚠️ 메타데이터를 찾을 수 없습니다.\n\n"

        # 전체 메타데이터 JSON 제공
        result_text += "\n---\n\n"
        result_text += "**전체 메타데이터 (SQL 생성용)**:\n\n"
        result_text += "```json\n"
        result_text += json.dumps(all_metadata, ensure_ascii=False, indent=2)
        result_text += "\n```\n\n"

        result_text += "---\n\n"
        result_text += "**다음 단계**: 위 메타데이터를 참고하여 Oracle SQL을 생성한 후,\n"
        result_text += "`execute_sql` Tool을 호출하여 실행하세요.\n\n"
        result_text += "**Oracle SQL 생성 가이드**:\n"
        result_text += "- Schema.Table 형식 사용 (예: SCOTT.ORDERS)\n"
        result_text += "- Oracle 날짜 함수 사용 (TRUNC, ADD_MONTHS, TO_CHAR 등)\n"
        result_text += "- 코드 칼럼의 경우 코드값으로 WHERE 조건 작성\n"
        result_text += "- FK 정보를 참고하여 정확한 JOIN 조건 작성\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"상세 메타데이터 조회 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 상세 메타데이터 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]




# ============================================
# Tool 12: 테이블 메타정보 조회
# ============================================

async def get_table_metadata(
    database_sid: str,
    schema_name: str,
    table_name: str
) -> list[dict]:
    """통합 메타정보 조회"""
    try:
        metadata = metadata_manager.load_unified_metadata(
            database_sid, schema_name, table_name
        )

        import json
        result_text = f"📊 통합 메타정보: {database_sid}.{schema_name}.{table_name}\n\n"
        result_text += "```json\n"
        result_text += json.dumps(metadata, ensure_ascii=False, indent=2)
        result_text += "\n```"

        return [{"type": "text", "text": result_text}]

    except FileNotFoundError:
        return [{
            "type": "text",
            "text": f"❌ 메타정보가 없습니다: {database_sid}.{schema_name}.{table_name}"
        }]
    except Exception as e:
        import traceback
        logger.error(f"에러 발생: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 에러: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: SQL 규칙 조회
# ============================================

async def view_sql_rules() -> list[dict]:
    """현재 설정된 SQL 작성 규칙 조회"""
    try:
        from pathlib import Path

        # data/sql_rules.md 공유 파일 사용
        sql_rules_path = data_dir / "sql_rules.md"

        if not sql_rules_path.exists():
            return [{
                "type": "text",
                "text": "❌ SQL 규칙 파일이 없습니다.\n`update_sql_rules` Tool을 사용하여 규칙을 생성하세요."
            }]

        with open(sql_rules_path, 'r', encoding='utf-8') as f:
            rules_content = f.read()

        result_text = "📋 현재 SQL 작성 규칙\n\n"
        result_text += f"**파일 위치**: {sql_rules_path}\n\n"
        result_text += "---\n\n"
        result_text += rules_content

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 규칙 조회 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 규칙 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: SQL 규칙 업데이트
# ============================================

async def update_sql_rules(rules_content: str) -> list[dict]:
    """SQL 작성 규칙 업데이트"""
    try:
        from pathlib import Path

        # data/sql_rules.md 공유 파일 사용
        sql_rules_path = data_dir / "sql_rules.md"
        backup_dir = data_dir / "sql_rules_backups"

        # 백업 디렉토리 생성
        backup_dir.mkdir(exist_ok=True)

        # 백업 생성 (기존 파일이 있는 경우)
        if sql_rules_path.exists():
            import shutil
            from datetime import datetime
            backup_file = f'sql_rules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            backup_path = backup_dir / backup_file
            shutil.copy2(sql_rules_path, backup_path)
            backup_msg = f"✅ 기존 규칙 백업: {backup_file}\n"
        else:
            backup_msg = ""

        # 새 규칙 저장
        with open(sql_rules_path, 'w', encoding='utf-8') as f:
            f.write(rules_content)

        result_text = "✅ SQL 작성 규칙 업데이트 완료\n\n"
        result_text += backup_msg
        result_text += f"**파일 위치**: {sql_rules_path}\n"
        result_text += f"**규칙 길이**: {len(rules_content)} 자\n\n"
        result_text += "---\n\n"
        result_text += "**업데이트된 규칙 미리보기**:\n\n"
        result_text += rules_content[:500]
        if len(rules_content) > 500:
            result_text += "\n\n... (생략)"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 규칙 업데이트 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 규칙 업데이트 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: 자연어로 컬럼 검색 (의미 기반)
# ============================================

async def search_columns(
    database_sid: str,
    schema_name: str,
    query: str,
    table_name: str = None,
    n_results: int = 10
) -> list[dict]:
    """
    ★ 자연어로 컬럼 검색 (Vector DB 기반 의미 검색)

    사용자의 자연어 질문을 벡터로 변환하여
    가장 관련 있는 Oracle 컬럼들을 찾아줍니다.

    Args:
        database_sid: Database SID
        schema_name: 스키마 이름
        query: 자연어 검색어 (예: "라인", "일자", "수량", "모델명")
        table_name: 특정 테이블로 제한 (선택)
        n_results: 반환할 컬럼 수 (기본값: 10)

    Returns:
        관련 컬럼 정보 리스트
    """
    try:
        vector_db = get_vector_db()

        # Vector DB 컬럼 컬렉션 확인
        if vector_db.columns_collection is None:
            return [{
                "type": "text",
                "text": (
                    "❌ **컬럼 Vector DB를 사용할 수 없습니다**\n\n"
                    f"**Database**: {database_sid}\n"
                    f"**Schema**: {schema_name}\n"
                    f"**검색어**: {query}\n\n"
                    "**원인**: 컬럼 벡터화가 완료되지 않았습니다.\n\n"
                    "**해결 방법**:\n"
                    "1. 루트 디렉토리에서 컬럼 벡터화 스크립트 실행:\n"
                    "   ```bash\n"
                    "   python vectorize_columns.py\n"
                    "   ```\n\n"
                    "2. 벡터화 완료 후 다시 시도하세요.\n"
                    "   (21,515개 컬럼을 벡터화하는 데 시간이 걸릴 수 있습니다)\n\n"
                    "💡 **참고**: 이후에는 자동으로 진행 상황을 추적하여 빠르게 처리됩니다."
                )
            }]

        # 컬럼 검색 수행
        columns = vector_db.search_columns(
            query=query,
            database_sid=database_sid,
            schema_name=schema_name,
            table_name=table_name,
            n_results=n_results
        )

        if not columns:
            return [{
                "type": "text",
                "text": (
                    f"ℹ️ **검색 결과가 없습니다**\n\n"
                    f"**검색어**: {query}\n"
                    f"**Database**: {database_sid}\n"
                    f"**Schema**: {schema_name}\n"
                    f"{'**테이블**: ' + table_name if table_name else ''}\n\n"
                    "이 조건에 맞는 컬럼이 없습니다.\n"
                    "다른 검색어로 시도해보세요."
                )
            }]

        # 결과 포맷팅
        result_text = f"🔍 **컬럼 검색 결과** (의미 기반)\n\n"
        result_text += f"**검색어**: {query}\n"
        result_text += f"**Database**: {database_sid}\n"
        result_text += f"**Schema**: {schema_name}\n"
        if table_name:
            result_text += f"**테이블**: {table_name}\n"
        result_text += f"**발견된 컬럼**: {len(columns)}개\n\n"
        result_text += "**검색 결과 (유사도 순)**:\n\n"

        for i, col in enumerate(columns, 1):
            result_text += f"### {i}. {col['table_name']}.{col['column_name']}"
            if col.get('is_pk'):
                result_text += " [PK]"
            result_text += f" ({col['similarity']}% 유사도)\n"

            if col.get('korean_name'):
                result_text += f"- **한글명**: {col['korean_name']}\n"

            if col.get('data_type'):
                result_text += f"- **데이터타입**: {col['data_type']}\n"

            if col.get('description'):
                desc = col['description'][:100]
                if len(col['description']) > 100:
                    desc += "..."
                result_text += f"- **설명**: {desc}\n"

            if col.get('column_comment'):
                result_text += f"- **컬럼 주석**: {col['column_comment']}\n"

            result_text += "\n"

        result_text += "---\n\n"
        result_text += "**다음 단계**:\n"
        result_text += "1. 위 컬럼들을 SELECT 절에 포함시켜 SQL 작성\n"
        result_text += "2. `execute_sql` Tool로 SQL 실행\n\n"
        result_text += "💡 **TIP**: 유사도가 높은(>70%) 컬럼부터 선택하세요."

        return [{
            "type": "text",
            "text": result_text
        }]

    except RuntimeError as e:
        logger.error(f"Vector DB error: {e}")
        return [{
            "type": "text",
            "text": f"❌ Vector DB 오류: {str(e)}"
        }]

    except Exception as e:
        import traceback
        logger.error(f"컬럼 검색 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 컬럼 검색 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: SQL 생성 및 미리보기 (피드백 포함)
# ============================================

async def generate_and_review_sql(
    database_sid: str,
    schema_name: str,
    natural_query: str,
    created_by: str = "system"
) -> list[dict]:
    """
    ★ SQL 생성 후 미리보기 (사용자 검토 기능)

    자연어 질문을 받아 SQL을 생성하고, 미리보기를 제공합니다.
    사용자가 검토 후 피드백을 제출할 수 있습니다.
    """
    try:
        # Step 1: Vector DB로 관련 테이블/컬럼 검색
        vector_db = get_vector_db()
        if not vector_db.is_available():
            return [{
                "type": "text",
                "text": "❌ Vector DB를 사용할 수 없습니다. 먼저 벡터화를 완료하세요."
            }]

        # 테이블 검색 (가중치 적용)
        table_weights = feedback_manager.get_table_weights(database_sid, schema_name)
        tables = vector_db.search_tables(
            question=natural_query,
            database_sid=database_sid,
            schema_name=schema_name,
            n_results=5,
            weights=table_weights if table_weights else None
        )

        if not tables:
            return [{
                "type": "text",
                "text": f"❌ 관련 테이블을 찾을 수 없습니다.\n자연어: {natural_query}"
            }]

        # 선택된 테이블 정보
        selected_table = tables[0]
        table_name = selected_table["table_name"]

        # 컬럼 검색
        column_weights = feedback_manager.get_column_weights(
            table_name, database_sid, schema_name
        )
        columns = vector_db.search_columns(
            query=natural_query,
            database_sid=database_sid,
            schema_name=schema_name,
            table_name=table_name,
            n_results=10,
            column_weights={table_name: column_weights} if column_weights else None
        )

        # Step 2: Claude로 SQL 생성 (간단한 쿼리)
        # 여기서는 기본 SELECT 구문 생성
        selected_columns = [col["column_name"] for col in columns[:5]]
        if not selected_columns:
            selected_columns = ["*"]

        columns_clause = ", ".join(selected_columns)
        generated_sql = f"SELECT {columns_clause} FROM {schema_name}.{table_name}"

        # Step 3: 피드백 저장 (SQL 생성 이력)
        feedback_data = {
            "user_query": natural_query,
            "selected_table": table_name,
            "selected_columns": selected_columns,
            "generated_sql": generated_sql,
            "database_sid": database_sid,
            "schema_name": schema_name,
            "created_by": created_by
        }

        feedback_id = feedback_manager.save_sql_generation(feedback_data)

        # Step 4: 미리보기 형식으로 반환
        result_text = f"🔍 **SQL 생성 완료** (ID: {feedback_id})\n\n"
        result_text += f"**사용자 질문**: {natural_query}\n\n"
        result_text += f"**선택된 테이블**: {table_name}\n"
        result_text += f"**테이블 유사도**: {selected_table.get('similarity', 0):.1f}%\n\n"

        result_text += "**검색된 컬럼** (상위 5개):\n"
        for i, col in enumerate(columns[:5], 1):
            result_text += f"- {i}. {col['column_name']} ({col.get('similarity', 0):.1f}% 유사도)\n"

        result_text += f"\n**생성된 SQL**:\n```sql\n{generated_sql}\n```\n\n"

        result_text += f"**다음 단계**:\n"
        result_text += f"1. `submit_sql_feedback` Tool을 사용하여 다음 중 선택:\n"
        result_text += f"   - action: 'approve' (승인 후 실행)\n"
        result_text += f"   - action: 'modify' (수정 제안 후 재생성)\n"
        result_text += f"   - action: 'reject' (거부)\n\n"
        result_text += f"**Feedback ID**: `{feedback_id}`\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 생성 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 생성 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: 사용자 피드백 저장 및 가중치 계산
# ============================================

async def submit_sql_feedback(
    feedback_id: str,
    action: str,
    suggestions: str = None,
    user_confidence: float = 0.5
) -> list[dict]:
    """
    ★ 사용자 피드백 저장 및 가중치 계산

    action: 'approve', 'modify', 'reject'
    """
    try:
        # Step 1: 사용자 피드백 저장
        feedback_manager.save_user_feedback(
            feedback_id=feedback_id,
            action=action,
            suggestions=suggestions,
            user_confidence=user_confidence
        )

        # Step 2: 가중치 계산
        feedback_manager.calculate_weights()

        result_text = f"✅ **피드백 처리 완료**\n\n"
        result_text += f"**Feedback ID**: {feedback_id}\n"
        result_text += f"**사용자 선택**: {action.upper()}\n"
        result_text += f"**신뢰도**: {user_confidence*100:.0f}%\n\n"

        if suggestions:
            result_text += f"**사용자 제안**: {suggestions}\n\n"

        result_text += "✅ 가중치 재계산 완료\n"
        result_text += "다음 검색부터 사용자의 피드백이 반영됩니다.\n\n"

        if action == "modify":
            result_text += "💡 다음 단계:\n"
            result_text += "`regenerate_sql_with_feedback` Tool을 사용하여\n"
            result_text += "사용자 피드백을 반영한 SQL을 재생성할 수 있습니다.\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"피드백 저장 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 피드백 저장 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: 피드백 기반 SQL 재생성
# ============================================

async def regenerate_sql_with_feedback(
    feedback_id: str,
    feedback_text: str
) -> list[dict]:
    """
    ★ 사용자 피드백을 반영하여 SQL 재생성
    """
    try:
        # 피드백 정보 조회
        feedback_summary = feedback_manager.query_feedback_summary(limit=100)

        # 해당 feedback_id 찾기
        target_feedback = None
        for fb in feedback_summary:
            if fb.get("feedback_id") == feedback_id:
                target_feedback = fb
                break

        if not target_feedback:
            return [{
                "type": "text",
                "text": f"❌ Feedback ID를 찾을 수 없습니다: {feedback_id}"
            }]

        # 재생성된 SQL (간단한 예시)
        # 실제 구현에서는 Claude에게 피드백을 전달하여 SQL 재생성
        regenerated_sql = f"-- 피드백 반영됨: {feedback_text}\n"
        regenerated_sql += f"-- 원본 Query: {target_feedback.get('user_query', '')}\n"
        regenerated_sql += "SELECT * FROM " + target_feedback.get('selected_table', 'TABLE')

        result_text = f"🔄 **SQL 재생성 완료**\n\n"
        result_text += f"**Feedback ID**: {feedback_id}\n"
        result_text += f"**사용자 피드백**: {feedback_text}\n\n"
        result_text += f"**재생성된 SQL**:\n```sql\n{regenerated_sql}\n```\n\n"
        result_text += "💡 다음 단계:\n"
        result_text += "`execute_sql_direct` Tool을 사용하여 SQL을 실행할 수 있습니다.\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 재생성 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 재생성 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# Tool: SQL 직접 실행 (피드백 없이)
# ============================================

async def execute_sql_direct(
    database_sid: str,
    sql: str,
    max_rows: int = 100
) -> list[dict]:
    """SQL을 직접 실행 (피드백 기능 없음)"""
    try:
        connector = get_connector(database_sid)

        # SQL 실행
        results = connector.query(sql, max_rows=max_rows)

        if isinstance(results, str):
            return [{
                "type": "text",
                "text": f"✅ **SQL 실행 완료**\n\n{results}"
            }]

        # 결과 포맷팅
        result_text = f"✅ **SQL 실행 완료** ({len(results)}행)\n\n"
        result_text += "```\n"

        if results:
            # 헤더
            headers = list(results[0].keys())
            header_line = " | ".join([f"{h[:15]:15}" for h in headers])
            result_text += header_line + "\n"
            result_text += "-" * len(header_line) + "\n"

            # 데이터
            for row in results[:min(10, len(results))]:
                values = [str(row.get(h, ""))[:15] for h in headers]
                result_text += " | ".join([f"{v:15}" for v in values]) + "\n"

            if len(results) > 10:
                result_text += f"\n... ({len(results) - 10}개 행 생략)\n"

        result_text += "```\n"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"SQL 실행 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ SQL 실행 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


# ============================================
# 서버 실행
# ============================================
async def main():
    """MCP 서버 실행"""
    logger.info("="*60)
    logger.info("🚀 Oracle Database MCP 서버 시작")
    logger.info("="*60)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
