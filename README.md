# Job Matcher Assignment

A comprehensive job matching system that combines job scraping, resume matching, vector search, and a user-friendly interface.

## Project Structure

```
job-matcher-assignment/
│
├── scraper/             # Part 1: Job-Scraping Engine
│   ├── linkedin_scraper.py
│   ├── naukri_scraper.py
│   ├── company_scraper.py
│   └── deduper.py
│
├── matcher/             # Part 2: Resume-Based Matching
│   ├── schema.py
│   ├── scorer.py
│   ├── matcher.py
│   └── test_matcher.py
│
├── vector_search/       # Part 3: Vector DB Integration
│   ├── embedder.py
│   ├── vector_db.py
│   └── semantic_matcher.py
│
├── bot/                 # Part 4: Buddy Bot CLI
│   ├── cli.py
│   ├── parser.py
│   └── utils.py
│
├── frontend/            # Part 5: UI & Deployment
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── api.js
│
├── devops/              # Part 6: DevOps & CI
│   └── .github/workflows/ci.yml
│
├── jobs.json            # Output of scraper
├── resume.json          # Input for matcher
├── README.md
└── requirements.txt
```

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the scraper:
```bash
python scraper/linkedin_scraper.py
python scraper/naukri_scraper.py
```

4. Start the matching process:
```bash
python matcher/matcher.py
```

5. Launch the frontend:
```bash
cd frontend
python -m http.server 8000
```

## Components

1. **Job Scraping Engine**: Scrapes job listings from LinkedIn and Naukri
2. **Resume-Based Matching**: Matches resumes with job descriptions
3. **Vector Search**: Implements semantic search using vector embeddings
4. **Buddy Bot CLI**: Command-line interface for job matching
5. **Frontend**: Web interface for job matching
6. **DevOps**: CI/CD pipeline configuration

## Requirements

- Python 3.8+
- Node.js 14+ (for frontend)
- Modern web browser 