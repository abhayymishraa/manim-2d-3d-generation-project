import os
import logging
import subprocess
import tempfile
import glob
import shutil
from .config import settings
from .generator import generate_manim_code
from .supabase_client import update_job_data, upload_to_supabase
from langchain_core.messages import HumanMessage, AIMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RENDER_DIR = settings.RENDER_DIR
MAX_ITERATIONS = 5


def run_manim(code: str, temp_dir: str, quality: str = "m") -> tuple[bool, str]:
    """
    Run Manim code and render the animation in a temporary directory.

    Args:
        code: The Python code to render
        temp_dir: Directory to save the rendered video temporarily
        quality: Render quality (l=low, m=medium, h=high)

    Returns:
        Tuple of (success, error_message or output_file)
    """

    temp_path = None
    try:
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Using temporary directory: {temp_dir}")

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

        cmd = [
            "python",
            "-m",
            "manim",
            temp_path,
            "Scene",
            f"-q{quality}",
            "--format=mp4",
            f"--media_dir={temp_dir}",
        ]

        logger.info(f"Running command: {' '.join(cmd)}")

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

        mp4_files = [
            f
            for f in glob.glob(os.path.join(temp_dir, "**", "*.mp4"), recursive=True)
            if "partial_movie_files" not in f
        ]
        logger.info(f"Found MP4 files: {mp4_files}")

        if not mp4_files:
            logger.error("No MP4 file found after rendering")
            return False, "No MP4 file found after rendering"

        output_file = mp4_files[0]

        logger.info(f"Manim rendering completed successfully: {output_file}")
        return True, output_file

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
    Process a rendering job from start to finish with iterative error correction:
    1. Generate Manim code
    2. Run Manim to create animation in a temp directory
    3. If error occurs, try to fix up to MAX_ITERATIONS times
    4. Upload successful result to Supabase
    5. Clean up temp files
    """
    job_dir = os.path.join(RENDER_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    conversation_history = []
    conversation_history.append(HumanMessage(content=prompt))

    try:
        code = generate_manim_code(prompt)
        conversation_history.append(AIMessage(content=code))

        code_path = os.path.join(job_dir, "code.py")
        with open(code_path, "w") as f:
            f.write(code)

        logger.info(f"Initial code generated for job {job_id}")
    except Exception as e:
        logger.error(f"Error generating initial code for job {job_id}: {str(e)}")
        update_job_data(
            job_id=job_id,
            status="failed",
            prompt=prompt,
            message=f"Code generation failed: {str(e)}",
        )
        with open(os.path.join(job_dir, "status.txt"), "w") as f:
            f.write(f"failed\nCode generation failed: {str(e)}")
        return

    success = False
    result = ""
    final_code = code
    iteration = 0

    while not success and iteration < MAX_ITERATIONS:
        iteration += 1
        logger.info(f"Starting iteration {iteration} for job {job_id}")

        temp_iter_dir = tempfile.mkdtemp(prefix=f"manim_iter_{iteration}_")

        try:

            success, result = run_manim(final_code, temp_iter_dir, quality)

            if success:
                logger.info(f"Successful render on iteration {iteration}")

                final_output_dir = os.path.join(job_dir, "media")
                os.makedirs(final_output_dir, exist_ok=True)

                rel_path = (
                    os.path.relpath(result, RENDER_DIR)
                    if RENDER_DIR in result
                    else result
                )

                target_file = os.path.join(final_output_dir, os.path.basename(result))
                shutil.copy2(result, target_file)

                result = os.path.relpath(target_file, RENDER_DIR)
                break
            else:
                if iteration < MAX_ITERATIONS:
                    error_prompt = f"""
The Manim code failed to render with the following error:
```
{result}
```
Please fix the code to address this error. Only respond with the complete, corrected code - no explanations.
"""
                    conversation_history.append(HumanMessage(content=error_prompt))

                    try:
                        from .generator import generate_code_with_history

                        final_code = generate_code_with_history(conversation_history)
                        conversation_history.append(AIMessage(content=final_code))

                        with open(
                            os.path.join(job_dir, f"code_iter_{iteration}.py"), "w"
                        ) as f:
                            f.write(final_code)

                        with open(code_path, "w") as f:
                            f.write(final_code)

                        logger.info(f"Generated improved code in iteration {iteration}")
                    except Exception as e:
                        logger.error(f"Error generating improved code: {str(e)}")
                        break
        finally:
            try:
                shutil.rmtree(temp_iter_dir)
                logger.info(f"Cleaned up temporary directory: {temp_iter_dir}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_iter_dir}: {str(e)}"
                )

    status_path = os.path.join(job_dir, "status.txt")

    if success:
        try:
            video_full_path = os.path.join(RENDER_DIR, result)
            supabase_url = upload_to_supabase(job_id, video_full_path, final_code)

            update_job_data(
                job_id=job_id,
                status="completed",
                prompt=prompt,
                code=final_code,
                url=supabase_url,
            )

            with open(status_path, "w") as f:
                f.write("completed\n")
                f.write(supabase_url)

            try:
                shutil.rmtree(job_dir)
                logger.info(f"Cleaned up local files for job {job_id}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up local files for job {job_id}: {str(e)}"
                )

            logger.info(
                f"Job {job_id} completed after {iteration} iterations: {supabase_url}"
            )
        except Exception as e:
            logger.error(f"Error finalizing successful job {job_id}: {str(e)}")
            with open(status_path, "w") as f:
                f.write(f"failed\nError finalizing successful job: {str(e)}")
    else:
        update_job_data(
            job_id=job_id,
            status="failed",
            prompt=prompt,
            code=final_code,
            message=f"Failed after {iteration} iterations. Last error: {result}",
        )

        with open(status_path, "w") as f:
            f.write(
                f"failed\nFailed after {iteration} iterations. Last error: {result}"
            )

        logger.info(f"Job {job_id} failed after {iteration} iterations: {result[:100]}")
