import requests
import time
import os

# API endpoints
BASE_URL = "http://localhost:8000/api"
GENERATE_URL = f"{BASE_URL}/generate"
STATUS_URL = f"{BASE_URL}/status"
CODE_URL = f"{BASE_URL}/code"


def generate_visualization(prompt, quality="m"):
    """Submit a request to generate a visualization."""
    response = requests.post(GENERATE_URL, json={"prompt": prompt, "quality": quality})
    return response.json()


def check_status(job_id):
    """Check the status of a rendering job."""
    response = requests.get(f"{STATUS_URL}/{job_id}")
    return response.json()


def get_code(job_id):
    """Get the generated code for a job."""
    response = requests.get(f"{CODE_URL}/{job_id}")
    return response.json()


def wait_for_completion(job_id, polling_interval=5, timeout=300):
    """Wait for a job to complete, polling at the specified interval."""
    start_time = time.time()
    while True:
        status_info = check_status(job_id)

        if status_info["status"] == "completed":
            print(f"Job completed! Output: {status_info.get('output_path')}")
            return status_info

        if status_info["status"] == "failed":
            print(f"Job failed: {status_info.get('message')}")
            return status_info

        elapsed = time.time() - start_time
        if elapsed > timeout:
            print(f"Timeout after {timeout} seconds")
            return None

        print(f"Job still processing... ({elapsed:.1f}s elapsed)")
        time.sleep(polling_interval)


if __name__ == "__main__":
    # Example usage
    prompt = "Show me a visualization of the Pythagorean theorem"

    # Generate the visualization
    print(f"Requesting visualization for: {prompt}")
    result = generate_visualization(prompt)
    print(f"Request submitted: {result}")

    job_id = result["job_id"]

    # Wait for completion
    final_status = wait_for_completion(job_id)

    if final_status and final_status["status"] == "completed":
        # Get the code
        code_result = get_code(job_id)
        print("\nGenerated Manim code:")
        print("-" * 40)
        print(code_result["code"])
        print("-" * 40)
