import logging
from typing import Dict, List
import urllib.parse

def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(level=getattr(logging, log_level))
    return logging.getLogger(__name__)

def create_seo_key(keyword: str, location: str = None) -> str:
    """Create SEO-friendly keyword for URL"""
    seo_key = f"{keyword.lower().replace(' ', '-')}-jobs"
    if location:
        seo_key += f"-in-{location.lower()}"
    return seo_key

def create_referer_url(seo_key: str, keyword: str, location: str = None, experience: int = None) -> str:
    """Create referer URL for the API request"""
    params = {
        "k": keyword,
        "l": location.lower() if location else "",
        "experience": experience if experience else ""
    }
    return f"https://www.naukri.com/{seo_key}?{urllib.parse.urlencode(params)}"

def extract_placeholder(placeholders: List[Dict], type_name: str) -> str:
    """Extract value from placeholders list based on type"""
    for placeholder in placeholders:
        if placeholder.get("type") == type_name:
            return placeholder.get("label", "")
    return "" 