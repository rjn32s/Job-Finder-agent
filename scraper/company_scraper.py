import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, List, Optional, Set
from datetime import datetime
import logging
from fake_useragent import UserAgent
import json
import html
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def filter_jobs(jobs, job_title=None, location=None):
    def match(job, field, value):
        if not value:
            return True
        field_val = (job.get(field, '') or '')
        return value.lower() in field_val.lower()
    return [
        job for job in jobs
        if match(job, 'title', job_title) and match(job, 'location', location)
    ]

class CompanyScraper:
    def __init__(self):
        # Set up detailed logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        self.ua = UserAgent()
        self.session = requests.Session()
        
        # Serper API configuration
        self.serper_api_key = os.getenv('SERPER_API_KEY')
        if not self.serper_api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        
        # Define target companies and their career page patterns
        self.target_companies = {
            "razorpay": {
                "name": "Razorpay",
                "career_url": "https://razorpay.com/jobs/",
                "job_patterns": ["/jobs/", "/careers/"],
                "domains": ["razorpay.com"]
            },
            "freshworks": {
                "name": "Freshworks",
                "career_url": "https://www.freshworks.com/company/careers/",
                "job_patterns": ["/careers/", "/jobs/"],
                "domains": ["freshworks.com"]
            },
            "zoho": {
                "name": "Zoho",
                "career_url": "https://www.zoho.com/careers/job-openings.html",
                "job_patterns": ["/careers/", "/jobs/", "/jobdetails/"],
                "domains": ["zoho.com"]
            },
            "cognizant": {
                "name": "Cognizant",
                "career_url": "https://careers.cognizant.com/global/en",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["cognizant.com"]
            },
            "wipro": {
                "name": "Wipro",
                "career_url": "https://careers.wipro.com/careers-home/",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["wipro.com"]
            },
            "ltimindtree": {
                "name": "LTIMindtree",
                "career_url": "https://careers.ltimindtree.com/",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["ltimindtree.com"]
            },
            "infosys": {
                "name": "Infosys",
                "career_url": "https://career.infosys.com/joblist",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["infosys.com"]
            },
            "tcs": {
                "name": "TCS",
                "career_url": "https://ibegin.tcs.com/iBegin/jobs/search",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["tcs.com"]
            },
            "hcl": {
                "name": "HCL",
                "career_url": "https://www.hcltech.com/careers/jobs",
                "job_patterns": ["/job/", "/jobs/", "/careers/"],
                "domains": ["hcltech.com"]
            }
        }

    def _get_random_delay(self) -> float:
        """Generate a random delay between requests"""
        delay = random.uniform(0.5, 1)
        self.logger.debug(f"Generated random delay: {delay:.2f} seconds")
        return delay

    def _get_headers(self, company: str) -> Dict:
        """Generate headers for each request"""
        return {
            "User-Agent": self.ua.random,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

    def _make_request(self, url: str, company: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make a request with random delay and headers"""
        try:
            self.logger.info(f"Making request to: {url}")
            if params:
                self.logger.debug(f"With parameters: {params}")
            
            time.sleep(self._get_random_delay())
            response = self.session.get(
                url,
                params=params,
                headers=self._get_headers(company),
                timeout=30
            )
            
            self.logger.debug(f"Response status code: {response.status_code}")
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            # Log response content length and first 200 characters
            content_preview = response.text[:200].replace('\n', ' ')
            self.logger.debug(f"Response content length: {len(response.text)}")
            self.logger.debug(f"Response content preview: {content_preview}...")
            
            return response
        except requests.RequestException as e:
            self.logger.error(f"Error making request to {url}: {str(e)}")
            if hasattr(e.response, 'text'):
                self.logger.error(f"Error response content: {e.response.text[:500]}")
            return None

    def search_company_jobs(self, company_key: str, keyword: str = "", location: str = "") -> List[Dict]:
        """
        Search for jobs from a specific company's career page
        """
        if company_key not in self.target_companies:
            self.logger.error(f"Company {company_key} not supported")
            return []

        company_info = self.target_companies[company_key]
        self.logger.info(f"Searching jobs for {company_info['name']}")

        try:
            # Construct search query for the specific company
            query = f"site:{company_info['domains'][0]} {keyword}"
            if location:
                query += f" location:{location}"

            self.logger.info(f"Searching Serper with query: {query}")

            # Make request to Serper API
            response = requests.post(
                "https://google.serper.dev/search",
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "q": query,
                    "gl": "in",  # Set location to India
                    "hl": "en",  # Set language to English
                    "num": 5,   # Get 10 results per company
                    "type": "search"
                }
            )

            response.raise_for_status()
            data = response.json()

            # Extract organic results
            organic_results = data.get("organic", [])
            job_links = set()

            # Filter and collect job links
            for result in organic_results:
                link = result.get("link", "")
                
                # Verify it's a job page from the company
                if any(pattern in link.lower() for pattern in company_info["job_patterns"]):
                    job_links.add(link)

            self.logger.info(f"Found {len(job_links)} potential job listings for {company_info['name']}")
            return list(job_links)

        except Exception as e:
            self.logger.error(f"Error searching jobs for {company_info['name']}: {str(e)}")
            return []

    COMMON_SKILLS = [
        "python", "java", "c++", "c#", "javascript", "typescript", "go", "ruby", "php", "swift", "kotlin",
        "sql", "nosql", "mongodb", "postgresql", "mysql", "aws", "azure", "gcp", "docker", "kubernetes",
        "linux", "django", "flask", "react", "angular", "vue", "node", "rest", "graphql", "html", "css"
    ]

    def extract_skills_from_text(self, text: str) -> list:
        """Extract common skills from a block of text."""
        if not text:
            return []
        text_lower = text.lower()
        found = set()
        for skill in self.COMMON_SKILLS:
            if skill in text_lower:
                found.add(skill.capitalize() if skill.islower() else skill)
        return list(found)

    def scrape_job_page(self, url: str, company_key: str) -> Optional[Dict]:
        """
        Scrape a single job listing page
        """
        try:
            response = self._make_request(url, company_key)
            if not response:
                return None

            soup = BeautifulSoup(response.text, 'html.parser')
            company_info = self.target_companies[company_key]
            
            # Try to extract job details using common patterns
            title = None
            location = None
            description = None
            skills = []

            # Look for title in common locations
            title_candidates = [
                soup.find("h1"),
                soup.find("h2"),
                soup.find(class_=lambda x: x and any(term in x.lower() for term in [
                    "title", "job-title", "position-title", "role-title"
                ]))
            ]
            title = next((t.text.strip() for t in title_candidates if t), None)

            # Look for location
            location_candidates = [
                soup.find(class_=lambda x: x and any(term in x.lower() for term in [
                    "location", "place", "city", "office"
                ])),
                soup.find(string=lambda x: x and any(term in x.lower() for term in [
                    "location:", "based in", "office in"
                ]))
            ]
            location = next((l.text.strip() for l in location_candidates if l), None)

            # Look for description
            description_candidates = [
                soup.find(class_=lambda x: x and any(term in x.lower() for term in [
                    "description", "details", "content", "requirements",
                    "responsibilities", "about-role", "job-details"
                ])),
                soup.find("div", {"id": lambda x: x and any(term in x.lower() for term in [
                    "description", "details", "content"
                ])})
            ]
            description = next((d.text.strip() for d in description_candidates if d), None)

            # Try to extract skills from a requirements/skills section
            skills_section = soup.find(class_=lambda x: x and "skill" in x.lower())
            if skills_section:
                skills = [li.text.strip() for li in skills_section.find_all("li") if li.text.strip()]
            # Fallback: extract from description
            if not skills and description:
                skills = self.extract_skills_from_text(description)

            if not title:
                return None

            return {
                "title": title,
                "company": company_info["name"],
                "location": location,
                "description": description,
                "skills": skills,
                "url": url,
                "source": f"{company_info['name']} Career Page",
                "scraped_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error scraping job page {url}: {str(e)}")
            return None

    def scrape_freshworks_jobs(self, keyword: str = "", limit: int = 10, max_pages: int = 1) -> list:
        """
        Scrape jobs directly from Freshworks' SmartRecruiters API.
        """
        jobs = []
        for page in range(max_pages):
            offset = page * limit
            url = (
                f"https://api.smartrecruiters.com/v1/companies/freshworks/postings"
                f"?limit={limit}&offset={offset}"
            )
            if keyword:
                url += f"&search={keyword}"
            try:
                self.logger.info(f"Fetching Freshworks jobs from: {url}")
                resp = self.session.get(url, headers=self._get_headers("freshworks"), timeout=30)
                resp.raise_for_status()
                data = resp.json()
                for job in data.get("content", []):
                    desc = job.get("jobAd", {}).get("sections", {}).get("jobDescription", "")
                    skills = self.extract_skills_from_text(desc)
                    jobs.append({
                        "title": job.get("name"),
                        "company": "Freshworks",
                        "location": job.get("location", {}).get("city"),
                        "department": job.get("department"),
                        "url": f"https://careers.smartrecruiters.com/Freshworks/{job.get('id')}",
                        "description": desc,
                        "skills": skills,
                        "source": "Freshworks SmartRecruiters API",
                        "scraped_at": datetime.now().isoformat()
                    })
                if not data.get("content"):
                    break  # No more jobs
            except Exception as e:
                self.logger.error(f"Error fetching Freshworks jobs: {str(e)}")
                break
        self.logger.info(f"Total Freshworks jobs scraped: {len(jobs)}")
        return jobs

    def scrape_zoho_job_page(self, url: str) -> dict:
        """
        Scrape a Zoho job detail page for title, description, country, industry, skills, and URL.
        """
        try:
            self.logger.info(f"Scraping Zoho job page: {url}")
            resp = self.session.get(url, headers=self._get_headers("zoho"), timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Title
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else None

            # Description
            desc_section = soup.find('section', string=lambda x: x and 'Job Description' in x)
            if not desc_section:
                desc_section = soup.find('div', string=lambda x: x and 'Job Description' in x)
            description = None
            if desc_section:
                # Get the next sibling or parent for the actual description
                desc_content = desc_section.find_next('ul') or desc_section.find_next('div')
                if desc_content:
                    description = desc_content.get_text(separator='\n').strip()
            if not description:
                # Fallback: look for Job Description by heading
                desc_heading = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Job Description' in tag.text)
                if desc_heading:
                    desc_content = desc_heading.find_next('ul') or desc_heading.find_next('div')
                    if desc_content:
                        description = desc_content.get_text(separator='\n').strip()

            # Country and Industry
            country = None
            industry = None
            info_section = soup.find('div', string=lambda x: x and 'Job Information' in x)
            if not info_section:
                # Try to find by heading
                info_heading = soup.find(lambda tag: tag.name in ['h2', 'h3'] and 'Job Information' in tag.text)
                if info_heading:
                    info_section = info_heading.find_parent('div')
            if info_section:
                # Find all list items or spans
                for li in info_section.find_all(['li', 'span', 'div']):
                    text = li.get_text(strip=True)
                    if 'Country' in text:
                        country = text.split('Country')[-1].strip(': ').strip()
                    if 'Industry' in text:
                        industry = text.split('Industry')[-1].strip(': ').strip()
            # Fallback: look for text blocks
            if not country or not industry:
                for label in soup.find_all(['div', 'span', 'li']):
                    text = label.get_text(strip=True)
                    if not country and text.lower() == 'country':
                        next_val = label.find_next_sibling(text=True)
                        if next_val:
                            country = next_val.strip()
                    if not industry and text.lower() == 'industry':
                        next_val = label.find_next_sibling(text=True)
                        if next_val:
                            industry = next_val.strip()

            # Skills
            skills = []
            skills_section = soup.find(class_=lambda x: x and "skill" in x.lower())
            if skills_section:
                skills = [li.text.strip() for li in skills_section.find_all("li") if li.text.strip()]
            if not skills and description:
                skills = self.extract_skills_from_text(description)

            return {
                "title": title,
                "description": description,
                "country": country,
                "industry": industry,
                "skills": skills,
                "url": url,
                "company": "Zoho",
                "source": "Zoho Careers",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scraping Zoho job page {url}: {str(e)}")
            return None

    def scrape_cognizant_job_page(self, url: str) -> dict:
        """
        Scrape a Cognizant job detail page for title, description, skills, and URL.
        """
        try:
            self.logger.info(f"Scraping Cognizant job page: {url}")
            resp = self.session.get(url, headers=self._get_headers("cognizant"), timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Title
            title_tag = soup.find(['h1', 'h2'], string=True)
            title = title_tag.text.strip() if title_tag else None
            # Description
            desc_section = soup.find('div', class_=lambda x: x and 'job-description' in x.lower())
            if not desc_section:
                desc_section = soup.find('section')
            description = None
            if desc_section:
                description = desc_section.get_text(separator='\n').strip()
            # Fallback: look for 'Responsibilities' or 'Job Summary'
            if not description:
                resp_tag = soup.find(string=lambda x: x and 'Responsibilities' in x)
                if resp_tag:
                    description = resp_tag.find_parent().get_text(separator='\n').strip()
            # Skills
            skills = []
            skills_section = soup.find(class_=lambda x: x and "skill" in x.lower())
            if skills_section:
                skills = [li.text.strip() for li in skills_section.find_all("li") if li.text.strip()]
            if not skills and description:
                skills = self.extract_skills_from_text(description)
            return {
                "title": title,
                "description": description,
                "skills": skills,
                "url": url,
                "company": "Cognizant",
                "source": "Cognizant Careers",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scraping Cognizant job page {url}: {str(e)}")
            return None

    def scrape_wipro_job_page(self, url: str) -> dict:
        """
        Scrape a Wipro job detail page for title, description, location, skills, and URL.
        """
        try:
            self.logger.info(f"Scraping Wipro job page: {url}")
            resp = self.session.get(url, headers=self._get_headers("wipro"), timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Title
            title_tag = soup.find(string=lambda x: x and x.strip().lower().startswith('title:'))
            title = None
            if title_tag:
                title = title_tag.split(':', 1)[-1].strip()
            else:
                h1 = soup.find('h1')
                if h1:
                    title = h1.text.strip()
            # Location
            city_tag = soup.find(string=lambda x: x and x.strip().lower().startswith('city:'))
            location = None
            if city_tag:
                location = city_tag.split(':', 1)[-1].strip()
            # Description
            desc_heading = soup.find(string=lambda x: x and 'Job Description' in x)
            description = None
            if desc_heading:
                desc_block = desc_heading.find_parent()
                if desc_block:
                    description = desc_block.get_text(separator='\n').strip()
            # Fallback: look for 'Role Purpose'
            if not description:
                role_purpose = soup.find(string=lambda x: x and 'Role Purpose' in x)
                if role_purpose:
                    description = role_purpose.find_parent().get_text(separator='\n').strip()
            # Skills
            skills = []
            skills_section = soup.find(class_=lambda x: x and "skill" in x.lower())
            if skills_section:
                skills = [li.text.strip() for li in skills_section.find_all("li") if li.text.strip()]
            if not skills and description:
                skills = self.extract_skills_from_text(description)
            return {
                "title": title,
                "location": location,
                "description": description,
                "skills": skills,
                "url": url,
                "company": "Wipro",
                "source": "Wipro Careers",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scraping Wipro job page {url}: {str(e)}")
            return None

    def scrape_ltimindtree_job_page(self, url: str) -> dict:
        """
        Scrape an LTIMindtree job detail page for title, description, skills, and URL.
        """
        try:
            self.logger.info(f"Scraping LTIMindtree job page: {url}")
            resp = self.session.get(url, headers=self._get_headers("ltimindtree"), timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            # Title
            title_tag = soup.find('h1')
            title = title_tag.text.strip() if title_tag else None
            # Description
            desc_heading = soup.find(string=lambda x: x and 'RESPONSIBILITIES' in x.upper())
            description = None
            if desc_heading:
                desc_block = desc_heading.find_parent()
                if desc_block:
                    description = desc_block.get_text(separator='\n').strip()
            # Fallback: get all text under the main content
            if not description:
                main = soup.find('main')
                if main:
                    description = main.get_text(separator='\n').strip()
            # Skills
            skills = []
            skills_section = soup.find(class_=lambda x: x and "skill" in x.lower())
            if skills_section:
                skills = [li.text.strip() for li in skills_section.find_all("li") if li.text.strip()]
            if not skills and description:
                skills = self.extract_skills_from_text(description)
            return {
                "title": title,
                "description": description,
                "skills": skills,
                "url": url,
                "company": "LTIMindtree",
                "source": "LTIMindtree Careers",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error scraping LTIMindtree job page {url}: {str(e)}")
            return None

    def scrape_all_companies(self, keyword: str = "", location: str = "") -> Dict[str, List[Dict]]:
        """
        Scrape jobs from all target companies and filter by keyword and location
        """
        all_jobs = {}
        for company_key in self.target_companies:
            self.logger.info(f"\nScraping jobs for {self.target_companies[company_key]['name']}")
            if company_key == "freshworks":
                jobs = self.scrape_freshworks_jobs(keyword=keyword, limit=10, max_pages=1)
            elif company_key == "zoho":
                job_links = self.search_company_jobs(company_key, keyword, location)
                jobs = []
                for link in job_links:
                    job_data = self.scrape_zoho_job_page(link)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.info(f"Successfully scraped Zoho job: {job_data['title']}")
            elif company_key == "cognizant":
                job_links = self.search_company_jobs(company_key, keyword, location)
                jobs = []
                for link in job_links:
                    job_data = self.scrape_cognizant_job_page(link)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.info(f"Successfully scraped Cognizant job: {job_data['title']}")
            elif company_key == "wipro":
                job_links = self.search_company_jobs(company_key, keyword, location)
                jobs = []
                for link in job_links:
                    job_data = self.scrape_wipro_job_page(link)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.info(f"Successfully scraped Wipro job: {job_data['title']}")
            elif company_key == "ltimindtree":
                job_links = self.search_company_jobs(company_key, keyword, location)
                jobs = []
                for link in job_links:
                    job_data = self.scrape_ltimindtree_job_page(link)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.info(f"Successfully scraped LTIMindtree job: {job_data['title']}")
            else:
                job_links = self.search_company_jobs(company_key, keyword, location)
                jobs = []
                for link in job_links:
                    job_data = self.scrape_job_page(link, company_key)
                    if job_data:
                        jobs.append(job_data)
                        self.logger.info(f"Successfully scraped job: {job_data['title']}")
            # Filter jobs by job title and location
            jobs = filter_jobs(jobs, job_title=keyword, location=location)
            all_jobs[company_key] = jobs
            self.logger.info(f"Found {len(jobs)} jobs for {self.target_companies[company_key]['name']}")
        return all_jobs

if __name__ == "__main__":
    # Example usage
    scraper = CompanyScraper()
    
    # Scrape jobs from all companies
    all_jobs = scraper.scrape_all_companies(
        keyword="software engineer",
        location="bangalore"
    )
    
    # Print results
    for company_key, jobs in all_jobs.items():
        company_name = scraper.target_companies[company_key]["name"]
        print(f"\n{company_name.upper()} JOBS:")
        print("-" * 50)
        for job in jobs:
            print(f"Title: {job.get('title', '')}")
            print(f"Location: {job.get('location', '')}")
            print(f"URL: {job.get('url', '')}")
            print("-" * 30)
