import json
import os
from vector_search.semantic_matcher import SemanticMatcher

def print_job_match(job, score):
    """Print job match details in a formatted way."""
    print(f"\nScore: {score:.3f}")
    print(f"Title: {job['title']}")
    print(f"Company: {job['company']}")
    if job.get('location'):
        print(f"Location: {job['location']}")
    if job.get('skills'):
        print(f"Skills: {', '.join(job['skills'])}")
    if job.get('description'):
        desc = job['description'][:200] + "..." if len(job['description']) > 200 else job['description']
        print(f"Description: {desc}")
    print(f"URL: {job['url']}")

def main():
    # Initialize the semantic matcher
    print("Initializing semantic matcher...")
    matcher = SemanticMatcher()
    
    # Paths
    jobs_path = "data/jobs.json"
    index_dir = "data/vector_index"
    
    # Check if index exists
    if os.path.exists(os.path.join(index_dir, "jobs.index")):
        print("Loading existing index...")
        matcher.load_index(index_dir)
    else:
        print("Creating new index...")
        matcher.index_jobs(jobs_path, index_dir)
    
    # Test queries
    test_queries = [
        "Python backend developer with AWS experience",
        "Frontend React developer",
        "Data scientist with machine learning",
        "DevOps engineer with Kubernetes"
    ]
    
    print("\nTesting search queries:")
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        results = matcher.search_jobs(query, k=3)
        for job, score in results:
            print_job_match(job, score)
    
    # Test resume matching
    print("\nTesting resume matching...")
    with open("resume.json") as f:
        resume = json.load(f)
    
    matches = matcher.match_resume_to_jobs(resume, k=3)
    print("\nTop matches for resume:")
    for job, score in matches:
        print_job_match(job, score)

if __name__ == "__main__":
    main() 