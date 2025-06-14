import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import os
import sys

# Add the parent directory to Python path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.config import Config
from scraper.utils import setup_logging, create_seo_key, create_referer_url, extract_placeholder

class NaukriScraper:
    def __init__(self):
        self.logger = setup_logging(Config.LOG_LEVEL)
        self.base_url = Config.NAUKRI_BASE_URL
        self.headers = {
            "accept": "application/json",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9",
            "appid": Config.NAUKRI_APP_ID,
            "clientid": Config.NAUKRI_CLIENT_ID,
            "content-type": "application/json",
            "gid": "LOCATION,INDUSTRY,EDUCATION,FAREA_ROLE",
            "priority": "u=1, i",
            "systemid": "Naukri",
            "user-agent": Config.USER_AGENT,
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "nkparam": Config.NAUKRI_NKPARAM
        }
        
        # Initialize session to maintain cookies
        self.session = requests.Session()
        
        # Set initial cookies
        self.session.cookies.update({
            "HitsFromTieup": "23531",
            "wExp": "N",
            "TieupFromTMS": "105",
            "_t_ds": "1f874b961749876300-161f874b96-01f874b96",
            "J": "0",
            "_gcl_gs": "2.1.k1$i1749876299$u155968292",
            "_ga": "GA1.1.1683586426.1749876301",
            "_gcl_au": "1.1.519158250.1749876302",
            "test": "naukri.com",
            "_t_us": "684CFE55",
            "_t_s": "direct",
            "_t_r": "1030%2F%2F",
            "persona": "default"
        })

    def search_jobs(self, 
                   keyword: str, 
                   location: Optional[str] = None,
                   experience: Optional[int] = None,
                   page: int = 1,
                   limit: int = Config.DEFAULT_RESULTS_PER_PAGE) -> List[Dict]:
        """
        Search for jobs using Naukri's API
        
        Args:
            keyword (str): Job title or keyword to search for
            location (str, optional): Location to search in
            experience (int, optional): Years of experience
            page (int): Page number for pagination
            limit (int): Number of results per page
            
        Returns:
            List[Dict]: List of job listings
        """
        try:
            # Create SEO-friendly keyword and referer URL
            seo_key = create_seo_key(keyword, location)
            referer_url = create_referer_url(seo_key, keyword, location, experience)
            
            # Add referer to headers
            headers = self.headers.copy()
            headers["referer"] = referer_url

            params = {
                "noOfResults": limit,
                "urlType": Config.DEFAULT_URL_TYPE,
                "searchType": Config.DEFAULT_SEARCH_TYPE,
                "keyword": keyword,
                "pageNo": page,
                "k": keyword,
                "seoKey": seo_key,
                "src": "jobsearchDesk",
                "latLong": ""
            }
            
            if location:
                params["location"] = location.lower()
                params["l"] = location.lower()
            if experience:
                params["experience"] = experience

            # First visit the search page to get necessary cookies
            self.logger.info(f"Visiting search page: {referer_url}")
            search_page_response = self.session.get(referer_url, headers=headers)
            self.logger.info(f"Search page status code: {search_page_response.status_code}")
            
            # Then make the API request
            self.logger.info(f"Making API request to: {self.base_url}")
            self.logger.info(f"With params: {params}")
            
            response = self.session.get(
                self.base_url,
                headers=headers,
                params=params,
                stream=True
            )
            
            self.logger.info(f"API Response status code: {response.status_code}")
            self.logger.info(f"API Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get("jobDetails"):
                self.logger.warning(f"No jobs found for keyword: {keyword}")
                return []

            jobs = []
            for job in data["jobDetails"]:
                # Extract placeholders
                placeholders = job.get("placeholders", [])
                location = extract_placeholder(placeholders, "location")
                experience = extract_placeholder(placeholders, "experience")
                salary = extract_placeholder(placeholders, "salary")

                processed_job = {
                    "title": job.get("title", ""),
                    "company": job.get("companyName", ""),
                    "location": location,
                    "experience": experience,
                    "salary": salary,
                    "description": job.get("jobDescription", ""),
                    "skills": job.get("tagsAndSkills", ""),
                    "posted_date": job.get("footerPlaceholderLabel", ""),
                    "job_url": f"https://www.naukri.com{job.get('jdURL', '')}",
                    "company_logo": job.get("logoPath", ""),
                    "company_rating": job.get("ambitionBoxData", {}).get("AggregateRating", ""),
                    "company_reviews": job.get("ambitionBoxData", {}).get("ReviewsCount", ""),
                    "job_id": job.get("jobId", ""),
                    "company_id": job.get("companyId", ""),
                    "currency": job.get("currency", ""),
                    "created_date": job.get("createdDate", ""),
                    "experience_text": job.get("experienceText", ""),
                    "mode": job.get("mode", ""),
                    "board": job.get("board", ""),
                    "source": "Naukri",
                    "scraped_at": datetime.now().isoformat()
                }
                jobs.append(processed_job)

            self.logger.info(f"Successfully fetched {len(jobs)} jobs from Naukri")
            return jobs

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching jobs from Naukri: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing Naukri API response: {str(e)}")
            try:
                self.logger.error(f"Raw response content: {response.content[:1000]}")
            except:
                pass
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in Naukri scraper: {str(e)}")
            try:
                self.logger.error(f"Raw response content: {response.content[:1000]}")
            except:
                pass
            return []

    def get_job_details(self, job_url: str) -> Optional[Dict]:
        """
        Get detailed information about a specific job
        
        Args:
            job_url (str): URL of the job posting
            
        Returns:
            Optional[Dict]: Detailed job information or None if not found
        """
        try:
            response = self.session.get(job_url, headers=self.headers)
            response.raise_for_status()
            
            return {
                "url": job_url,
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error fetching job details from {job_url}: {str(e)}")
            return None

if __name__ == "__main__":
    # Example usage
    scraper = NaukriScraper()
    jobs = scraper.search_jobs(
        keyword="Tax Accountant",
        location="Delhi",
        experience=1,
        page=1,
        limit=20
    )
    
    for job in jobs:
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Experience: {job['experience']}")
        print(f"Salary: {job['salary']}")
        print(f"Skills: {job['skills']}")
        print(f"Posted: {job['posted_date']}")
        print(f"Company Rating: {job['company_rating']} ({job['company_reviews']} reviews)")
        print(f"Job ID: {job['job_id']}")
        print(f"Company ID: {job['company_id']}")
        print(f"Currency: {job['currency']}")
        print(f"Created Date: {job['created_date']}")
        print(f"Experience Text: {job['experience_text']}")
        print(f"Mode: {job['mode']}")
        print(f"Board: {job['board']}")
        print("\nJob Description:")
        print(job['description'])
        print(f"\nURL: {job['job_url']}")
        print("-" * 80)
