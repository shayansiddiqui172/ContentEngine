import logging
import time
import requests
from scripts.scraper.config import PROXYCURL_API_KEY, PROXYCURL_RATE_LIMIT
from scripts.scraper.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

BASE_URL = "https://nubela.co/proxycurl/api"
_rate_limiter = RateLimiter(PROXYCURL_RATE_LIMIT)

MAX_RETRIES = 3
BACKOFF_BASE = 2  # seconds


def _make_request(url: str, params: dict) -> dict | None:
    """Make a rate-limited request to Proxycurl with retry logic."""
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}

    for attempt in range(MAX_RETRIES):
        _rate_limiter.wait()
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                wait_time = BACKOFF_BASE ** (attempt + 1)
                logger.warning(f"Rate limited (429). Retrying in {wait_time}s...")
                time.sleep(wait_time)
            elif resp.status_code == 404:
                logger.warning(f"Profile not found (404): {params}")
                return None
            else:
                logger.error(f"Proxycurl error {resp.status_code}: {resp.text}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** (attempt + 1))
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE ** (attempt + 1))

    logger.error(f"All {MAX_RETRIES} retries exhausted for {url}")
    return None


def get_profile(linkedin_url: str) -> dict | None:
    """Fetch a LinkedIn profile via Proxycurl Person Profile endpoint."""
    logger.info(f"Fetching profile: {linkedin_url}")
    return _make_request(
        f"{BASE_URL}/v2/linkedin",
        {
            "linkedin_profile_url": linkedin_url,
            "use_cache": "if-present",
            "fallback_to_cache": "on-error",
            "skills": "include",
            "extra": "include",
        },
    )


def get_profile_posts(linkedin_url: str, num_posts: int = 10) -> list[dict]:
    """Fetch recent posts for a LinkedIn profile via Proxycurl."""
    logger.info(f"Fetching posts for: {linkedin_url}")
    result = _make_request(
        f"{BASE_URL}/v2/linkedin/profile/post",
        {
            "linkedin_profile_url": linkedin_url,
            "category": "posts",
            "limit": num_posts,
        },
    )
    if result is None:
        return []
    # Proxycurl returns {"posts": [...]} or a list directly
    if isinstance(result, list):
        return result
    return result.get("posts", [])
