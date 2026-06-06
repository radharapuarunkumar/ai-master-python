from fastapi import APIRouter, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.common import ResponseEnvelope

router = APIRouter(prefix="/jobs", tags=["Jobs"])

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    type: str  # e.g., "Full-time", "Internship"
    description: str
    apply_url: str
    posted_at: str

# Sample Data
SAMPLE_JOBS = [
    JobListing(
        id="job-1",
        title="Junior Python Backend Engineer",
        company="TechCorp Inc.",
        location="Remote",
        type="Full-time",
        description="Looking for a junior python engineer with FastAPI experience.",
        apply_url="https://example.com/apply/job-1",
        posted_at="2 days ago"
    ),
    JobListing(
        id="job-2",
        title="Python Developer Intern",
        company="AI Startup",
        location="New York, NY",
        type="Internship",
        description="Learn and grow with our AI team. Python, Pandas, and Flask required.",
        apply_url="https://example.com/apply/job-2",
        posted_at="1 week ago"
    ),
    JobListing(
        id="job-3",
        title="Backend Software Engineer",
        company="Global Systems",
        location="San Francisco, CA",
        type="Full-time",
        description="Seeking an engineer to work on scalable microservices using Python.",
        apply_url="https://example.com/apply/job-3",
        posted_at="3 days ago"
    )
]

@router.get("", response_model=ResponseEnvelope[List[JobListing]])
async def get_jobs(job_type: Optional[str] = None):
    """List jobs and internships."""
    jobs = SAMPLE_JOBS
    if job_type:
        jobs = [j for j in jobs if j.type.lower() == job_type.lower()]
    return ResponseEnvelope(data=jobs)
