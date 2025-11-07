"""
PowerBuilder Upload and Processing API Endpoints
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from typing import List
from app.models.powerbuilder import (
    PowerBuilderProcessResponse,
    PowerBuilderJobStatus,
    PowerBuilderSummary
)
from app.core.powerbuilder_parser import PowerBuilderParser
from app.core.legacy_analyzer import LegacyAnalyzer
import logging
import uuid
from pathlib import Path
import shutil
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory job tracking (in production, use Redis or database)
jobs = {}


async def process_powerbuilder_files_background(
    job_id: str,
    file_paths: List[str],
    database_sid: str,
    schema_name: str,
    vector_store,
    embedding_service
):
    """Background task to process PowerBuilder files"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["started_at"] = datetime.utcnow().isoformat()

        # Initialize parser and analyzer
        pb_parser = PowerBuilderParser()
        legacy_analyzer = LegacyAnalyzer(vector_store, embedding_service, pb_parser)

        # Process files
        result = await legacy_analyzer.process_powerbuilder_files(
            file_paths=file_paths,
            database_sid=database_sid,
            schema_name=schema_name
        )

        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress_percent"] = 100
        jobs[job_id]["files_processed"] = result["files_processed"]
        jobs[job_id]["sql_queries_extracted"] = result["sql_queries_extracted"]
        jobs[job_id]["business_rules_extracted"] = result["business_rules_extracted"]
        jobs[job_id]["tables_discovered"] = result["table_list"]
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

        logger.info(f"Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["completed_at"] = datetime.utcnow().isoformat()

    finally:
        # Cleanup uploaded files
        for file_path in file_paths:
            try:
                Path(file_path).unlink()
            except:
                pass


@router.post("/upload", response_model=PowerBuilderProcessResponse)
async def upload_powerbuilder_files(
    background_tasks: BackgroundTasks,
    request: Request,
    files: List[UploadFile] = File(...),
    database_sid: str = Form(...),
    schema_name: str = Form(...)
):
    """
    Upload PowerBuilder files (.srw, .srd, .pbl) for processing

    The files will be parsed in the background to extract SQL queries,
    business rules, and table relationships.
    """
    try:
        # Validate file extensions
        allowed_extensions = {".srw", ".srd", ".pbl", ".sra"}
        invalid_files = []

        for file in files:
            ext = Path(file.filename).suffix.lower()
            if ext not in allowed_extensions:
                invalid_files.append(file.filename)

        if invalid_files:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file types: {', '.join(invalid_files)}. "
                       f"Only .srw, .srd, .pbl, .sra files are allowed."
            )

        # Create upload directory
        upload_dir = Path("./uploads") / str(uuid.uuid4())
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files
        saved_paths = []
        for file in files:
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_paths.append(str(file_path))

        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress_percent": 0,
            "files_processed": 0,
            "sql_queries_extracted": 0,
            "business_rules_extracted": 0,
            "tables_discovered": [],
            "error": None,
            "started_at": None,
            "completed_at": None
        }

        # Start background processing
        background_tasks.add_task(
            process_powerbuilder_files_background,
            job_id,
            saved_paths,
            database_sid,
            schema_name,
            request.app.state.vector_store,
            request.app.state.embedding_service
        )

        logger.info(f"PowerBuilder upload job created: {job_id} ({len(files)} files)")

        return PowerBuilderProcessResponse(
            job_id=job_id,
            status="queued",
            message=f"Processing {len(files)} files in background. Use /jobs/{job_id} to check status."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=PowerBuilderJobStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a PowerBuilder processing job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job_data = jobs[job_id]

    return PowerBuilderJobStatus(
        job_id=job_data["job_id"],
        status=job_data["status"],
        progress_percent=job_data["progress_percent"],
        files_processed=job_data["files_processed"],
        sql_queries_extracted=job_data["sql_queries_extracted"],
        business_rules_extracted=job_data["business_rules_extracted"],
        tables_discovered=job_data["tables_discovered"],
        error=job_data["error"],
        started_at=job_data["started_at"],
        completed_at=job_data["completed_at"]
    )


@router.get("/jobs")
async def list_jobs():
    """
    List all PowerBuilder processing jobs
    """
    return {
        "jobs": list(jobs.values()),
        "total_count": len(jobs)
    }


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from history
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    del jobs[job_id]

    return {
        "success": True,
        "message": f"Job {job_id} deleted"
    }
