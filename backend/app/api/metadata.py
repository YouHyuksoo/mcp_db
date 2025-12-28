"""
* @file backend/app/api/metadata.py
* @description
* 이 파일은 메타데이터 관리 및 Vector DB 관련 API 엔드포인트를 정의합니다.
* CSV 업로드, JSON 마이그레이션, 의미 기반 검색 기능을 제공하며
* Oracle DB와 연동하여 실제 테이블 구조를 추출하고 임베딩하여 저장합니다.
*
* 초보자 가이드:
* 1. **`/process` 엔드포인트**: table_info, common_columns, code_definitions CSV 파일을 받아 
*    DB 스키마와 통합된 지식 베이스를 생성합니다.
* 2. **`/search` 엔드포인트**: 자연어 질문을 받아 관련성 높은 테이블을 Vector DB에서 검색합니다.
*
* 유지보수 팁:
* - 임베딩 텍스트 구조 변경: `generate_document_text` 함수를 수정하세요.
* - DB 추출 정보 추가: `process_metadata` 루프 내의 OracleConnector 호출 부분을 수정하세요.
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
    db_key: str = Form(...),
    table_metadata: UploadFile = File(...),
    column_definitions: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    메타데이터 처리 엔드포인트 (2종 CSV 통합)
    
    Args:
        db_key: DB Connection Key (SID)
        table_metadata: table_metadata.csv (테이블 정의)
        column_definitions: column_definitions.csv (컬럼/코드 정의)
    """
    try:
        logger.info(f"Processing metadata for DB: {db_key}")
        
        # 1. 파일 읽기 및 파싱 함수
        async def read_csv(file_obj: UploadFile) -> list:
            content = await file_obj.read()
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('cp949')
                except UnicodeDecodeError:
                    text = content.decode('euc-kr', errors='replace')
            
            # BOM 제거 및 파싱
            if text.startswith('\ufeff'):
                text = text[1:]
                
            return list(csv.DictReader(io.StringIO(text)))

        # 2. CSV 데이터 로드
        tables_data = await read_csv(table_metadata)
        columns_data = await read_csv(column_definitions)
        
        # 딕셔너리로 변환
        table_info_map = {row['table_name'].strip(): row for row in tables_data if row.get('table_name', '').strip()}
        
        # 공통 컬럼 정의 맵 (컬럼명 -> 정보)
        # table_name이 있으면 그것도 고려해야 하지만, 현재 데이터 구조상 empty인 경우가 많음 (공통 정의)
        col_def_map = {}
        for row in columns_data:
            cname = row.get('column_name', '').strip()
            if cname:
                col_def_map[cname] = row

        logger.info(f"Loaded {len(table_info_map)} tables and {len(col_def_map)} column definitions")

        # 3. 데이터 저장 (백업용)
        project_root = Path(__file__).parent.parent.parent.parent
        # DB 이름을 정확히 알기 어렵지만 db_key 사용
        # 실제로는 get_db_config(db_key)['name'] 등이 필요하나, 
        # 여기서는 경로 구조를 단순화하거나 기존 로직을 따라감.
        # 일단 db_key를 폴더명으로 사용 (나중에 credentials에서 정확한 SID 확인 가능)
        
        # credentials 로딩 및 오라클 연결 준비
        import importlib.util
        from app.utils.enhanced_metadata_builder import EnhancedMetadataBuilder

        mcp_path = project_root / "mcp"
        
        # CredentialsManager 동적 로드
        cred_spec = importlib.util.spec_from_file_location("credentials_manager", mcp_path / "credentials_manager.py")
        cred_module = importlib.util.module_from_spec(cred_spec)
        cred_spec.loader.exec_module(cred_module)
        CredentialsManager = cred_module.CredentialsManager
        
        # OracleConnector 동적 로드
        ora_spec = importlib.util.spec_from_file_location("oracle_connector", mcp_path / "oracle_connector.py")
        ora_module = importlib.util.module_from_spec(ora_spec)
        ora_spec.loader.exec_module(ora_module)
        OracleConnector = ora_module.OracleConnector
        
        # Credentials 로드
        credentials_dir = project_root / "data" / "credentials"
        cred_manager = CredentialsManager(credentials_dir=str(credentials_dir))
        credentials = cred_manager.load_credentials(db_key)
        
        if not credentials:
            raise HTTPException(status_code=404, detail=f"Database credentials not found for {db_key}")

        schema_name = credentials['user'].upper() # Default schema is user
        vector_store = req.app.state.vector_store # req 객체 필요
        embedding_service = req.app.state.embedding_service

        # 4. 파일 저장 경로 설정 (실제 경로)
        # data/{db_key}/csv_uploads
        # db_key가 SID와 다를 수 있으나, 보통 매핑됨.
        data_dir = project_root / "data" / db_key / schema_name
        csv_uploads_dir = data_dir / "csv_uploads"
        csv_uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 저장 (seek(0) 하고 다시 읽어야 함)
        await table_metadata.seek(0)
        await column_definitions.seek(0)
        with open(csv_uploads_dir / "table_metadata.csv", "wb") as f:
            f.write(await table_metadata.read())
        with open(csv_uploads_dir / "column_definitions.csv", "wb") as f:
            f.write(await column_definitions.read())

        # 5. 메타데이터 처리 (동기 실행 - 작업량에 따라 백그라운드로 이동 고려)
        # 여기서는 사용자 피드백을 위해 동기로 처리하되, 타임아웃 주의
        
        logger.info(f"Connecting to Oracle DB: {db_key}")
        oracle = OracleConnector(
            host=credentials['host'],
            port=credentials['port'],
            service_name=credentials['service_name'],
            user=credentials['user'],
            password=credentials['password']
        )
        
        if not oracle.connect():
             raise HTTPException(status_code=500, detail="Failed to connect to Oracle DB")

        processed_count = 0
        try:
            for table_name, table_csv_info in table_info_map.items():
                logger.info(f"Processing table: {table_name}")
                
                # DB에서 컬럼 정보 조회
                db_columns = oracle.extract_table_columns(schema_name, table_name)
                if not db_columns:
                    logger.warning(f"Table {table_name} not found in DB or has no columns")
                    continue
                
                # DB PK 정보 조회
                pks = oracle.extract_primary_keys(schema_name, table_name)
                
                # 컬럼 정보 병합
                enhanced_columns = []
                for col in db_columns:
                    col_name = col['name']
                    # CSV 정의 찾기
                    csv_col_def = col_def_map.get(col_name)
                    
                    merged_col = col.copy()
                    merged_col['is_key'] = col_name in pks
                    
                    if csv_col_def:
                        merged_col['korean_name'] = csv_col_def.get('korean_name', '')
                        merged_col['description'] = csv_col_def.get('description', '')
                        merged_col['code_values'] = csv_col_def.get('code_values', '') # JSON string
                    
                    enhanced_columns.append(merged_col)
                
                # 임베딩 텍스트 생성
                summary_text = EnhancedMetadataBuilder.create_summary_text(
                    database_sid=db_key,
                    schema_name=schema_name,
                    table_name=table_name,
                    korean_name=table_csv_info.get('description_ko', ''), # description_ko를 한글명으로 사용?
                    # 주의: table_metadata.csv의 description_ko는 "테이블 설명" 역할. 
                    # create_summary_text 인자의 korean_name은 "한글 테이블명"
                    # CSV의 description_ko가 "품목 정보 조회" 같다면 description에 넣는 게 맞음.
                    # 하지만 기존 데이터 보면 description_ko에 "Item/BOM Management (품목/BOM 관리)" 같은 게 들어있음.
                    # 이를 description으로 넘김.
                    description=table_csv_info.get('description_ko', ''), 
                    columns=enhanced_columns,
                    domain=table_csv_info.get('domain', ''),
                    keywords=table_csv_info.get('keywords', ''),
                    sample_queries=table_csv_info.get('sample_queries', ''),
                    related_tables=[{'table_name': t.strip()} for t in table_csv_info.get('related_tables', '').split(',') if t.strip()]
                )
                
                # 임베딩 벡터 생성
                embedding = embedding_service.embed_text(summary_text)
                
                # Vector DB 저장
                metadata_dict = {
                    "table_name": table_name,
                    "schema_name": schema_name,
                    "database_sid": db_key,
                    "korean_name": "", # CSV에서 한글명을 따로 분리 안 했으면 description에 포함됨
                    "description": table_csv_info.get('description_ko', ''),
                    "domain": table_csv_info.get('domain', ''),
                    "keywords": table_csv_info.get('keywords', ''),
                    "column_count": len(enhanced_columns),
                    "update_date": datetime.now().isoformat()
                }
                
                vector_store.add_metadata(
                    table_id=f"{db_key}.{schema_name}.{table_name}",
                    summary_text=summary_text,
                    embedding=embedding,
                    metadata=metadata_dict
                )
                processed_count += 1
                
        finally:
            oracle.disconnect()
            
        return {
            "success": True,
            "tables_processed": processed_count,
            "database_sid": db_key,
            "schema_name": schema_name
        }

    except Exception as e:
        logger.error(f"Error in process_metadata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
            table_pks = schema_tables_pks.get(table_name, [])
            matched_columns = []
            table_code_definitions = {}

            for db_col in db_columns:
                col_name = db_col['COLUMN_NAME']
                is_pk = col_name in table_pks

                # Start with DB column info
                column_info = {
                    "column_name": col_name,
                    "data_type": db_col['DATA_TYPE'],
                    "data_length": db_col['DATA_LENGTH'],
                    "nullable": db_col['NULLABLE'],
                    "column_id": db_col['COLUMN_ID'],
                    "is_pk": is_pk,
                    "db_comment": db_col.get('COMMENTS', '')
                }

                # Enhance with CSV metadata if available
                if col_name in common_columns_dict:
                    csv_col = common_columns_dict[col_name]
                    column_info.update({
                        "korean_name": csv_col.get('korean_name', ''),
                        "description": csv_col.get('description', '') or db_col.get('COMMENTS', ''),
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
                    # No CSV metadata, use DB comment if available
                    column_info.update({
                        "korean_name": "",
                        "description": db_col.get('COMMENTS', ''),
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

            # 최적화된 CSV 데이터 병합 (있는 경우)
            if table_name in optimized_metadata_data:
                opt_data = optimized_metadata_data[table_name]
                metadata["description_ko"] = opt_data.get("description_ko", "")
                metadata["domain"] = opt_data.get("domain", "")
                metadata["keywords"] = opt_data.get("keywords", "")
                metadata["sample_queries"] = opt_data.get("sample_queries", "")
                metadata["database_sid"] = database_sid
                metadata["schema_name"] = schema_name
                logger.debug(f"Merged optimized metadata for: {table_name}")

            # 임베딩을 위한 텍스트 생성 (최적화된 필드 포함)
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
                    "description": metadata.get("table_comment", ""),
                    "description_ko": metadata.get("description_ko", ""),
                    "domain": metadata.get("domain", ""),
                    "keywords": metadata.get("keywords", ""),
                    "sample_queries": metadata.get("sample_queries", ""),
                    "column_count": len(metadata.get("columns", [])),
                    "created_at": metadata.get("created_at", ""),
                    # 상세 정보 추가 (JSON 문자열로 저장)
                    "has_primary_key": any(col.get("is_pk") for col in metadata.get("columns", [])),
                    "has_foreign_keys": bool(metadata.get("related_tables")),
                    "key_columns": json.dumps([col for col in metadata.get("columns", []) if col.get("is_pk")], ensure_ascii=False),
                    "related_tables": json.dumps(metadata.get("related_tables", "").split(",") if metadata.get("related_tables") else [], ensure_ascii=False),
                    "business_rules": json.dumps([{"rule": metadata.get("business_purpose", "")}], ensure_ascii=False)
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
    
    ★ 최적화됨: keywords, sample_queries 필드 지원으로 시맨틱 검색 품질 향상
    """
    database_sid = metadata.get("database_sid", "")
    schema_name = metadata.get("schema_name", "")
    table_name = metadata.get("table_name", "")
    table_comment = metadata.get("table_comment", "")
    business_purpose = metadata.get("business_purpose", "")
    usage_scenarios = metadata.get("usage_scenarios", [])
    columns = metadata.get("columns", [])
    
    # 새로운 최적화된 CSV 필드들
    description_ko = metadata.get("description_ko", "") or metadata.get("table_description_ko", "")
    domain = metadata.get("domain", "")
    keywords = metadata.get("keywords", "")
    sample_queries = metadata.get("sample_queries", "")

    text_parts = []
    
    # 1. 헤더 (DB/스키마 정보 포함)
    if database_sid and schema_name:
        text_parts.append(f"[{database_sid}.{schema_name}] 테이블: {table_name}")
    else:
        text_parts.append(f"테이블명: {table_name}")
    text_parts.append("")
    
    # 2. 도메인/업무영역 (새 필드)
    if domain:
        text_parts.append(f"업무영역: {domain}")
    
    # 3. 한국어 설명 (새 필드 우선, 없으면 기존 필드)
    if description_ko:
        text_parts.append(f"설명: {description_ko}")
    elif table_comment:
        text_parts.append(f"설명: {table_comment}")
    
    # 4. 비즈니스 목적
    if business_purpose:
        text_parts.append(f"비즈니스 목적: {business_purpose}")
    text_parts.append("")
    
    # 5. 키워드 (새 필드 - 유사어/동의어 매칭용)
    if keywords:
        text_parts.append(f"관련 키워드: {keywords}")
    
    # 6. 샘플 질문 (새 필드 - 사용자 의도 매칭용)
    if sample_queries:
        queries = [q.strip() for q in sample_queries.split("|") if q.strip()]
        if queries:
            text_parts.append("관련 질문:")
            for q in queries[:5]:
                text_parts.append(f"  - {q}")
    
    # 7. 사용 시나리오 (기존 필드)
    if usage_scenarios and any(usage_scenarios):
        text_parts.append("사용 시나리오:")
        for i, scenario in enumerate(usage_scenarios, 1):
            if scenario:
                text_parts.append(f"  {i}. {scenario}")
    text_parts.append("")

    # 8. 컬럼 정보 (샘플만 포함)
    if columns:
        text_parts.append(f"컬럼 수: {len(columns)}개")
        text_parts.append("주요 컬럼:")
        for col in columns[:10]:
            col_name = col.get("column_name", col.get("name", col.get("COLUMN_NAME", "")))
            korean_name = col.get("korean_name", "")
            description = col.get("description", "")
            if col_name:
                if korean_name or description:
                    text_parts.append(f"  - {col_name} ({korean_name}): {description}")
                else:
                    col_type = col.get("data_type", col.get("DATA_TYPE", ""))
                    text_parts.append(f"  - {col_name} [{col_type}]")

    # 9. 코드 정의 (샘플만 포함)
    code_defs = metadata.get("code_definitions", {})
    if code_defs:
        text_parts.append(f"코드 컬럼 수: {len(code_defs)}개")

    return "\n".join(text_parts)
