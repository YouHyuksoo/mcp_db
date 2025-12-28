"""Dashboard-related Pydantic models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class VectorDBStats(BaseModel):
    """Vector database collection statistics"""
    metadata_count: int = Field(..., description="Number of metadata entries")
    patterns_count: int = Field(..., description="Number of learned patterns")
    business_rules_count: int = Field(..., description="Number of business rules")


class DatabaseInfo(BaseModel):
    """Registered database information"""
    database_sid: str = Field(..., description="Database SID")
    schema_name: str = Field(..., description="Schema name")
    table_count: int = Field(..., description="Number of tables in metadata")
    last_updated: Optional[str] = Field(None, description="Last metadata update timestamp")
    connection_status: str = Field("unknown", description="Connection status: active/inactive/unknown")


class UploadedFile(BaseModel):
    """Uploaded file information"""
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="File type: csv/powerbuilder")
    upload_time: str = Field(..., description="Upload timestamp")
    file_size: int = Field(..., description="File size in bytes")
    processing_status: str = Field(..., description="Processing status: pending/processing/completed/failed")
    rules_extracted: Optional[int] = Field(None, description="Number of business rules extracted")


class PatternSummary(BaseModel):
    """SQL pattern summary information"""
    pattern_id: str
    question: str
    database_sid: str
    schema_name: str
    use_count: int
    success_rate: float
    learned_at: str


class DashboardSummary(BaseModel):
    """Complete dashboard summary"""
    vector_db_stats: VectorDBStats
    registered_databases: List[DatabaseInfo]
    recent_patterns: List[PatternSummary]
    upload_history: List[UploadedFile]
    total_databases: int
    total_patterns: int
    total_uploads: int


class DatabaseListResponse(BaseModel):
    """Response for database listing"""
    databases: List[DatabaseInfo]
    total_count: int
