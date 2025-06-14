import click
from rich.console import Console
from rich.prompt import Prompt
from parser import QueryParser, JobFilters
import utils
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from utils import match_resume_api, parse_resume_to_schema

console = Console()

def detect_intent(user_input: str) -> str:
    """Detect user intent: 'job_search', 'resume_search', or 'unknown'."""
    text = user_input.lower()
    if any(word in text for word in ["resume", "cv", "profile", "match my resume", "paste my resume"]):
        return "resume_search"
    if any(word in text for word in ["job", "find", "search", "looking for", "position", "role", "opening"]):
        return "job_search"
    # Heuristic: if the input is long (e.g., > 300 chars), treat as resume
    if len(user_input) > 300:
        return "resume_search"
    return "unknown"

@click.command()
def buddy():
    """Conversational Buddy Bot: Job search or resume match."""
    try:
        parser = QueryParser()
        console.print("[bold blue]\n🤖 Hi! How can I help you today?[/bold blue]")
        user_input = Prompt.ask("")
        intent = detect_intent(user_input)

        # If intent is unclear, ask for clarification
        if intent == "unknown":
            console.print("[yellow]Do you want to search for jobs or find jobs matching your resume?[/yellow]")
            clarification = Prompt.ask("Type 'job' or 'resume'").strip().lower()
            if "resume" in clarification:
                intent = "resume_search"
            else:
                intent = "job_search"

        if intent == "resume_search":
            # Get resume text if not already provided
            if len(user_input) < 300:
                console.print("\n[bold]Paste your resume text (press Ctrl+D when done):[/bold]")
                resume_text = utils.get_resume_text()
            else:
                resume_text = user_input
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Parsing your resume...", total=None)
                resume_dict = parse_resume_to_schema(resume_text)
            if not resume_dict:
                console.print("[red]Could not parse your resume into structured data. Please try again or provide more details.[/red]")
                return
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Finding jobs matching your resume...", total=None)
                jobs = match_resume_api(resume_dict)
            utils.display_jobs(jobs)
            if jobs and utils.get_user_confirmation("\nWould you like to save these suggestions?"):
                utils.save_jobs_to_json(jobs)
        else:
            # Job search flow
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Analyzing your query...", total=None)
                filters = parser.parse_query(user_input)
            console.print(Panel.fit(
                "[bold green]Starting job search with these parameters:[/bold green]",
                border_style="green"
            ))
            filters.display()
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Searching for jobs...", total=None)
                search_query = filters.to_search_query()
                jobs = utils.search_jobs_api(search_query)
            utils.display_jobs(jobs)
            if jobs and utils.get_user_confirmation("\nWould you like to save these results?"):
                utils.save_jobs_to_json(jobs)
    except KeyboardInterrupt:
        console.print("\n[yellow]Session cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred: {str(e)}[/red]")

if __name__ == '__main__':
    buddy()
