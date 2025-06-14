import faiss
import numpy as np
import json
from typing import List, Dict, Tuple
import os

class VectorDB:
    def __init__(self, dimension: int = 384):  # 384 is the dimension for all-MiniLM-L6-v2
        """
        Initialize FAISS index for vector similarity search.
        
        Args:
            dimension: Dimension of the vectors (depends on the embedding model)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance for similarity
        self.jobs: List[Dict] = []  # Store job metadata
        
    def add_jobs(self, jobs: List[Dict], embeddings: np.ndarray):
        """
        Add jobs and their embeddings to the index.
        
        Args:
            jobs: List of job dictionaries
            embeddings: numpy array of job embeddings
        """
        if len(jobs) != len(embeddings):
            raise ValueError("Number of jobs must match number of embeddings")
            
        # Ensure embeddings are in the correct shape (num_jobs x dimension)
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        elif len(embeddings.shape) > 2:
            raise ValueError(f"Invalid embeddings shape: {embeddings.shape}")
            
        # Add vectors to FAISS index
        self.index.add(embeddings.astype('float32'))
        self.jobs.extend(jobs)
        
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[Dict, float]]:
        """
        Search for similar jobs using vector similarity.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            
        Returns:
            List of (job, score) tuples, sorted by similarity
        """
        # Ensure query vector is the right shape
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
            
        # Search the index
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Convert distances to similarity scores (1 / (1 + distance))
        scores = 1 / (1 + distances[0])
        
        # Return jobs with their scores
        results = []
        for idx, score in zip(indices[0], scores):
            if idx < len(self.jobs):  # Ensure index is valid
                results.append((self.jobs[idx], float(score)))
                
        return results
    
    def save(self, index_path: str, jobs_path: str):
        """
        Save the FAISS index and job metadata to disk.
        
        Args:
            index_path: Path to save the FAISS index
            jobs_path: Path to save the job metadata
        """
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save job metadata
        with open(jobs_path, 'w') as f:
            json.dump(self.jobs, f)
            
    def load(self, index_path: str, jobs_path: str):
        """
        Load the FAISS index and job metadata from disk.
        
        Args:
            index_path: Path to the FAISS index
            jobs_path: Path to the job metadata
        """
        if os.path.exists(index_path) and os.path.exists(jobs_path):
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load job metadata
            with open(jobs_path, 'r') as f:
                self.jobs = json.load(f)
        else:
            raise FileNotFoundError("Index or jobs file not found")
