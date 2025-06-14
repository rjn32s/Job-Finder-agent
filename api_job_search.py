from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import json
from scraper.naukri_scraper import NaukriScraper
from scraper.company_scraper import CompanyScraper
from datetime import datetime

app = FastAPI()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
OUTPUT_FILE = os.path.join(DATA_DIR, 'jobs.json')

class JobSearchRequest(BaseModel):
    title: str
    experience: Optional[int] = None
    location: Optional[str] = None

class JobResult(BaseModel):
    title: str
    company: str
    location: Optional[str]
    date: str
    url: str

@app.post("/search_jobs", response_model=List[JobResult])
def search_jobs(req: JobSearchRequest):
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
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "location": job.get("location", ""),
            "date": job.get("posted_date") or job.get("scraped_at", ""),
            "url": job.get("job_url", "")
        }
        for job in naukri_jobs
    ]

    # Run CompanyScraper
    company_scraper = CompanyScraper()
    company_jobs = company_scraper.scrape_all_companies(
        keyword=req.title,
        location=req.location or ""
    )
    company_results = []
    for jobs in company_jobs.values():
        for job in jobs:
            company_results.append({
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "date": job.get("scraped_at", ""),
                "url": job.get("url", "")
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