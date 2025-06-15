from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from scraper.naukri_scraper import NaukriScraper
from scraper.company_scraper import CompanyScraper
from datetime import datetime
from vector_search.semantic_matcher import SemanticMatcher
from functools import lru_cache
import faiss
import numpy as np
from matcher.matcher import keyword_match_jobs
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pathlib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- START: NEXT.JS SERVING LOGIC ---
# Define the path to the frontend's build directory
frontend_dir = pathlib.Path(__file__).parent / "frontend"
# The static assets are in .next/static
static_dir = frontend_dir / ".next" / "static"

# Mount the static assets from the .next/static directory
# The path MUST be "/_next/static" for Next.js to find its assets
app.mount("/_next/static", StaticFiles(directory=static_dir), name="next-static")
# --- END: NEXT.JS SERVING LOGIC ---

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'jobs.json')

# Initialize semantic matcher with optimizations
matcher = SemanticMatcher()
index_dir = "data/vector_index"

# Load or create index on startup
@app.on_event("startup")
async def startup_event():
    jobs_path = "data/jobs.json"
    
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(jobs_path), exist_ok=True)

    if os.path.exists(os.path.join(index_dir, "jobs.index")):
        matcher.load_index(index_dir)
    else:
        # If jobs.json exists and is not empty, build the index from it.
        if os.path.exists(jobs_path) and os.path.getsize(jobs_path) > 0:
            try:
                with open(jobs_path, 'r') as f:
                    jobs = json.load(f)
                if jobs:
                    matcher.batch_index_jobs(jobs, batch_size=1000)
                    matcher.save_index(index_dir)
            except (json.JSONDecodeError, FileNotFoundError):
                print("Could not build index. File 'jobs.json' might be corrupt or missing.")
        else:
            print("'jobs.json' not found or is empty. Starting with an empty search index.")
            # Optional: Create an empty jobs file if it doesn't exist
            if not os.path.exists(jobs_path):
                with open(jobs_path, 'w') as f:
                    json.dump([], f)

class JobSearchRequest(BaseModel):
    title: Optional[str] = None
    experience: Optional[int] = None
    location: Optional[str] = None
    use_semantic_search: bool = True
    min_similarity: float = 0.6  # Minimum similarity threshold

class JobResult(BaseModel):
    title: str
    company: str
    location: Optional[str]
    date: str
    url: str
    skills: List[str]
    description: str

class JobResponse(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    skills: List[str]
    date: Optional[str] = None
    url: str
    description: str
    similarity_score: Optional[float] = None

# Cache frequently used search results
@lru_cache(maxsize=1000)
def cached_search(query: str, k: int = 10):
    return matcher.search_jobs(query, k=k)

@app.post("/search_jobs", response_model=List[JobResponse])
async def search_jobs(request: JobSearchRequest):
    try:
        # Load jobs from JSON
        with open("data/jobs.json", "r") as f:
            jobs = json.load(f)

        if request.use_semantic_search and request.title:
            # Use cached semantic search (remove min_similarity)
            results = cached_search(
                request.title, 
                k=10
            )
            matched_jobs = []
            for job, score in results:
                # Apply filters if provided
                if request.experience and job.get("min_experience", 0) > request.experience:
                    continue
                if request.location and request.location.lower() not in job.get("location", "").lower():
                    continue
                
                # Convert to response format
                job_response = JobResponse(
                    title=job["title"],
                    company=job["company"],
                    location=job.get("location"),
                    skills=job.get("skills", []),
                    date=job.get("date"),
                    url=job["url"],
                    description=job.get("description", ""),
                    similarity_score=score
                )
                matched_jobs.append(job_response)
            
            return matched_jobs
        else:
            # Use traditional filtering
            matched_jobs = []
            for job in jobs:
                # Apply filters
                if request.title and request.title.lower() not in job["title"].lower():
                    continue
                if request.experience and job.get("min_experience", 0) > request.experience:
                    continue
                if request.location and request.location.lower() not in job.get("location", "").lower():
                    continue

                # Convert to response format
                job_response = JobResponse(
                    title=job["title"],
                    company=job["company"],
                    location=job.get("location"),
                    skills=job.get("skills", []),
                    date=job.get("date"),
                    url=job["url"],
                    description=job.get("description", ""),
                    similarity_score=None
                )
                matched_jobs.append(job_response)
            
            return matched_jobs

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match_resume", response_model=List[JobResponse])
async def match_resume(resume: dict):
    try:
        min_similarity = resume.pop("min_similarity", 0.0)
        # Use semantic matcher to find matching jobs with minimum similarity threshold
        results = matcher.match_resume_to_jobs(resume, k=10, min_similarity=min_similarity)
        # Convert to response format
        matched_jobs = []
        for job, score in results:
            job_response = JobResponse(
                title=job["title"],
                company=job["company"],
                location=job.get("location"),
                skills=job.get("skills", []),
                date=job.get("date"),
                url=job["url"],
                description=job.get("description", ""),
                similarity_score=score
            )
            matched_jobs.append(job_response)
        return matched_jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape_and_save_jobs", response_model=List[JobResult])
def scrape_and_save_jobs(req: JobSearchRequest):
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Run NaukriScraper
    naukri_scraper = NaukriScraper()
    naukri_jobs = naukri_scraper.search_jobs(
        keyword=req.title,
        location=req.location,
        experience=req.experience,
        page=1,
        limit=20
    )
    naukri_results = [
        {
            "title": job.get("title") or "",
            "company": job.get("company") or "",
            "location": job.get("location") or "",
            "date": job.get("posted_date") or job.get("scraped_at") or "",
            "url": job.get("job_url") or "",
            "skills": job.get("skills", []) if isinstance(job.get("skills", []), list) else [s.strip() for s in job.get("skills", "").split(",") if s.strip()],
            "description": job.get("description") if isinstance(job.get("description"), str) and job.get("description") is not None else ""
        }
        for job in naukri_jobs
    ]

    # Run CompanyScraper
    # Use job_title if available, else fallback to title, else empty string
    job_title = getattr(req, 'job_title', None) or req.title or ""
    company_scraper = CompanyScraper()
    company_jobs = company_scraper.scrape_all_companies(
        keyword=job_title,
        location=req.location or ""
    )
    company_results = []
    for jobs in company_jobs.values():
        for job in jobs:
            company_results.append({
                "title": job.get("title") or "",
                "company": job.get("company") or "",
                "location": job.get("location") or "",
                "date": job.get("scraped_at") or "",
                "url": job.get("url") or "",
                "skills": job.get("skills", []) if isinstance(job.get("skills", []), list) else [s.strip() for s in job.get("skills", "").split(",") if s.strip()],
                "description": job.get("description") if isinstance(job.get("description"), str) and job.get("description") is not None else ""
            })

    # Combine and deduplicate by URL
    all_results = naukri_results + company_results
    seen_urls = set()
    deduped_results = []
    for job in all_results:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped_results.append(job)

    # Save to /data/jobs.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(deduped_results, f, ensure_ascii=False, indent=2)

    return deduped_results

@app.post("/match_resume_keyword", response_model=List[dict])
async def match_resume_keyword(resume: dict, n: int = 5):
    try:
        # Load jobs from JSON
        with open("data/jobs.json", "r") as f:
            jobs = json.load(f)
        # Get top N keyword matches
        matches = keyword_match_jobs(resume, jobs, n)
        # Format response
        results = []
        for match in matches:
            job = match["job"]
            results.append({
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "skills": job.skills,
                "date": job.date,
                "url": job.url,
                "description": job.description,
                "score": match["score"],
                "matched_skills": match["matched_skills"],
                "location_match": match["location_match"],
                "exp_match": match["exp_match"],
                "about_match": match["about_match"]
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/{full_path:path}")
async def serve_next_app(full_path: str):
    """
    Serve the Next.js app.
    This catch-all route handles all other requests and serves the Next.js app,
    allowing client-side routing to take over.
    """
    # The main entry point for the Next.js App Router
    index_path = pathlib.Path(__file__).parent / "frontend" / ".next" / "server" / "app" / "index.html"
    
    # For any path that is not an API route, serve the Next.js app.
    if index_path.exists():
        return FileResponse(index_path)
    else:
        # If the index file doesn't exist, it likely means the frontend wasn't built correctly.
        raise HTTPException(status_code=404, detail="Next.js app not found. Please build the frontend.") 