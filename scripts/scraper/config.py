import os
import json
from dotenv import load_dotenv

load_dotenv()

# API Keys
PROXYCURL_API_KEY = os.getenv("PROXYCURL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Rate limits
PROXYCURL_RATE_LIMIT = 2  # requests per second
GEMINI_RATE_LIMIT = 10  # requests per second

# Thresholds
VIRAL_FLAG_MULTIPLIER = 2.0  # engagement > 2x creator average = viral
DEFAULT_ENGAGEMENT_RATE = 0.02  # 2% fallback for impression estimation

# Defaults for manual fields
DEFAULT_WATCH_STATUS = "PASSIVE"
DEFAULT_CONNECTION_STATUS = "NOT_CONNECTED"
DEFAULT_PRIMARY_ROLE = "FOUNDER"

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_PROFILES_PATH = os.path.join(PROJECT_ROOT, "data", "target_profiles.json")
ENRICHED_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "enriched_creators.json")
RAW_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "raw_creators.json")


def load_target_profiles() -> list[str]:
    """Load LinkedIn profile URLs from target_profiles.json."""
    with open(TARGET_PROFILES_PATH, "r") as f:
        data = json.load(f)
    return data.get("profiles", [])
