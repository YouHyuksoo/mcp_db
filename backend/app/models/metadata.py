"""Metadata-related Pydantic models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class MetadataSearchRequest(BaseModel):
    """Request for metadata search"""
    question: str = Field(..., description="Natural language question")
    database_sid: Optional[str] = Field(None, description="Filter by database SID")
    schema_name: Optional[str] = Field(None, description="Filter by schema name")
    limit: int = Field(5, ge=1, le=20, description="Number of results to return")


class MetadataSearchResult(BaseModel):
    """Single metadata search result"""
    table_id: str
    table_name: str
    schema_name: str
    database_sid: str
    korean_name: Optional[str] = None
    description: Optional[str] = None
    similarity_score: float
    column_count: int


class MetadataSearchResponse(BaseModel):
    """Response for metadata search"""
    results: List[MetadataSearchResult]
    total_found: int
    query: str


class MigrationRequest(BaseModel):
    """Request for metadata migration"""
    metadata_dir: str = Field(..., description="Path to metadata directory")
    database_sid: str = Field(..., description="Database SID")
    schema_name: str = Field(..., description="Schema name")


class MigrationResponse(BaseModel):
    """Response for metadata migration"""
    success: bool
    tables_migrated: int
    database_sid: str
    schema_name: str
    error: Optional[str] = None
