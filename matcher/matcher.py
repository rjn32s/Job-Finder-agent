import json
from matcher.schema import Resume, Job
from typing import List
import os

def score_job(resume: Resume, job: Job):
    # Location match
    location_score = 2 if job.location and any(loc.lower() in job.location.lower() for loc in resume.preferred_locations) else 0

    # Skills match (by name, case-insensitive)
    resume_skill_names = {s.name.lower() for s in resume.skills}
    job_skills = set([s.lower() for s in (job.skills or [])])
    skill_matches = resume_skill_names & job_skills
    skill_score = len(skill_matches)

    # Experience match
    exp_score = 0
    if job.min_experience is not None:
        exp_score = 2 if resume.experience_years >= job.min_experience else 0

    # About/Projects match (keywords in job description)
    about_text = (resume.about or "") + " " + " ".join([p.description for p in (resume.projects or [])])
    about_keywords = set(about_text.lower().split())
    desc = job.description or ""
    about_score = 1 if any(word in desc.lower() for word in about_keywords) else 0

    total_score = location_score + skill_score + exp_score + about_score
    return {
        "job": job,
        "score": total_score,
        "matched_skills": list(skill_matches),
        "location_match": location_score > 0,
        "exp_match": exp_score > 0,
        "about_match": about_score > 0
    }

def top_n_matches(resume: Resume, jobs: List[Job], n=5):
    scored = [score_job(resume, job) for job in jobs]
    scored.sort(key=lambda x: (x["score"], len(x["matched_skills"]), x["job"].title), reverse=True)
    return scored[:n]

def keyword_match_jobs(resume_dict: dict, jobs_list: list, n=5):
    # Convert dicts to Resume and Job objects
    resume = Resume(**resume_dict)
    jobs = [Job(**job) for job in jobs_list]
    return top_n_matches(resume, jobs, n)

if __name__ == "__main__":
    resume_path = "resume.json"
    jobs_path = os.path.join("data", "jobs.json")
    with open(resume_path) as f:
        resume = Resume(**json.load(f))
    with open(jobs_path) as f:
        jobs = [Job(**job) for job in json.load(f)]
    matches = top_n_matches(resume, jobs)
    for match in matches:
        job = match["job"]
        print(f"{job.title} at {job.company} | Score: {match['score']} | Skills: {match['matched_skills']} | LocationMatch: {match['location_match']} | ExpMatch: {match['exp_match']} | AboutMatch: {match['about_match']} | URL: {job.url}")
