import re
import logging
import os
import shutil
from datetime import datetime, timedelta
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RENDER_DIR = settings.RENDER_DIR


def validate_job_id(job_id: str) -> bool:
    """
    Validate that a job ID has the correct format (UUID).

    Args:
        job_id: Job ID to validate

    Returns:
        True if valid, False otherwise
    """
    return bool(re.match(r"^[0-9a-f-]+$", job_id))


def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Clean up old job directories that are older than the specified age.

    Args:
        max_age_hours: Maximum age of job directories in hours
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for item in os.listdir(RENDER_DIR):
            job_dir = os.path.join(RENDER_DIR, item)

            if not os.path.isdir(job_dir):
                continue

            mod_time = datetime.fromtimestamp(os.path.getmtime(job_dir))

            if mod_time < cutoff_time:
                try:
                    shutil.rmtree(job_dir)
                    logger.info(f"Cleaned up old job directory: {item}")
                except Exception as e:
                    logger.error(
                        f"Failed to clean up old job directory {item}: {str(e)}"
                    )

        logger.info(f"Finished cleaning up old job directories")

    except Exception as e:
        logger.error(f"Error cleaning up old job directories: {str(e)}")


def get_job_path(job_id: str) -> str:
    """
    Get the full path to a job directory.

    Args:
        job_id: Job ID

    Returns:
        Full path to the job directory
    """
    return os.path.join(RENDER_DIR, job_id)
