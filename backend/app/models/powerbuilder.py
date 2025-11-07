"""PowerBuilder parsing-related Pydantic models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class PowerBuilderUploadRequest(BaseModel):
    """Request for PowerBuilder file upload"""
    database_sid: str = Field(..., description="Database SID")
    schema_name: str = Field(..., description="Schema name")
    # Note: Actual files will be uploaded via multipart/form-data


class PowerBuilderProcessResponse(BaseModel):
    """Response for PowerBuilder processing"""
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    message: str


class PowerBuilderJobStatus(BaseModel):
    """Status of a PowerBuilder processing job"""
    job_id: str
    status: str
    progress_percent: int = Field(0, ge=0, le=100)
    files_processed: int = 0
    sql_queries_extracted: int = 0
    business_rules_extracted: int = 0
    tables_discovered: List[str] = []
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class PowerBuilderSummary(BaseModel):
    """Summary of PowerBuilder extraction"""
    files_processed: int
    tables_discovered: int
    table_list: List[str]
    sql_queries_extracted: int
    business_rules_extracted: int
    relationships_discovered: int
    total_knowledge_entries: int
    complexity_score: str  # "low", "medium", "high", "very_high"
