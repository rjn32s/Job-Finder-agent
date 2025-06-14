from pydantic import BaseModel
from typing import List, Optional, Dict

class Skill(BaseModel):
    name: str
    level: Optional[str] = None  # e.g., beginner, intermediate, advanced, expert

class Project(BaseModel):
    title: str
    description: str

class Resume(BaseModel):
    name: str
    email: str
    preferred_locations: List[str]
    skills: List[Skill]
    experience_years: int
    about: Optional[str] = ""
    projects: Optional[List[Project]] = []

class Job(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    skills_required: Optional[List[str]] = None
    date: Optional[str] = None
    url: str
    min_experience: Optional[int] = None
    description: Optional[str] = ""
