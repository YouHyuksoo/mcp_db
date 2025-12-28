"""
Metadata API Endpoints
Handles Vector DB search, metadata migration, and CSV processing
"""

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from typing import Optional
from app.models.metadata import (
    MetadataSearchRequest,
    MetadataSearchResponse,
    MetadataSearchResult,
    MigrationRequest,
    MigrationResponse
)
from app.utils.metadata_migrator import MetadataMigrator
import logging
import csv
import io
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=MetadataSearchResponse)
async def search_metadata(request: MetadataSearchRequest, req: Request):
    """
    Search for relevant tables using semantic search (Vector DB)

    This replaces the slow JSON file search in Stage 1 of the 2-stage process.
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        # Create embedding for the question
        query_embedding = embedding_service.embed_text(request.question)

        # Prepare filter
        filter_dict = None
        if request.database_sid and request.schema_name:
            filter_dict = {
                "database_sid": request.database_sid,
                "schema_name": request.schema_name
            }

        # Search Vector DB
        results = vector_store.search_metadata(
            query_embedding=query_embedding,
            n_results=request.limit,
            filter_dict=filter_dict
        )

        # Format results
        search_results = []
        for i, table_id in enumerate(results.get("ids", [])):
            metadata = results["metadatas"][i]
            distance = results["distances"][i]

            # Convert distance to similarity score (0-1, higher = more similar)
            similarity = max(0, 1 - (distance / 2))

            search_results.append(MetadataSearchResult(
                table_id=table_id,
                table_name=metadata.get("table_name", ""),
                schema_name=metadata.get("schema_name", ""),
                database_sid=metadata.get("database_sid", ""),
                korean_name=metadata.get("korean_name"),
                description=metadata.get("description"),
                similarity_score=round(similarity, 4),
                column_count=metadata.get("column_count", 0)
            ))

        logger.info(f"Metadata search: '{request.question}' -> {len(search_results)} results")

        return MetadataSearchResponse(
            results=search_results,
            total_found=len(search_results),
            query=request.question
        )

    except Exception as e:
        logger.error(f"Metadata search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate", response_model=MigrationResponse)
async def migrate_metadata(request: MigrationRequest, req: Request):
    """
    Migrate JSON metadata files to Vector DB

    This is a one-time migration operation for existing projects.
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        migrator = MetadataMigrator(vector_store, embedding_service)

        result = await migrator.migrate_from_json(
            metadata_dir=request.metadata_dir,
            database_sid=request.database_sid,
            schema_name=request.schema_name
        )

        if result["success"]:
            return MigrationResponse(
                success=True,
                tables_migrated=result["tables_migrated"],
                database_sid=request.database_sid,
                schema_name=request.schema_name
            )
        else:
            return MigrationResponse(
                success=False,
                tables_migrated=0,
                database_sid=request.database_sid,
                schema_name=request.schema_name,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return MigrationResponse(
            success=False,
            tables_migrated=0,
            database_sid=request.database_sid,
            schema_name=request.schema_name,
            error=str(e)
        )


@router.get("/stats")
async def get_metadata_stats(req: Request):
    """Get Vector DB statistics"""
    try:
        vector_store = req.app.state.vector_store
        stats = vector_store.get_stats()

        return {
            "success": True,
            "metadata_count": stats["metadata_count"],
            "patterns_count": stats["patterns_count"],
            "business_rules_count": stats["business_rules_count"],
            "total_entries": sum(stats.values())
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_metadata(
    request: Request,
    database_sid: str = Form(...),
    schema_name: str = Form(...),
    table_info: UploadFile = File(...),
    common_columns: UploadFile = File(...),
    code_definitions: UploadFile = File(...),
):
    """
    CSV 파일 3종을 업로드하여 DB 스키마와 통합된 메타정보를 생성하고 Vector DB에 저장

    Args:
        database_sid: Oracle Database SID
        schema_name: Schema name
        table_info: table_info_template.csv
        common_columns: common_columns_template.csv
        code_definitions: code_definitions_template.csv

    Returns:
        {
            "success": true,
            "tables_processed": 10,
            "database_sid": "ORCL",
            "schema_name": "HR"
        }
    """
    try:
        vector_store = request.app.state.vector_store

        # 1. CSV 파일 검증
        logger.info(f"Processing metadata for {database_sid}.{schema_name}")

        # CSV 파일 읽기
        table_info_content = await table_info.read()
        common_columns_content = await common_columns.read()
        code_definitions_content = await code_definitions.read()

        # CSV 파싱
        table_info_data = parse_csv(table_info_content.decode('utf-8'))
        common_columns_data = parse_csv(common_columns_content.decode('utf-8'))
        code_definitions_data = parse_csv(code_definitions_content.decode('utf-8'))

        logger.info(f"Parsed {len(table_info_data)} tables, {len(common_columns_data)} common columns, {len(code_definitions_data)} code definitions")

        # 2. 데이터 저장 디렉토리 생성
        project_root = Path(__file__).parent.parent.parent.parent
        data_dir = project_root / "data" / database_sid / schema_name
        metadata_dir = data_dir / "metadata"
        csv_uploads_dir = data_dir / "csv_uploads"

        metadata_dir.mkdir(parents=True, exist_ok=True)
        csv_uploads_dir.mkdir(parents=True, exist_ok=True)

        # 3. CSV 파일 저장
        (csv_uploads_dir / "table_info_template.csv").write_bytes(table_info_content)
        (csv_uploads_dir / "common_columns_template.csv").write_bytes(common_columns_content)
        (csv_uploads_dir / "code_definitions_template.csv").write_bytes(code_definitions_content)

        # 4. Oracle DB 연결 및 스키마 조회
        logger.info(f"Connecting to Oracle DB: {database_sid}")

        # Load DB credentials
        import sys
        import importlib.util
        from pathlib import Path as PathLib

        # Import CredentialsManager and OracleConnector from mcp directory
        project_root = Path(__file__).parent.parent.parent.parent
        mcp_path = project_root / "mcp"

        credentials_manager_spec = importlib.util.spec_from_file_location(
            "credentials_manager", mcp_path / "credentials_manager.py"
        )
        credentials_manager_module = importlib.util.module_from_spec(credentials_manager_spec)
        credentials_manager_spec.loader.exec_module(credentials_manager_module)
        CredentialsManager = credentials_manager_module.CredentialsManager

        oracle_connector_spec = importlib.util.spec_from_file_location(
            "oracle_connector", mcp_path / "oracle_connector.py"
        )
        oracle_connector_module = importlib.util.module_from_spec(oracle_connector_spec)
        oracle_connector_spec.loader.exec_module(oracle_connector_module)
        OracleConnector = oracle_connector_module.OracleConnector

        # Load credentials
        credentials_dir = project_root / "data" / "credentials"
        cred_manager = CredentialsManager(credentials_dir=str(credentials_dir))
        credentials = cred_manager.load_credentials(database_sid)

        # Connect to Oracle DB
        oracle = OracleConnector(
            host=credentials['host'],
            port=credentials['port'],
            service_name=credentials['service_name'],
            user=credentials['user'],
            password=credentials['password']
        )

        if not oracle.connect():
            raise HTTPException(status_code=500, detail=f"Failed to connect to Oracle DB: {database_sid}")

        # Query schema to get table columns for each table in table_info_data
        schema_tables_columns = {}
        try:
            for table_row in table_info_data:
                table_name = table_row.get('table_name', '').strip()
                if not table_name:
                    continue

                # Query ALL_TAB_COLUMNS to get actual columns for this table
                query = """
                    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, COLUMN_ID
                    FROM ALL_TAB_COLUMNS
                    WHERE OWNER = :schema_name AND TABLE_NAME = :table_name
                    ORDER BY COLUMN_ID
                """
                result = oracle.execute_query(query, {
                    'schema_name': schema_name,
                    'table_name': table_name
                })

                if result:
                    schema_tables_columns[table_name] = [
                        {
                            'column_name': row['COLUMN_NAME'],
                            'data_type': row['DATA_TYPE'],
                            'data_length': row['DATA_LENGTH'],
                            'nullable': row['NULLABLE'],
                            'column_id': row['COLUMN_ID']
                        }
                        for row in result
                    ]
                    logger.info(f"Found {len(result)} columns for table {table_name}")
                else:
                    logger.warning(f"No columns found for table {table_name} in schema {schema_name}")
        finally:
            oracle.disconnect()

        logger.info(f"Retrieved schema information for {len(schema_tables_columns)} tables")

        # 5. 통합 메타정보 생성
        tables_processed = 0
        metadata_list = []

        # 공통 컬럼 딕셔너리 생성 (column_name을 키로)
        common_columns_dict = {}
        for col_row in common_columns_data:
            col_name = col_row.get('column_name', '').strip()
            if col_name:
                common_columns_dict[col_name] = {
                    "column_name": col_name,
                    "korean_name": col_row.get('korean_name', ''),
                    "description": col_row.get('description', ''),
                    "business_rule": col_row.get('business_rule', ''),
                    "sample_values": col_row.get('sample_values', ''),
                    "unit": col_row.get('unit', ''),
                    "is_code_column": col_row.get('is_code_column', 'N'),
                    "aggregation_functions": col_row.get('aggregation_functions', ''),
                    "is_sensitive": col_row.get('is_sensitive', 'N')
                }

        # 코드 정의 딕셔너리 생성 (column_name을 키로)
        code_definitions_dict = {}
        for code_row in code_definitions_data:
            col_name = code_row.get('column_name', '').strip()
            code_value = code_row.get('code_value', '').strip()
            code_label = code_row.get('code_label', '')

            if col_name and code_value:
                if col_name not in code_definitions_dict:
                    code_definitions_dict[col_name] = {}
                code_definitions_dict[col_name][code_value] = code_label

        # 테이블별로 메타정보 통합
        logger.info(f"Starting table processing loop with {len(table_info_data)} rows")
        for idx, table_row in enumerate(table_info_data):
            table_name = table_row.get('table_name', '').strip()
            if not table_name:
                continue

            # Skip if table not found in DB schema
            if table_name not in schema_tables_columns:
                logger.warning(f"Table {table_name} not found in DB schema, skipping")
                continue

            # 테이블 기본 정보
            table_metadata = {
                "database_sid": database_sid,
                "schema_name": schema_name,
                "table_name": table_name,
                "table_comment": table_row.get('business_purpose', ''),
                "business_purpose": table_row.get('business_purpose', ''),
                "usage_scenarios": [
                    table_row.get('usage_scenario_1', ''),
                    table_row.get('usage_scenario_2', ''),
                    table_row.get('usage_scenario_3', '')
                ],
                "related_tables": table_row.get('related_tables', ''),
                "columns": [],
                "code_definitions": {},
                "created_at": datetime.now().isoformat(),
            }

            # Match actual DB columns with CSV column definitions
            db_columns = schema_tables_columns[table_name]
            matched_columns = []
            table_code_definitions = {}

            for db_col in db_columns:
                col_name = db_col['column_name']

                # Start with DB column info
                column_info = {
                    "column_name": col_name,
                    "data_type": db_col['data_type'],
                    "data_length": db_col['data_length'],
                    "nullable": db_col['nullable'],
                    "column_id": db_col['column_id'],
                }

                # Enhance with CSV metadata if available
                if col_name in common_columns_dict:
                    csv_col = common_columns_dict[col_name]
                    column_info.update({
                        "korean_name": csv_col.get('korean_name', ''),
                        "description": csv_col.get('description', ''),
                        "business_rule": csv_col.get('business_rule', ''),
                        "sample_values": csv_col.get('sample_values', ''),
                        "unit": csv_col.get('unit', ''),
                        "is_code_column": csv_col.get('is_code_column', 'N'),
                        "aggregation_functions": csv_col.get('aggregation_functions', ''),
                        "is_sensitive": csv_col.get('is_sensitive', 'N')
                    })

                    # Add code definitions if this is a code column
                    if col_name in code_definitions_dict:
                        table_code_definitions[col_name] = code_definitions_dict[col_name]
                else:
                    # No CSV metadata, use defaults
                    column_info.update({
                        "korean_name": "",
                        "description": "",
                        "business_rule": "",
                        "sample_values": "",
                        "unit": "",
                        "is_code_column": "N",
                        "aggregation_functions": "",
                        "is_sensitive": "N"
                    })

                matched_columns.append(column_info)

            table_metadata["columns"] = matched_columns
            table_metadata["code_definitions"] = table_code_definitions

            # JSON 파일로 저장
            metadata_file = metadata_dir / f"{table_name}.json"
            metadata_file.write_text(json.dumps(table_metadata, ensure_ascii=False, indent=2), encoding='utf-8')

            metadata_list.append(table_metadata)
            tables_processed += 1

            logger.info(f"Processed metadata for table: {table_name}")

        # 6. 임베딩 생성 및 Vector DB 저장
        logger.info(f"Adding {tables_processed} tables to Vector DB")
        embedding_service = request.app.state.embedding_service

        for metadata in metadata_list:
            table_name = metadata["table_name"]
            table_id = f"{database_sid}.{schema_name}.{table_name}"

            # 임베딩을 위한 텍스트 생성
            document_text = generate_document_text(metadata)

            # 임베딩 생성
            embedding = embedding_service.embed_text(document_text)

            # Vector DB에 추가
            vector_store.add_metadata(
                table_id=table_id,
                summary_text=document_text,
                embedding=embedding,
                metadata={
                    "database_sid": database_sid,
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "table_comment": metadata.get("table_comment", ""),
                    "column_count": len(metadata.get("columns", [])),
                    "created_at": metadata.get("created_at", ""),
                }
            )

        # 7. 업로드 히스토리 저장
        history_file = data_dir / "upload_history.json"
        history = []
        if history_file.exists():
            history = json.loads(history_file.read_text(encoding='utf-8'))

        history.append({
            "timestamp": datetime.now().isoformat(),
            "database_sid": database_sid,
            "schema_name": schema_name,
            "tables_processed": tables_processed,
            "files": {
                "table_info": table_info.filename,
                "common_columns": common_columns.filename,
                "code_definitions": code_definitions.filename,
            }
        })

        history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')

        logger.info(f"Successfully processed {tables_processed} tables for {database_sid}.{schema_name}")

        return {
            "success": True,
            "tables_processed": tables_processed,
            "database_sid": database_sid,
            "schema_name": schema_name,
        }

    except Exception as e:
        logger.error(f"Failed to process metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"메타데이터 처리 중 오류가 발생했습니다: {str(e)}")


@router.get("/list")
async def list_metadata(
    request: Request,
    database_sid: Optional[str] = None,
    schema_name: Optional[str] = None,
):
    """
    등록된 메타데이터 목록 조회

    Args:
        database_sid: Optional filter by database SID
        schema_name: Optional filter by schema name

    Returns:
        {
            "metadata": [...],
            "total_count": 10
        }
    """
    try:
        vector_store = request.app.state.vector_store

        # Vector DB에서 메타데이터 조회
        metadata_list = vector_store.list_all_metadata(
            database_sid=database_sid,
            schema_name=schema_name
        )

        # 간단한 요약 정보만 반환
        summary_list = []
        for metadata in metadata_list:
            summary_list.append({
                "table_name": metadata.get("table_name", ""),
                "table_comment": metadata.get("table_comment", ""),
                "column_count": metadata.get("column_count", 0),
                "last_updated": metadata.get("created_at", ""),
            })

        return {
            "metadata": summary_list,
            "total_count": len(summary_list),
        }

    except Exception as e:
        logger.error(f"Failed to list metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def parse_csv(csv_content: str) -> list[dict]:
    """CSV 콘텐츠를 파싱하여 딕셔너리 리스트로 반환"""
    # Remove BOM if present
    if csv_content.startswith('\ufeff'):
        csv_content = csv_content[1:]

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)

    # Debug: Log first row to check parsing
    if rows:
        logger.info(f"CSV parsed - Total rows: {len(rows)}")
        logger.info(f"First CSV row keys: {list(rows[0].keys())}")
        logger.info(f"First CSV row sample: {rows[0]}")

    return rows


def generate_document_text(metadata: dict) -> str:
    """
    메타데이터를 임베딩을 위한 텍스트로 변환

    이 텍스트는 자연어 질의와 매칭하기 위해 사용됨
    """
    table_name = metadata.get("table_name", "")
    table_comment = metadata.get("table_comment", "")
    business_purpose = metadata.get("business_purpose", "")
    usage_scenarios = metadata.get("usage_scenarios", [])
    columns = metadata.get("columns", [])

    # 기본 정보
    text_parts = [
        f"테이블명: {table_name}",
        f"설명: {table_comment}",
        f"비즈니스 목적: {business_purpose}",
    ]

    # 사용 시나리오
    if usage_scenarios and any(usage_scenarios):
        text_parts.append("사용 시나리오:")
        for i, scenario in enumerate(usage_scenarios, 1):
            if scenario:
                text_parts.append(f"  {i}. {scenario}")

    # 컬럼 정보 (샘플만 포함 - 너무 많으면 임베딩 품질 저하)
    if columns:
        text_parts.append(f"컬럼 수: {len(columns)}개")
        # 처음 10개 컬럼만 포함
        text_parts.append("주요 컬럼:")
        for col in columns[:10]:
            col_name = col.get("column_name", "")
            korean_name = col.get("korean_name", "")
            description = col.get("description", "")
            if col_name:
                text_parts.append(f"  - {col_name} ({korean_name}): {description}")

    # 코드 정의 (샘플만 포함)
    code_defs = metadata.get("code_definitions", {})
    if code_defs:
        text_parts.append(f"코드 컬럼 수: {len(code_defs)}개")

    return "\n".join(text_parts)
