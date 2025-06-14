import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Naukri API Configuration
    NAUKRI_BASE_URL = os.getenv('NAUKRI_BASE_URL', 'https://www.naukri.com/jobapi/v3/search')
    NAUKRI_APP_ID = os.getenv('NAUKRI_APP_ID', '109')
    NAUKRI_CLIENT_ID = os.getenv('NAUKRI_CLIENT_ID', 'd3skt0p')
    NAUKRI_NKPARAM = os.getenv('NAUKRI_NKPARAM')

    # Default Search Parameters
    DEFAULT_RESULTS_PER_PAGE = int(os.getenv('DEFAULT_RESULTS_PER_PAGE', '20'))
    DEFAULT_SEARCH_TYPE = os.getenv('DEFAULT_SEARCH_TYPE', 'adv')
    DEFAULT_URL_TYPE = os.getenv('DEFAULT_URL_TYPE', 'search_by_key_loc')

    # User Agent
    USER_AGENT = os.getenv('USER_AGENT')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO') 