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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"] for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'jobs.json')

# Initialize semantic matcher with optimizations
matcher = SemanticMatcher()
index_dir = "data/vector_index"

# Load or create index on startup
@app.on_event("startup")
async def startup_event():
    jobs_path = "data/jobs.json"
    if os.path.exists(os.path.join(index_dir, "jobs.index")):
        matcher.load_index(index_dir)
    else:
        # Use batch processing for initial indexing
        with open(jobs_path, 'r') as f:
            jobs = json.load(f)
        matcher.batch_index_jobs(jobs, batch_size=1000)
        matcher.save_index(index_dir)

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