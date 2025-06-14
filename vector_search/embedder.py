from sentence_transformers import SentenceTransformer
from typing import List, Union
import numpy as np
import re
from bs4 import BeautifulSoup

class TextEmbedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedder with a sentence transformer model.
        Using all-MiniLM-L6-v2 as it's fast and works well on CPU.
        """
        self.model = SentenceTransformer(model_name)
        
    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags and clean the text.
        
        Args:
            text: Input text with HTML
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        # Remove HTML tags
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        return text
        
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better embeddings.
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
            
        # Clean HTML first
        text = self._clean_html(text)
            
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep important ones
        text = re.sub(r'[^a-z0-9\s.,;:!?()\-]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
        
    def embed_text(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Convert text to embeddings.
        
        Args:
            text: Single string or list of strings to embed
            
        Returns:
            numpy array of embeddings
        """
        if isinstance(text, str):
            text = [text]
            
        # Preprocess each text
        text = [self._preprocess_text(t) for t in text]
        
        return self.model.encode(text, convert_to_numpy=True)
    
    def embed_job(self, job_data: dict) -> np.ndarray:
        """
        Create a job embedding by combining relevant fields.
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            numpy array of the job embedding
        """
        # Clean and preprocess each field
        title = self._preprocess_text(job_data.get('title', ''))
        company = self._preprocess_text(job_data.get('company', ''))
        description = self._preprocess_text(job_data.get('description', ''))
        skills = [self._preprocess_text(skill) for skill in job_data.get('skills', [])]
        location = self._preprocess_text(job_data.get('location', ''))
        
        # Combine relevant fields for embedding with clear structure
        text_parts = [
            f"Job Title: {title}",
            f"Company: {company}",
            f"Location: {location}",
            f"Required Skills: {' '.join(skills)}",
            f"Job Description: {description}"
        ]
        
        # Filter out empty strings and join
        text = " | ".join(filter(None, text_parts))
        return self.embed_text(text)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Create an embedding for a search query.
        
        Args:
            query: Search query string
            
        Returns:
            numpy array of the query embedding
        """
        return self.embed_text(query)
