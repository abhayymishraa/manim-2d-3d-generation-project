from fastapi import APIRouter, BackgroundTasks, HTTPException
from .schemas import GenerateRequest, GenerateResponse
from .config import settings
from .renderer import process_rendering_job
from .supabase_client import (
    delete_job_data,
    get_job_status,
    get_job_code,
    upload_to_supabase,
    update_job_data,
)
import re
import os
import uuid
import logging
import shutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

RENDER_DIR = settings.RENDER_DIR
logger.info(f"Using render directory: {RENDER_DIR}")

if not os.path.exists(RENDER_DIR):
    try:
        os.makedirs(RENDER_DIR, exist_ok=True)
        logger.info(f"Created render directory: {RENDER_DIR}")
    except Exception as e:
        logger.error(f"Failed to create render directory: {str(e)}")


@router.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate a Manim visualization for the given concept."""

    job_id = f"{uuid.uuid4()}"
    job_dir = os.path.join(RENDER_DIR, job_id)

    try:
        os.makedirs(job_dir, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create job directory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

    status_path = os.path.join(job_dir, "status.txt")
    with open(status_path, "w") as f:
        f.write("pending")

    background_tasks.add_task(
        process_rendering_job,
        job_id=job_id,
        prompt=req.prompt,
        quality=req.quality if hasattr(req, "quality") and req.quality else "m",
    )

    logger.info(f"Started rendering job {job_id} for prompt: {req.prompt[:30]}...")
    return GenerateResponse(
        job_id=job_id,
        status="pending",
        message=f"Job {job_id} started for prompt: {req.prompt[:30]}...",
    )


@router.get("/status/{job_id}", response_model=GenerateResponse)
def get_status(job_id: str):
    """Get the status of a rendering job."""

    # Validate job_id to prevent directory traversal
    if not re.match(r"^[0-9a-f-]+$", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    supabase_response = get_job_status(job_id)

    if supabase_response:
        return GenerateResponse(
            job_id=job_id,
            status=supabase_response["status"],
            message=supabase_response.get("message") or "",
            output_path=supabase_response.get("url"),
        )

    job_dir = os.path.join(RENDER_DIR, job_id)
    status_path = os.path.join(job_dir, "status.txt")

    if not os.path.exists(status_path):
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        with open(status_path, "r") as f:
            lines = f.readlines()

        status = lines[0].strip()
        message = "".join(lines[1:]).strip() if len(lines) > 1 else ""

        # If completed, message contains the relative path to the video
        video_path = None

        if status == "completed" and message:
            full_path = os.path.join(RENDER_DIR, message)

            if not os.path.exists(full_path):
                logger.error(f"Video file not found at: {full_path}")
                status = "failed"
                message = f"Video file not found at: {full_path}"
                video_path = None
            else:
                video_path = message
                logger.info(f"Video file found at: {full_path}")
                if status == "completed" and video_path:

                    full_video_path = os.path.join(RENDER_DIR, video_path)
                    supabase_url = upload_to_supabase(job_id, full_video_path)

                    if supabase_url:
                        update_job_data(job_id, status="completed", url=supabase_url)
                        logger.info(
                            f"Re-uploaded video for job {job_id} to Supabase: {supabase_url}"
                        )
                    else:
                        logger.error(
                            f"Failed to re-upload video for job {job_id} to Supabase"
                        )

        return GenerateResponse(
            job_id=job_id,
            status=status,
            message=message if status != "completed" else "",
            output_path=video_path,
        )
    except Exception as e:
        logger.error(f"Error reading status for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error reading job status: {str(e)}"
        )


@router.get("/code/{job_id}")
def get_code(job_id: str):
    """Get the generated code for a job."""
    # Validate job_id to prevent directory traversal
    if not re.match(r"^[0-9a-f-]+$", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    supabase_code = get_job_code(job_id)
    if supabase_code:
        return {"job_id": job_id, "code": supabase_code}

    job_dir = os.path.join(RENDER_DIR, job_id)
    code_path = os.path.join(job_dir, "code.py")

    if not os.path.exists(code_path):
        raise HTTPException(status_code=404, detail="Code not found for this job")

    try:
        with open(code_path, "r") as f:
            code = f.read()

        return {"job_id": job_id, "code": code}
    except Exception as e:
        logger.error(f"Error reading code for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error reading code: {str(e)}")


@router.delete("/job/{job_id}")
def delete_job(job_id: str):
    """Delete all files associated with a job."""
    # Validate job_id to prevent directory traversal
    if not re.match(r"^[0-9a-f-]+$", job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    delete_status = delete_job_data(job_id)

    job_dir = os.path.join(RENDER_DIR, job_id)
    local_deleted = False

    if os.path.exists(job_dir):
        try:
            shutil.rmtree(job_dir)
            local_deleted = True
        except Exception as e:
            logger.error(f"Error deleting job {job_id} locally: {str(e)}")

    if delete_status or local_deleted:
        return {"status": "success", "message": f"Job {job_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")
