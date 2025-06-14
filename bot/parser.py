from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
import json
import re
from rich.console import Console
from rich.prompt import Prompt, Confirm
import time

load_dotenv()

console = Console()

class JobFilters(BaseModel):
    """Pydantic model for job search filters extracted from user query."""
    job_title: Optional[str] = Field(None, description="Main job title or role")
    location: Optional[str] = Field(None, description="Job location")
    is_remote: Optional[bool] = Field(None, description="Whether the job is remote")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    years_experience: Optional[int] = Field(None, description="Years of experience required")
    keywords: List[str] = Field(default_factory=list, description="Additional keywords")

    def display(self) -> None:
        """Display the extracted filters in a readable format."""
        console.print("\n[bold cyan]Extracted Search Parameters:[/bold cyan]")
        if self.job_title:
            console.print(f"📋 Job Title: {self.job_title}")
        if self.location:
            console.print(f"📍 Location: {self.location}")
        if self.is_remote is not None:
            console.print(f"🏠 Remote: {'Yes' if self.is_remote else 'No'}")
        if self.years_experience is not None:
            console.print(f"⏳ Experience: {self.years_experience} years")
        if self.skills:
            console.print(f"🛠️ Skills: {', '.join(self.skills)}")
        if self.keywords:
            console.print(f"🔑 Keywords: {', '.join(self.keywords)}")

    def to_search_query(self) -> Dict[str, Any]:
        """Convert filters to search query format."""
        query = {}
        if self.job_title:
            query['job_title'] = self.job_title
        if self.location:
            query['location'] = self.location
        if self.is_remote is not None:
            query['is_remote'] = self.is_remote
        if self.years_experience is not None:
            query['years_experience'] = self.years_experience
        if self.skills:
            query['skills'] = self.skills
        if self.keywords:
            query['keywords'] = self.keywords
        return query

class QueryParser:
    def __init__(self):
        """Initialize the query parser with LangChain and Groq."""
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.3-70b-versatile",
            timeout=30
        )
        
        self.prompt = PromptTemplate(
            input_variables=["user_input"],
            template="""
            Extract job search filters from the following user query. Return a JSON object with these fields:
            - job_title: Main job title or role (e.g., "Python Developer", "Software Engineer")
            - location: Job location (e.g., "Bangalore", "Remote")
            - is_remote: Boolean indicating if remote work is mentioned
            - skills: List of required skills (e.g., ["Python", "Django", "AWS"])
            - years_experience: Number of years of experience required (if mentioned)
            - keywords: Additional relevant keywords

            Important: 
            1. Only include fields that are EXPLICITLY mentioned in the query.
            2. Do not make assumptions or add fields that weren't mentioned.
            3. If a field is not mentioned, set it to null.
            4. For skills and keywords, always return an empty array [] if none are mentioned.
            5. Return valid JSON format.

            User query: "{user_input}"

            Return only the JSON object, nothing else. Do not include markdown formatting or code blocks.
            """
        )

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks if present."""
        text = re.sub(r'```json\s*|\s*```', '', text)
        return text.strip()

    def _fix_json(self, json_str: str) -> Dict[str, Any]:
        """Fix common JSON formatting issues."""
        try:
            # Try parsing as is
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fix common issues
            # Replace single quotes with double quotes
            json_str = json_str.replace("'", '"')
            # Ensure lists are properly formatted
            json_str = re.sub(r'\[([^"\]]+)\]', lambda m: f'["{m.group(1)}"]', json_str)
            # Remove any trailing commas
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                console.print(f"[yellow]Warning: Could not parse JSON response: {str(e)}[/yellow]")
                # Return a minimal valid response
                return {
                    "job_title": None,
                    "location": None,
                    "is_remote": None,
                    "skills": [],
                    "years_experience": None,
                    "keywords": []
                }

    def parse_query(self, user_input: str) -> JobFilters:
        """
        Parse a natural language query into structured job filters.
        
        Args:
            user_input: Natural language query from user
            
        Returns:
            JobFilters object containing extracted filters
            
        Raises:
            ValueError: If parsing fails or LLM returns invalid JSON
        """
        try:
            # Get response from LLM using the new syntax
            response = self.llm.invoke(self.prompt.format(user_input=user_input))
            
            # Extract and clean JSON from response
            json_str = self._extract_json(response.content)
            
            # Fix and parse JSON
            json_data = self._fix_json(json_str)

            # If years_experience is 0 but not mentioned in the query, treat as None
            if (
                ('years_experience' in json_data and json_data['years_experience'] == 0)
                and not (re.search(r'\bexperience\b', user_input, re.IGNORECASE) or re.search(r'\bexp\b', user_input, re.IGNORECASE))
            ):
                json_data['years_experience'] = None
            
            # Parse response into JobFilters
            filters = JobFilters.parse_obj(json_data)
            
            # Clean up and validate filters
            if filters.job_title:
                filters.job_title = filters.job_title.strip()
            if filters.location:
                filters.location = filters.location.strip()
            
            return filters
            
        except Exception as e:
            raise ValueError(f"Failed to parse query: {str(e)}")

    def parse_resume(self, resume_text: str) -> JobFilters:
        """
        Extract job preferences from resume text.
        
        Args:
            resume_text: Text content of the resume
            
        Returns:
            JobFilters object containing extracted preferences
        """
        try:
            prompt = PromptTemplate(
                input_variables=["resume_text"],
                template="""
                Extract job preferences and qualifications from this resume. Return a JSON object with:
                - job_title: Preferred job title based on experience
                - skills: List of skills mentioned
                - years_experience: Years of experience
                - keywords: Additional relevant keywords

                Important: 
                1. Only include fields that are EXPLICITLY mentioned in the resume.
                2. Do not make assumptions or add fields that weren't mentioned.
                3. If a field is not mentioned, set it to null.
                4. For skills and keywords, always return an empty array [] if none are mentioned.
                5. Return valid JSON format.

                Resume text: "{resume_text}"

                Return only the JSON object, nothing else. Do not include markdown formatting or code blocks.
                """
            )
            
            # Get response using new syntax
            response = self.llm.invoke(prompt.format(resume_text=resume_text))
            
            # Extract and clean JSON from response
            json_str = self._extract_json(response.content)
            
            # Fix and parse JSON
            json_data = self._fix_json(json_str)
            
            filters = JobFilters.parse_obj(json_data)
            
            return filters
            
        except Exception as e:
            raise ValueError(f"Failed to parse resume: {str(e)}")
