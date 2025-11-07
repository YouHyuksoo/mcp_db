"""SQL pattern-related Pydantic models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LearnPatternRequest(BaseModel):
    """Request to learn a new SQL pattern"""
    question: str = Field(..., description="Natural language question")
    sql_query: str = Field(..., description="Generated SQL query")
    database_sid: str = Field(..., description="Database SID")
    schema_name: str = Field(..., description="Schema name")
    tables_used: List[str] = Field(..., description="List of tables used")
    execution_success: bool = Field(True, description="Whether query executed successfully")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in ms")
    row_count: Optional[int] = Field(None, description="Number of rows returned")
    user_feedback: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")


class LearnPatternResponse(BaseModel):
    """Response for pattern learning"""
    success: bool
    pattern_id: str
    message: str


class FindSimilarPatternRequest(BaseModel):
    """Request to find similar patterns"""
    question: str = Field(..., description="Natural language question")
    database_sid: str = Field(..., description="Database SID")
    schema_name: str = Field(..., description="Schema name")
    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Similarity threshold")
    min_success_rate: float = Field(0.8, ge=0.0, le=1.0, description="Minimum success rate")


class PatternMatch(BaseModel):
    """A matching SQL pattern"""
    pattern_id: str
    question: str
    sql_query: str
    similarity: float
    success_rate: float
    overall_score: float
    use_count: int


class FindSimilarPatternResponse(BaseModel):
    """Response for finding similar patterns"""
    found_match: bool
    pattern: Optional[PatternMatch] = None
    message: str


class PatternInfo(BaseModel):
    """Information about a SQL pattern"""
    pattern_id: str
    question: str
    sql_query: str
    database_sid: str
    schema_name: str
    use_count: int
    success_rate: float
    avg_execution_time_ms: Optional[float] = None
    avg_user_rating: Optional[float] = None
    learned_at: str
    last_used_at: Optional[str] = None


class ListPatternsResponse(BaseModel):
    """Response for listing patterns"""
    patterns: List[PatternInfo]
    total_count: int


class PatternFeedbackRequest(BaseModel):
    """Request to record pattern feedback"""
    pattern_id: str = Field(..., description="Pattern ID")
    execution_success: bool = Field(..., description="Whether execution succeeded")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating (1-5)")


class PatternStatsResponse(BaseModel):
    """Response for pattern statistics"""
    total_patterns: int
    avg_success_rate: float
    total_reuses: int
    estimated_llm_calls_saved: int
