import logging
import time
import threading
from .utils import cleanup_old_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLEANUP_INTERVAL = 12 * 60 * 60

MAX_JOB_AGE = 24


def cleanup_thread():
    """Background thread to periodically clean up old job directories."""
    while True:
        try:
            logger.info("Starting scheduled cleanup of old job directories")
            cleanup_old_jobs(max_age_hours=MAX_JOB_AGE)
            logger.info(
                f"Cleanup complete, next cleanup in {CLEANUP_INTERVAL/3600} hours"
            )
        except Exception as e:
            logger.error(f"Error during scheduled cleanup: {str(e)}")

        time.sleep(CLEANUP_INTERVAL)


def start_cleanup_scheduler():
    """Start the cleanup scheduler in a background thread."""
    thread = threading.Thread(target=cleanup_thread, daemon=True)
    thread.start()
    logger.info("Started cleanup scheduler thread")
