import pytest
from matcher.schema import Resume, Job, Skill, Project
from matcher.matcher import score_job, top_n_matches

@pytest.fixture
def sample_resume():
    return Resume(
        name="Test User",
        email="test@example.com",
        preferred_locations=["Bangalore", "Remote"],
        skills=[
            Skill(name="Python", level="expert"),
            Skill(name="Django", level="advanced"),
            Skill(name="SQL", level="intermediate"),
            Skill(name="AWS", level="intermediate")
        ],
        experience_years=3,
        about="Backend engineer with a passion for scalable APIs",
        projects=[
            Project(
                title="E-commerce API",
                description="Built a scalable REST API using Django and AWS"
            )
        ]
    )

@pytest.fixture
def sample_jobs():
    return [
        Job(
            title="Senior Python Developer",
            company="Tech Corp",
            location="Bangalore",
            skills=["Python", "Django", "AWS"],
            min_experience=2,
            description="Looking for a Python expert to build scalable APIs",
            url="http://example.com/job1"
        ),
        Job(
            title="Frontend Developer",
            company="Web Inc",
            location="Mumbai",
            skills=["JavaScript", "React"],
            min_experience=1,
            description="Frontend developer position",
            url="http://example.com/job2"
        ),
        Job(
            title="Backend Engineer",
            company="API Co",
            location="Remote",
            skills=["Python", "SQL"],
            min_experience=4,
            description="Backend position for API development",
            url="http://example.com/job3"
        )
    ]

def test_score_job_location_match(sample_resume, sample_jobs):
    # Test job with matching location
    score = score_job(sample_resume, sample_jobs[0])
    assert score["location_match"] is True
    assert score["score"] >= 2  # At least location score

    # Test job with non-matching location
    score = score_job(sample_resume, sample_jobs[1])
    assert score["location_match"] is False

def test_score_job_skills_match(sample_resume, sample_jobs):
    # Test job with matching skills
    score = score_job(sample_resume, sample_jobs[0])
    assert len(score["matched_skills"]) == 3  # Python, Django, AWS
    assert "python" in score["matched_skills"]
    assert "django" in score["matched_skills"]
    assert "aws" in score["matched_skills"]

    # Test job with fewer matching skills
    score = score_job(sample_resume, sample_jobs[2])
    assert len(score["matched_skills"]) == 2  # Python, SQL

def test_score_job_experience_match(sample_resume, sample_jobs):
    # Test job with matching experience
    score = score_job(sample_resume, sample_jobs[0])
    assert score["exp_match"] is True

    # Test job with higher experience requirement
    score = score_job(sample_resume, sample_jobs[2])
    assert score["exp_match"] is False

def test_score_job_about_match(sample_resume, sample_jobs):
    # Test job with matching about/projects keywords
    score = score_job(sample_resume, sample_jobs[0])
    assert score["about_match"] is True

    # Test job without matching keywords
    score = score_job(sample_resume, sample_jobs[1])
    assert score["about_match"] is False

def test_top_n_matches(sample_resume, sample_jobs):
    matches = top_n_matches(sample_resume, sample_jobs, n=2)
    
    # Should return top 2 matches
    assert len(matches) == 2
    
    # First match should be the job with highest score
    assert matches[0]["job"].title == "Senior Python Developer"
    assert matches[0]["score"] > matches[1]["score"]

def test_edge_cases():
    # Test with empty job skills
    resume = Resume(
        name="Test",
        email="test@example.com",
        preferred_locations=["Bangalore"],
        skills=[Skill(name="Python", level="expert")],
        experience_years=1
    )
    job = Job(
        title="Test Job",
        company="Test Co",
        location="Bangalore",
        skills=[],
        url="http://example.com"
    )
    score = score_job(resume, job)
    assert len(score["matched_skills"]) == 0

    # Test with missing optional fields
    job = Job(
        title="Test Job",
        company="Test Co",
        url="http://example.com"
    )
    score = score_job(resume, job)
    assert score["location_match"] is False
    assert score["exp_match"] is False
    assert score["about_match"] is False

def test_case_insensitive_matching(sample_resume):
    job = Job(
        title="Python Developer",
        company="Test Co",
        location="BANGALORE",
        skills=["PYTHON", "django"],
        url="http://example.com"
    )
    score = score_job(sample_resume, job)
    assert score["location_match"] is True
    assert "python" in score["matched_skills"]
    assert "django" in score["matched_skills"]
