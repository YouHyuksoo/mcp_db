"""
Database Management API Endpoints
Handle registered database credentials management
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

# Import CredentialsManager from mcp directory using importlib
mcp_path = project_root / "mcp"
credentials_manager_spec = importlib.util.spec_from_file_location(
    "credentials_manager",
    mcp_path / "credentials_manager.py"
)
if credentials_manager_spec and credentials_manager_spec.loader:
    credentials_manager_module = importlib.util.module_from_spec(credentials_manager_spec)
    credentials_manager_spec.loader.exec_module(credentials_manager_module)
    CredentialsManager = credentials_manager_module.CredentialsManager  # type: ignore
else:
    raise ImportError("Failed to load credentials_manager module")

from app.core.tnsnames_instance import get_tnsnames_parser

logger = logging.getLogger(__name__)
router = APIRouter()

# Global managers
# Use project root data directory
data_dir = project_root / "data"
credentials_dir = data_dir / "credentials"
credentials_manager = CredentialsManager(credentials_dir=str(credentials_dir))
# Use shared TNSNamesParser instance
tnsnames_parser = get_tnsnames_parser()


class DatabaseCredentials(BaseModel):
    """Database credentials for registration"""
    database_sid: str
    schema_name: str
    host: str
    port: int
    service_name: str
    user: str
    password: str


class RegisteredDatabase(BaseModel):
    """Registered database information"""
    database_sid: str
    schema_name: str
    host: str
    port: int
    service_name: str
    user: str
    is_connected: bool = False
    table_count: int = 0
    last_updated: Optional[str] = None


class DatabaseListResponse(BaseModel):
    """Response for registered databases list"""
    databases: List[RegisteredDatabase]
    total_count: int


# Import OracleConnector
oracle_connector_spec = importlib.util.spec_from_file_location(
    "oracle_connector",
    mcp_path / "oracle_connector.py"
)
if oracle_connector_spec and oracle_connector_spec.loader:
    oracle_connector_module = importlib.util.module_from_spec(oracle_connector_spec)
    oracle_connector_spec.loader.exec_module(oracle_connector_module)
    OracleConnector = oracle_connector_module.OracleConnector  # type: ignore

@router.get("/list", response_model=DatabaseListResponse)
async def list_registered_databases():
    """
    Get list of registered databases with connection status
    """
    try:
        database_sids = credentials_manager.list_databases()

        # Get Vector DB metadata for table counts
        from app.main import app_instance  # Assuming we can get it or just use a local VectorStore
        # Alternative: use req.app.state.vector_store if we have request, but this is a simple get
        # For simplicity, let's use the global vector_store if available or re-instantiate
        from app.core.vector_store import VectorStore
        vector_store = VectorStore() # It uses the default persist_directory
        databases_raw = vector_store.get_all_databases()
        vector_db_map = {f"{db['database_sid']}": db for db in databases_raw}

        databases = []
        for sid in database_sids:
            try:
                credentials = credentials_manager.load_credentials(sid)
                vector_info = vector_db_map.get(sid, {})
                
                # Check connection status
                is_connected = False
                try:
                    connector = OracleConnector(
                        host=credentials['host'],
                        port=credentials['port'],
                        service_name=credentials['service_name'],
                        user=credentials['user'],
                        password=credentials['password']
                    )
                    is_connected = connector.connect()
                    if is_connected:
                        connector.disconnect()
                except:
                    is_connected = False

                databases.append(RegisteredDatabase(
                    database_sid=sid,
                    schema_name=credentials.get('schema_name', credentials.get('user', 'unknown').upper()),
                    host=credentials.get('host', 'unknown'),
                    port=credentials.get('port', 0),
                    service_name=credentials.get('service_name', 'unknown'),
                    user=credentials.get('user', 'unknown'),
                    is_connected=is_connected,
                    table_count=vector_info.get("table_count", 0),
                    last_updated=vector_info.get("last_updated")
                ))
            except Exception as e:
                logger.error(f"Failed to load credentials for {sid}: {e}")
                continue

        return DatabaseListResponse(
            databases=databases,
            total_count=len(databases)
        )

    except Exception as e:
        logger.error(f"Failed to list registered databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_database(credentials: DatabaseCredentials):
    """
    Register new database credentials

    **사용 시나리오:**
    1. tnsnames.ora에서 파싱한 DB 정보로 등록
    2. 사용자가 수동으로 DB 정보 입력하여 등록
    3. 등록된 DB는 암호화되어 저장됨

    **입력:**
    - database_sid: DB 식별자
    - host, port, service_name: 연결 정보
    - user, password: 인증 정보

    **출력:**
    - 등록 성공 여부
    """
    try:
        credentials_dict = {
            'schema_name': credentials.schema_name,
            'host': credentials.host,
            'port': credentials.port,
            'service_name': credentials.service_name,
            'user': credentials.user,
            'password': credentials.password
        }

        success = credentials_manager.save_credentials(
            credentials.database_sid,
            credentials_dict
        )

        if success:
            return {
                "success": True,
                "message": f"Database {credentials.database_sid} registered successfully",
                "database_sid": credentials.database_sid
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save credentials")

    except Exception as e:
        logger.error(f"Failed to register database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{database_sid}")
async def delete_database(database_sid: str):
    """
    Delete registered database

    **사용 시나리오:**
    1. 더 이상 사용하지 않는 DB 삭제
    2. 접속 정보만 삭제 (메타데이터는 유지)

    **입력:**
    - database_sid: 삭제할 DB SID

    **출력:**
    - 삭제 성공 여부
    """
    try:
        success = credentials_manager.delete_credentials(database_sid)

        if success:
            return {
                "success": True,
                "message": f"Database {database_sid} deleted successfully",
                "database_sid": database_sid
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Database {database_sid} not found"
            )

    except Exception as e:
        logger.error(f"Failed to delete database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RegisterFromTnsnamesRequest(BaseModel):
    """Request to register database from tnsnames"""
    schema_name: str
    user: str
    password: str


@router.post("/register-from-tnsnames/{sid}")
async def register_from_tnsnames(sid: str, request: RegisterFromTnsnamesRequest):
    """
    Register database from tnsnames.ora parsed data

    **사용 시나리오:**
    1. tnsnames.ora 파싱 후 특정 DB 선택
    2. 사용자 인증 정보만 추가하여 등록
    3. Host, Port, Service Name은 tnsnames에서 자동 로드

    **입력:**
    - sid: tnsnames.ora에 있는 DB SID
    - user, password: 인증 정보

    **출력:**
    - 등록 성공 여부
    """
    try:
        # Check if SID exists in tnsnames
        if sid not in tnsnames_parser.databases:
            raise HTTPException(
                status_code=404,
                detail=f"SID {sid} not found in tnsnames.ora. Please parse tnsnames.ora first."
            )

        # Get connection info from tnsnames
        db_info = tnsnames_parser.databases[sid]

        credentials_dict = {
            'schema_name': request.schema_name,
            'host': db_info['host'],
            'port': db_info['port'],
            'service_name': db_info['service_name'],
            'user': request.user,
            'password': request.password
        }

        success = credentials_manager.save_credentials(sid, credentials_dict)

        if success:
            return {
                "success": True,
                "message": f"Database {sid} registered from tnsnames.ora",
                "database_sid": sid
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save credentials")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register database from tnsnames: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{database_sid}/info")
async def get_database_info(database_sid: str):
    """
    Get database connection info (without password)

    **사용 시나리오:**
    1. 특정 DB의 연결 정보 확인
    2. 비밀번호는 보안상 반환하지 않음

    **출력:**
    - DB 연결 정보 (Host, Port, Service Name, User)
    """
    try:
        credentials = credentials_manager.load_credentials(database_sid)

        # Remove password for security
        return {
            "database_sid": database_sid,
            "host": credentials.get('host'),
            "port": credentials.get('port'),
            "service_name": credentials.get('service_name'),
            "user": credentials.get('user')
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Database {database_sid} not found"
        )
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=str(e))
