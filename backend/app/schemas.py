from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    """Request model for generating Manim visualizations."""

    prompt: str
    quality: str = "m"  # l=low, m=medium, h=high


class GenerateResponse(BaseModel):
    """Response model for generation status and results."""

    job_id: str
    status: str  # "pending", "completed", "failed"
    message: str = ""
    output_path: Optional[str] = None
