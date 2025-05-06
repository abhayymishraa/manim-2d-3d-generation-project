from supabase import create_client
import os
import logging
from datetime import datetime
from .config import settings
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
SUPABASE_BUCKET = settings.SUPABASE_BUCKET

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_to_supabase(job_id: str, file_path: str, code: str = None) -> str:
    """
    Upload a file to Supabase Storage and return the public URL.
    
    Args:
        job_id: Unique job identifier
        file_path: Path to the file to upload
        code: Generated Manim code
        
    Returns:
        Public URL to the uploaded file
    """
    try:
        if not os.path.exists(file_path):
            logger.error(f"File not found for upload: {file_path}")
            return None
            
        _, file_extension = os.path.splitext(file_path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        remote_path = f"manim/{job_id}_{timestamp}{file_extension}"
        
        with open(file_path, "rb") as f:
            file_data = f.read()
            
        response = supabase.storage.from_(SUPABASE_BUCKET).upload(
            remote_path,
            file_data,
            file_options={"content-type": "video/mp4"}
        )
        
        file_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(remote_path)
        
        logger.info(f"File uploaded to Supabase: {file_url}")
        return file_url
        
    except Exception as e:
        logger.error(f"Error uploading to Supabase: {str(e)}")
        return None


def update_job_data(job_id: str, status: str, prompt: str = None, code: str = None, url: str = None, message: str = None):
    """
    Update job data in Supabase database.
    
    Args:
        job_id: Unique job identifier
        status: Job status (pending, completed, failed)
        prompt: The prompt used to generate the animation
        code: Generated Manim code
        url: URL to the rendered video
        message: Error message if status is 'failed'
    """
    try:
        job_data = {
            "id": job_id,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        if prompt:
            job_data["prompt"] = prompt
        if code:
            job_data["code"] = code
        if url:
            job_data["url"] = url
        if message:
            job_data["message"] = message
            
        response = supabase.table("manim_jobs").upsert(job_data).execute()
        
        logger.info(f"Updated job data in Supabase for job {job_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error updating job data in Supabase: {str(e)}")
        return None


def get_job_status(job_id: str):
    """
    Get job status from Supabase.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Job data or None if not found
    """
    try:
        response = supabase.table("manim_jobs").select("*").eq("id", job_id).execute()
        
        if response.data and len(response.data) > 0:
            logger.info(f"Retrieved job status from Supabase for job {job_id}")
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting job status from Supabase: {str(e)}")
        return None


def get_job_code(job_id: str):
    """
    Get job code from Supabase.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Code string or None if not found
    """
    try:
        response = supabase.table("manim_jobs").select("code").eq("id", job_id).execute()
        
        if response.data and len(response.data) > 0 and "code" in response.data[0]:
            logger.info(f"Retrieved job code from Supabase for job {job_id}")
            return response.data[0]["code"]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting job code from Supabase: {str(e)}")
        return None


def delete_job_data(job_id: str):
    """
    Delete job data and associated files from Supabase.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        True if successful, False otherwise
    """
    try:
        job_data = get_job_status(job_id)
        
        if job_data and "url" in job_data:
            url_parts = job_data["url"].split("/")
            if len(url_parts) > 0:
                file_path = url_parts[-1]
                try:
                    supabase.storage.from_(SUPABASE_BUCKET).remove([f"manim/{file_path}"])
                    logger.info(f"Deleted file from Supabase Storage for job {job_id}")
                except Exception as e:
                    logger.warning(f"Error deleting file from Supabase Storage: {str(e)}")
        
        response = supabase.table("manim_jobs").delete().eq("id", job_id).execute()
        
        logger.info(f"Deleted job data from Supabase for job {job_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting job data from Supabase: {str(e)}")
        return False