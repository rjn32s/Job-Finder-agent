# Buddy Bot: Setup & API Usage

## 1. Install Dependencies

First, install [uv](https://github.com/astral-sh/uv) (a fast Python package manager):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Then, sync your Python dependencies:

```bash
uv sync
```
 Activate the virtual environment

```bash
source .venv/bin/activate
```

## 2. Start the API Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn api_job_search:app --host 0.0.0.0 --port 8000
```

---

## 3. How to Use the API

### A. Job Search Endpoint

Search for jobs by title, experience, and location:

```bash
curl -X POST http://localhost:8000/scrape_and_save_jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "experience": 2,
    "location": "Bangalore"
  }'
```

### B. Resume Matching Endpoint

Find jobs that match your resume details:

```bash
curl -X POST http://localhost:8000/match_resume \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "Django", "AWS", "REST APIs"],
    "experience": 3,
    "location": "Bangalore",
    "preferred_locations": ["Bangalore", "Remote"],
    "about": "Backend developer with 3 years of experience building scalable APIs.",
    "projects": [
      {
        "name": "Inventory Management System",
        "description": "Built a Django-based inventory system for a retail client."
      }
    ]
  }'
```

---

**Tip:**
- For the CLI, just run:
  ```bash
  python bot/cli.py
  ```
  and follow the interactive prompts!


  How to run the APP: 
  Asssuming you have started the server, run the following command:
  ```bash
  cd frontend
  npm run dev
  ```
  This will start the Next.js app on http://localhost:3000

