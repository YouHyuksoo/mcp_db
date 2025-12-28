"""
TNSNames API Endpoints
Handle tnsnames.ora file parsing and database connection management
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import sys
from pathlib import Path

# Use shared TNSNamesParser instance
from app.core.tnsnames_instance import get_tnsnames_parser

logger = logging.getLogger(__name__)
router = APIRouter()

# Get shared tnsnames parser instance
tnsnames_parser = get_tnsnames_parser()


class TNSNamesParseRequest(BaseModel):
    """Request to parse tnsnames.ora file"""
    file_path: str


class DatabaseConnection(BaseModel):
    """Database connection information from tnsnames.ora"""
    sid: str
    host: str
    port: int
    service_name: str
    connection_type: str
    description: Optional[str] = ""


class TNSNamesParseResponse(BaseModel):
    """Response after parsing tnsnames.ora"""
    success: bool
    total_databases: int
    databases: List[DatabaseConnection]
    file_path: str
    error: Optional[str] = None


class DatabaseListResponse(BaseModel):
    """Response for database list"""
    databases: List[DatabaseConnection]
    total_count: int


@router.post("/parse", response_model=TNSNamesParseResponse)
async def parse_tnsnames_file(request: TNSNamesParseRequest):
    """
    Parse tnsnames.ora file and extract database connection information

    **사용 시나리오:**
    1. Oracle 클라이언트의 tnsnames.ora 파일 경로 입력
    2. 파일을 파싱하여 모든 DB 연결 정보 추출
    3. 추출된 DB 목록을 Frontend에 표시
    4. 관리자가 원하는 DB를 선택하여 메타데이터 수집 대상 설정

    **입력:**
    - file_path: tnsnames.ora 파일의 절대 경로
      예) D:\\app\\oracle\\product\\19c\\network\\admin\\tnsnames.ora

    **출력:**
    - 파싱된 DB 목록 (SID, Host, Port, Service Name 포함)
    """
    try:
        databases_dict = tnsnames_parser.parse_file(request.file_path)

        databases = []
        for sid, info in databases_dict.items():
            databases.append(DatabaseConnection(
                sid=sid,
                host=info['host'],
                port=info['port'],
                service_name=info['service_name'],
                connection_type=info['connection_type'],
                description=info.get('description', '')
            ))

        logger.info(f"Parsed {len(databases)} databases from {request.file_path}")

        return TNSNamesParseResponse(
            success=True,
            total_databases=len(databases),
            databases=databases,
            file_path=request.file_path
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {request.file_path}")
        return TNSNamesParseResponse(
            success=False,
            total_databases=0,
            databases=[],
            file_path=request.file_path,
            error=f"파일을 찾을 수 없습니다: {request.file_path}"
        )
    except IsADirectoryError as e:
        logger.error(f"Path is a directory, not a file: {request.file_path}")
        return TNSNamesParseResponse(
            success=False,
            total_databases=0,
            databases=[],
            file_path=request.file_path,
            error=f"디렉토리가 아닌 파일 경로를 입력해주세요. tnsnames.ora 파일의 전체 경로를 입력하세요. (예: D:\\app\\oracle\\product\\19c\\network\\admin\\tnsnames.ora)"
        )
    except Exception as e:
        logger.error(f"Failed to parse tnsnames.ora: {e}")
        return TNSNamesParseResponse(
            success=False,
            total_databases=0,
            databases=[],
            file_path=request.file_path,
            error=str(e)
        )


@router.get("/list", response_model=DatabaseListResponse)
async def list_databases():
    """
    Get list of parsed databases

    **사용 시나리오:**
    1. tnsnames.ora 파일을 파싱한 후 호출
    2. 현재 메모리에 저장된 DB 목록 조회
    3. Frontend에서 드롭다운 메뉴로 표시

    **출력:**
    - 현재 파싱된 모든 DB 연결 정보
    """
    try:
        databases = []
        for sid, info in tnsnames_parser.databases.items():
            databases.append(DatabaseConnection(
                sid=sid,
                host=info['host'],
                port=info['port'],
                service_name=info['service_name'],
                connection_type=info['connection_type'],
                description=info.get('description', '')
            ))

        return DatabaseListResponse(
            databases=databases,
            total_count=len(databases)
        )

    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/{keyword}")
async def search_databases(keyword: str):
    """
    Search databases by keyword

    **사용 시나리오:**
    1. 많은 DB가 등록된 경우 검색 기능 사용
    2. DB SID 또는 설명에서 키워드 검색
    3. 검색 결과를 Frontend에 표시

    **입력:**
    - keyword: 검색 키워드 (DB SID 또는 설명에서 검색)

    **출력:**
    - 검색된 DB 목록
    """
    try:
        matching_sids = tnsnames_parser.search_databases(keyword)

        databases = []
        for sid in matching_sids:
            info = tnsnames_parser.databases[sid]
            databases.append(DatabaseConnection(
                sid=sid,
                host=info['host'],
                port=info['port'],
                service_name=info['service_name'],
                connection_type=info['connection_type'],
                description=info.get('description', '')
            ))

        return DatabaseListResponse(
            databases=databases,
            total_count=len(databases)
        )

    except Exception as e:
        logger.error(f"Failed to search databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
