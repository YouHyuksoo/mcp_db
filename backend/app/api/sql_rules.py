"""
SQL Rules Management API Endpoints
Handle SQL writing rules management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime
import shutil
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# SQL rules file path (shared with MCP)
project_root = Path(__file__).parent.parent.parent.parent
SQL_RULES_PATH = project_root / "data" / "sql_rules.md"
SQL_RULES_BACKUP_DIR = project_root / "data" / "sql_rules_backups"


class SQLRulesResponse(BaseModel):
    """SQL rules response"""
    content: str
    file_path: str
    last_modified: Optional[str] = None


class SQLRulesUpdateRequest(BaseModel):
    """SQL rules update request"""
    content: str
    create_backup: bool = True


class SQLRulesUpdateResponse(BaseModel):
    """SQL rules update response"""
    success: bool
    message: str
    backup_file: Optional[str] = None
    file_path: str


@router.get("/view", response_model=SQLRulesResponse)
async def view_sql_rules():
    """
    View current SQL writing rules

    **사용 시나리오:**
    1. 현재 설정된 SQL 작성 규칙 조회
    2. Web UI에서 규칙 표시
    3. 규칙 수정 전 현재 내용 확인

    **출력:**
    - SQL 규칙 내용 (Markdown)
    - 파일 경로
    - 마지막 수정 시간
    """
    try:
        if not SQL_RULES_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="SQL rules file not found. Please create one first."
            )

        with open(SQL_RULES_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get last modified time
        stat = SQL_RULES_PATH.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return SQLRulesResponse(
            content=content,
            file_path=str(SQL_RULES_PATH),
            last_modified=last_modified
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to view SQL rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update", response_model=SQLRulesUpdateResponse)
async def update_sql_rules(request: SQLRulesUpdateRequest):
    """
    Update SQL writing rules

    **사용 시나리오:**
    1. Web UI에서 규칙 수정
    2. 새로운 규칙 추가
    3. 기존 규칙 업데이트

    **입력:**
    - content: 새로운 SQL 규칙 내용 (Markdown)
    - create_backup: 백업 생성 여부 (기본: true)

    **출력:**
    - 업데이트 성공 여부
    - 백업 파일 경로 (백업 생성 시)
    """
    try:
        # Ensure data directory exists
        SQL_RULES_PATH.parent.mkdir(parents=True, exist_ok=True)

        backup_file = None

        # Create backup if requested and file exists
        if request.create_backup and SQL_RULES_PATH.exists():
            # Ensure backup directory exists
            SQL_RULES_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

            # Create backup file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file_path = SQL_RULES_BACKUP_DIR / f"sql_rules_{timestamp}.md"

            # Copy to backup
            shutil.copy2(SQL_RULES_PATH, backup_file_path)
            backup_file = backup_file_path.name

            logger.info(f"Created backup: {backup_file}")

        # Write new rules
        with open(SQL_RULES_PATH, 'w', encoding='utf-8') as f:
            f.write(request.content)

        logger.info(f"Updated SQL rules: {len(request.content)} characters")

        return SQLRulesUpdateResponse(
            success=True,
            message="SQL rules updated successfully",
            backup_file=backup_file,
            file_path=str(SQL_RULES_PATH)
        )

    except Exception as e:
        logger.error(f"Failed to update SQL rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups")
async def list_sql_rules_backups():
    """
    List all SQL rules backup files

    **사용 시나리오:**
    1. 백업 파일 목록 조회
    2. 특정 백업으로 복원하기 전 확인

    **출력:**
    - 백업 파일 목록 (파일명, 생성 시간, 크기)
    """
    try:
        if not SQL_RULES_BACKUP_DIR.exists():
            return {
                "backups": [],
                "total_count": 0
            }

        backups = []
        for backup_file in sorted(SQL_RULES_BACKUP_DIR.glob("sql_rules_*.md"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "file_name": backup_file.name,
                "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_bytes": stat.st_size,
                "size_kb": round(stat.st_size / 1024, 2)
            })

        return {
            "backups": backups,
            "total_count": len(backups)
        }

    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore/{backup_file_name}")
async def restore_sql_rules_from_backup(backup_file_name: str):
    """
    Restore SQL rules from backup

    **사용 시나리오:**
    1. 이전 버전의 SQL 규칙으로 복원
    2. 잘못된 수정 취소

    **입력:**
    - backup_file_name: 복원할 백업 파일명

    **출력:**
    - 복원 성공 여부
    """
    try:
        backup_file_path = SQL_RULES_BACKUP_DIR / backup_file_name

        if not backup_file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Backup file not found: {backup_file_name}"
            )

        # Create backup of current file before restoring
        if SQL_RULES_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            current_backup = SQL_RULES_BACKUP_DIR / f"sql_rules_before_restore_{timestamp}.md"
            shutil.copy2(SQL_RULES_PATH, current_backup)

        # Restore from backup
        shutil.copy2(backup_file_path, SQL_RULES_PATH)

        logger.info(f"Restored SQL rules from backup: {backup_file_name}")

        return {
            "success": True,
            "message": f"SQL rules restored from {backup_file_name}",
            "file_path": str(SQL_RULES_PATH)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore from backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/template")
async def get_sql_rules_template():
    """
    Get SQL rules template

    **사용 시나리오:**
    1. 새 프로젝트 시작 시 기본 템플릿 로드
    2. 규칙 파일이 없을 때 기본 구조 제공

    **출력:**
    - SQL 규칙 템플릿 (Markdown)
    """
    template = """# SQL 작성 규칙

## 1. 인덱스 최적화

### 날짜 컬럼 검색
❌ **나쁜 예 (인덱스 사용 불가)**
```sql
WHERE TRUNC(date_col) = DATE '2025-01-01'
```

✅ **좋은 예 (인덱스 사용 가능)**
```sql
WHERE date_col >= DATE '2025-01-01' AND date_col < DATE '2025-01-02'
```

## 2. 문자열 검색

❌ **나쁜 예**
```sql
WHERE UPPER(col) = 'VALUE'
```

✅ **좋은 예**
```sql
WHERE col = 'VALUE'
```

## 3. 숫자 연산

❌ **나쁜 예**
```sql
WHERE col * 1.1 > 100
```

✅ **좋은 예**
```sql
WHERE col > 100 / 1.1
```

## 4. NULL 체크

✅ **올바른 사용**
```sql
WHERE col IS NULL
WHERE col IS NOT NULL
```

## 5. 추가 규칙

여기에 프로젝트별 SQL 작성 규칙을 추가하세요.
"""

    return {
        "template": template
    }
