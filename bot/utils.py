import json
from typing import List, Dict, Any
from pathlib import Path
import requests
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

def save_jobs_to_json(jobs: List[Dict[str, Any]], filepath: str = "data/jobs.json") -> None:
    """Save jobs to a JSON file."""
    try:
        # Create directory if it doesn't exist
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save jobs to file
        with open(filepath, 'w') as f:
            json.dump(jobs, f, indent=2)
            
        console.print(f"[green]Successfully saved {len(jobs)} jobs to {filepath}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save jobs: {str(e)}[/red]")

def display_jobs(jobs: List[Dict[str, Any]]) -> None:
    """Display jobs in a formatted table."""
    if not jobs:
        console.print("[yellow]No jobs found matching your criteria.[/yellow]")
        return
        
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Title")
    table.add_column("Company")
    table.add_column("Location")
    table.add_column("Date")
    table.add_column("URL")
    
    for job in jobs:
        table.add_row(
            job.get('title', 'N/A'),
            job.get('company', 'N/A'),
            job.get('location', 'N/A'),
            job.get('date', 'N/A'),
            job.get('url', 'N/A')
        )
    
    console.print(table)

def filters_to_api_payload(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Map JobFilters output to API payload with correct keys."""
    payload = {}
    if filters.get("job_title"):
        payload["title"] = filters["job_title"]
    if filters.get("years_experience") is not None:
        payload["experience"] = filters["years_experience"]
    if filters.get("location"):
        payload["location"] = filters["location"]
    return payload

def search_jobs_api(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Call the job search API with filters."""
    try:
        # Map filters to correct API payload
        payload = filters_to_api_payload(filters)
        response = requests.post(
            "http://localhost:8000/scrape_and_save_jobs",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]API Error: {str(e)}[/red]")
        return []

def get_resume_text() -> str:
    """Get resume text from user input."""
    console.print("\n[bold]Paste your resume text (press Ctrl+D when done):[/bold]")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines)

def suggest_corrections(query: str) -> str:
    """Suggest corrections for misspelled queries."""
    # TODO: Implement fuzzy matching or LLM-based correction
    return query

def get_user_confirmation(prompt: str) -> bool:
    """Get user confirmation for an action."""
    return Confirm.ask(prompt)

def match_resume_api(resume: dict) -> list:
    """Call the /match_resume endpoint with resume dict."""
    try:
        response = requests.post(
            "http://localhost:8000/match_resume",
            json=resume
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]API Error: {str(e)}[/red]")
        return []

def parse_resume_to_schema(resume_text: str) -> dict:
    """Stub: Parse resume text to Resume schema dict. To be implemented with LLM or rules."""
    # TODO: Implement real parsing logic
    return {}
