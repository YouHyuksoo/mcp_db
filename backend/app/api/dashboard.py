"""Dashboard API endpoints"""

from fastapi import APIRouter, HTTPException, Request
from typing import List
import logging

from app.models.dashboard import (
    DashboardSummary,
    DatabaseListResponse,
    VectorDBStats,
    DatabaseInfo,
    PatternSummary,
    UploadedFile
)

# Import CredentialsManager from mcp directory using importlib
import importlib.util
project_root = Path(__file__).parent.parent.parent.parent
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

# Import OracleConnector
oracle_connector_spec = importlib.util.spec_from_file_location(
    "oracle_connector",
    mcp_path / "oracle_connector.py"
)
if oracle_connector_spec and oracle_connector_spec.loader:
    oracle_connector_module = importlib.util.module_from_spec(oracle_connector_spec)
    oracle_connector_spec.loader.exec_module(oracle_connector_module)
    OracleConnector = oracle_connector_module.OracleConnector  # type: ignore

logger = logging.getLogger(__name__)

# Global manager
credentials_dir = project_root / "data" / "credentials"
credentials_manager = CredentialsManager(credentials_dir=str(credentials_dir))

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request):
    """
    Get comprehensive dashboard summary

    Returns:
        - Vector DB statistics
        - Registered databases
        - Recent patterns
        - Upload history
    """
    try:
        vector_store = request.app.state.vector_store

        # Get Vector DB statistics
        stats = vector_store.get_stats()
        vector_db_stats = VectorDBStats(
            metadata_count=stats["metadata_count"],
            patterns_count=stats["patterns_count"],
            business_rules_count=stats["business_rules_count"]
        )

        # Get registered database SIDs from credentials manager
        registered_sids = credentials_manager.list_databases()
        
        # Get Vector DB metadata for mapping table counts
        databases_raw = vector_store.get_all_databases()
        vector_db_map = {f"{db['database_sid']}": db for db in databases_raw}

        registered_databases = []
        for sid in registered_sids:
            try:
                creds = credentials_manager.load_credentials(sid)
                vector_info = vector_db_map.get(sid, {})
                
                # Check actual connection (simple health check)
                is_connected = False
                try:
                    connector = OracleConnector(
                        host=creds['host'],
                        port=creds['port'],
                        service_name=creds['service_name'],
                        user=creds['user'],
                        password=creds['password']
                    )
                    # We don't want to block too long, but simple connect/disconnect
                    is_connected = connector.connect()
                    if is_connected:
                        connector.disconnect()
                except:
                    is_connected = False

                registered_databases.append(DatabaseInfo(
                    database_sid=sid,
                    schema_name=creds.get('schema_name', creds.get('user', 'unknown').upper()),
                    table_count=vector_info.get("table_count", 0),
                    last_updated=vector_info.get("last_updated"),
                    connection_status="connected" if is_connected else "disconnected"
                ))
            except Exception as e:
                logger.error(f"Failed to process dashboard info for {sid}: {e}")
                continue

        # Get recent patterns
        patterns_raw = vector_store.get_recent_patterns(limit=10)
        recent_patterns = [
            PatternSummary(
                pattern_id=p["pattern_id"],
                question=p["question"],
                database_sid=p["database_sid"],
                schema_name=p["schema_name"],
                use_count=p["use_count"],
                success_rate=p["success_rate"],
                learned_at=p["learned_at"]
            )
            for p in patterns_raw
        ]

        # Get upload history from business rules collection
        upload_history_raw = vector_store.get_business_rules_summary()
        upload_history = [
            UploadedFile(
                file_name=upload["source"],
                file_type=upload["source_type"],
                upload_time=upload.get("last_updated", ""),
                file_size=0,  # Not stored in current implementation
                processing_status="completed",
                rules_extracted=upload["rule_count"]
            )
            for upload in upload_history_raw
        ]

        return DashboardSummary(
            vector_db_stats=vector_db_stats,
            registered_databases=registered_databases,
            recent_patterns=recent_patterns,
            upload_history=upload_history,
            total_databases=len(registered_databases),
            total_patterns=stats["patterns_count"],
            total_uploads=len(upload_history)
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases", response_model=DatabaseListResponse)
async def list_databases(request: Request):
    """
    List all registered databases

    Returns:
        List of databases with metadata statistics
    """
    try:
        vector_store = request.app.state.vector_store

        # Consolidate with credentials manager
        registered_sids = credentials_manager.list_databases()
        databases_raw = vector_store.get_all_databases()
        vector_db_map = {f"{db['database_sid']}": db for db in databases_raw}

        databases = []
        for sid in registered_sids:
            try:
                creds = credentials_manager.load_credentials(sid)
                vector_info = vector_db_map.get(sid, {})
                
                # Simple connection check
                is_connected = False
                try:
                    connector = OracleConnector(
                        host=creds['host'],
                        port=creds['port'],
                        service_name=creds['service_name'],
                        user=creds['user'],
                        password=creds['password']
                    )
                    is_connected = connector.connect()
                    if is_connected:
                        connector.disconnect()
                except:
                    pass

                databases.append(DatabaseInfo(
                    database_sid=sid,
                    schema_name=creds.get('schema_name', creds.get('user', 'unknown').upper()),
                    table_count=vector_info.get("table_count", 0),
                    last_updated=vector_info.get("last_updated"),
                    connection_status="connected" if is_connected else "disconnected"
                ))
            except:
                continue

        return DatabaseListResponse(
            databases=databases,
            total_count=len(databases)
        )

    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))
