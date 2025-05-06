const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export async function generateManimVisualization(prompt: string, quality: string) {
  const response = await fetch(`${API_BASE_URL}/api/manim/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt, quality }),
  })

  if (!response.ok) {
    throw new Error("Failed to generate visualization")
  }

  return response.json()
}

export async function getJobStatus(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/api/manim/status/${jobId}`)

  if (!response.ok) {
    throw new Error("Failed to get job status")
  }

  return response.json()
}

export async function getJobCode(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/api/manim/code/${jobId}`)

  if (!response.ok) {
    throw new Error("Failed to get job code")
  }

  return response.json()
}

export async function deleteJob(jobId: string) {
  const response = await fetch(`${API_BASE_URL}/api/manim/job/${jobId}`, {
    method: "DELETE",
  })

  if (!response.ok) {
    throw new Error("Failed to delete job")
  }

  return response.json()
}