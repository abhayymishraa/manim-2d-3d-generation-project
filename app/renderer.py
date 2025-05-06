import os
import logging
import subprocess
import tempfile
import glob
from datetime import datetime
from .config import settings
from .generator import generate_manim_code
from .supabase_client import update_job_data, upload_to_supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RENDER_DIR = settings.RENDER_DIR


def run_manim(
    code: str, job_id: str, output_path: str, quality: str = "m"
) -> tuple[bool, str]:
    """
    Run Manim code and render the animation.

    Args:
        code: The Python code to render
        job_id: Unique job identifier
        output_path: Directory to save the rendered video
        quality: Render quality (l=low, m=medium, h=high)

    Returns:
        Tuple of (success, error_message or output_file)
    """

    temp_path = None
    try:
        job_output_dir = os.path.join(output_path, job_id)
        os.makedirs(job_output_dir, exist_ok=True)

        logger.info(f"Created job directory: {job_output_dir}")

        # Create a temporary Python file with explicit cleanup
        try:
            with tempfile.NamedTemporaryFile(
                suffix=".py", mode="w", delete=False
            ) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name
                logger.info(f"Created temporary file: {temp_path}")
        except Exception as e:
            logger.error(f"Failed to create temporary file: {str(e)}")
            return False, f"Failed to create temporary file: {str(e)}"

        # Run Manim command
        cmd = [
            "python",
            "-m",
            "manim",
            temp_path,
            "Scene",
            f"-q{quality}",
            "--format=mp4",
            f"--media_dir={job_output_dir}",
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

        # Execute the command with timeout (4 minutes)
        try:
            process = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=240
            )

        except subprocess.TimeoutExpired:
            logger.error("Manim rendering timed out after 240 seconds")
            return False, "Rendering timed out after 240 seconds"

        logger.info(f"Manim stdout: {process.stdout}")
        logger.error(f"Manim stderr: {process.stderr}")

        if process.returncode != 0:
            logger.error(f"Manim rendering failed with exit code {process.returncode}")
            return False, process.stderr

        mp4_files = glob.glob(
            os.path.join(job_output_dir, "**", "Scene.mp4"), recursive=True
        )
        logger.info(f"Found MP4 files: {mp4_files}")

        if not mp4_files:
            logger.error("No MP4 file found after rendering")
            return False, "No MP4 file found after rendering"

        output_file = mp4_files[0]
        rel_path = os.path.relpath(output_file, RENDER_DIR)

        logger.info(f"Manim rendering completed successfully: {rel_path}")
        return True, rel_path

    except Exception as e:
        error_msg = f"Error running Manim: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"Removed temporary file: {temp_path}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary file {temp_path}: {str(e)}"
                )


def process_rendering_job(job_id: str, prompt: str, quality: str):
    """
    Process a rendering job from start to finish:
    1. Generate Manim code
    2. Run Manim to create animation
    3. Upload result to Supabase
    4. Clean up local files
    """
    try:
        job_dir = os.path.join(RENDER_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        code = generate_manim_code(prompt)
        code_path = os.path.join(job_dir, "code.py")
        with open(code_path, "w") as f:
            f.write(code)

        logger.info(f"Starting Manim render for job {job_id}")

        success, result = run_manim(code, job_id, RENDER_DIR, quality)
        logger.info(f"Manim render finished with success={success}")

        status_path = os.path.join(job_dir, "status.txt")

        if success:

            video_full_path = os.path.join(RENDER_DIR, result)
            supabase_url = upload_to_supabase(job_id, video_full_path, code)

            update_job_data(
                job_id=job_id,
                status="completed",
                prompt=prompt,
                code=code,
                url=supabase_url,
            )

            with open(status_path, "w") as f:
                f.write("completed\n")
                f.write(supabase_url)

            logger.info(f"Job {job_id} completed: {supabase_url}")

            try:
                import shutil

                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up local files for job {job_id}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up local files for job {job_id}: {str(e)}"
                )

        else:
            update_job_data(
                job_id=job_id, status="failed", prompt=prompt, code=code, message=result
            )

            with open(status_path, "w") as f:
                f.write(f"failed\n{result}")

            logger.info(f"Job {job_id} failed: {result[:100]}")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")

        job_dir = os.path.join(RENDER_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        try:
            update_job_data(
                job_id=job_id, status="failed", prompt=prompt, message=str(e)
            )
        except Exception as supabase_err:
            logger.error(
                f"Failed to update Supabase for job {job_id}: {str(supabase_err)}"
            )

        with open(os.path.join(job_dir, "status.txt"), "w") as f:
            f.write(f"failed\n{str(e)}")
