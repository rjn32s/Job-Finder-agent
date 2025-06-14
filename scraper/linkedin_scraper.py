from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData
from linkedin_jobs_scraper.query import Query, QueryOptions
from typing import List, Dict
import asyncio
import json
from loguru import logger
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


# Container to collect jobs
jobs: List[Dict] = []

# Event handler
def on_data(data: EventData):
    job = {
        "title": data.title,
        "company": data.company,
        "location": data.place,
        "date": data.date,
        "url": data.link
    }
    jobs.append(job)

def scrape_linkedin_jobs(query: str = "Python Developer", locations=["India"], limit: int = 5) -> List[Dict]:
    global jobs
    jobs = []  # reset

    scraper = LinkedinScraper(
        chrome_executable_path=None,
        headless=True,
        max_workers=1,
        slow_mo=1.5  # slow down to avoid detection
    )

    scraper.on(Events.DATA, on_data)

    queries = [
        Query(
            query=query,
            options=QueryOptions(
                locations=locations,
                limit=limit,
                apply_link=False
            )
        )
    ]

    # Run the scraper (must be inside event loop)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(scraper.run(queries))

    return jobs

if __name__ == "__main__":
    # Example usage
    jobs = scrape_linkedin_jobs(query="Machine Learning Engineer", locations=["Bangalore", "India"], limit=5)
    print(json.dumps(jobs, indent=2))
