import json
import os
from typing import List, Dict, Tuple
import numpy as np
from .embedder import TextEmbedder
from .vector_db import VectorDB

class SemanticMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the semantic matcher with embedder and vector database.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.embedder = TextEmbedder(model_name)
        self.vector_db = VectorDB()
        
    def index_jobs(self, jobs_path: str, index_dir: str = "data/vector_index"):
        """
        Index jobs from a JSON file.
        
        Args:
            jobs_path: Path to the jobs JSON file
            index_dir: Directory to save the index
        """
        # Load jobs
        with open(jobs_path, 'r') as f:
            jobs = json.load(f)
            
        # Create embeddings for all jobs
        embeddings = []
        for job in jobs:
            embedding = self.embedder.embed_job(job)
            # Remove the extra dimension if present
            if len(embedding.shape) > 1:
                embedding = embedding.squeeze()
            embeddings.append(embedding)
            
        # Stack embeddings into a single array
        embeddings = np.stack(embeddings)  # This will create a 2D array (num_jobs x embedding_dim)
        
        # Add to vector database
        self.vector_db.add_jobs(jobs, embeddings)
        
        # Create index directory if it doesn't exist
        os.makedirs(index_dir, exist_ok=True)
        
        # Save index and jobs
        self.vector_db.save(
            os.path.join(index_dir, "jobs.index"),
            os.path.join(index_dir, "jobs.json")
        )
        
    def load_index(self, index_dir: str = "data/vector_index"):
        """
        Load the existing index.
        
        Args:
            index_dir: Directory containing the index files
        """
        self.vector_db.load(
            os.path.join(index_dir, "jobs.index"),
            os.path.join(index_dir, "jobs.json")
        )
        
    def search_jobs(self, query: str, k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for jobs using semantic similarity.
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of (job, score) tuples, sorted by similarity
        """
        # Create query embedding
        query_embedding = self.embedder.embed_query(query)
        # Remove the extra dimension if present
        if len(query_embedding.shape) > 1:
            query_embedding = query_embedding.squeeze()
        
        # Search vector database
        return self.vector_db.search(query_embedding, k)
    
    def match_resume_to_jobs(self, resume: Dict, k: int = 5, min_similarity: float = 0.0) -> List[Tuple[Dict, float]]:
        """
        Match a resume to jobs using semantic similarity.
        Args:
            resume: Resume dictionary
            k: Number of results to return
            min_similarity: Minimum similarity threshold for filtering results
        Returns:
            List of (job, score) tuples, sorted by similarity
        """
        # Create resume text from relevant fields
        resume_text = " ".join([
            resume.get("about", ""),
            " ".join([skill["name"] if isinstance(skill, dict) and "name" in skill else str(skill) for skill in resume.get("skills", [])]),
            " ".join([project["description"] for project in resume.get("projects", []) if isinstance(project, dict) and "description" in project])
        ])
        print("DEBUG: Resume text for embedding:", resume_text)
        # Search using resume text
        results = self.search_jobs(resume_text, k)
        print("DEBUG: Top matches and scores:")
        for job, score in results:
            print(f"Score: {score:.3f} | {job.get('title')} at {job.get('company')}")
        # Filter by min_similarity
        filtered_results = [(job, score) for job, score in results if score >= min_similarity]
        return filtered_results
