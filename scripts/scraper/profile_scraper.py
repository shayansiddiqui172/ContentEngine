import re
from datetime import datetime, timezone
from scripts.scraper.config import DEFAULT_CONNECTION_STATUS, DEFAULT_PRIMARY_ROLE, follower_count_range

_VC_RE = re.compile(
    r'\b(?:VC|venture\s+capital(?:ist)?|investor|investing|fund|'
    r'managing\s+partner|general\s+partner|principal|angel\s+investor|'
    r'limited\s+partner|LP|portfolio)\b',
    re.IGNORECASE,
)
_STARTUP_RE = re.compile(
    r'\b(?:founder|co-founder|cofounder|CEO|CTO|COO|CPO|startup|entrepreneur|building)\b',
    re.IGNORECASE,
)
_AI_RE = re.compile(
    r'\b(?:artificial\s+intelligence|machine\s+learning|deep\s+learning|LLM|GPT|neural\s+network)\b',
    re.IGNORECASE,
)

def _detect_primary_role(bio: str | None) -> str:
    if not bio:
        return DEFAULT_PRIMARY_ROLE
    vc_hits = len(_VC_RE.findall(bio))
    startup_hits = len(_STARTUP_RE.findall(bio))
    ai_hits = len(_AI_RE.findall(bio))
    if vc_hits > 0 and vc_hits >= startup_hits:
        return "VC / Investor"
    if startup_hits > 0:
        return "Startup"
    if ai_hits > 0:
        return "AI"
    return "Ecosystem Partner"


def map_profile_to_creator(profile: dict) -> dict:
    """Map a PhantomBuster LinkedIn Profile Scraper row to the Creator schema."""
    linkedin_url = (profile.get("linkedinProfileUrl") or profile.get("profileUrl") or "").rstrip("/")

    full_name = f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip()
    firm = profile.get("companyName") or None
    location = profile.get("location") or None
    bio = profile.get("linkedinHeadline") or profile.get("linkedinDescription") or None

    follower_count_raw = profile.get("linkedinFollowersCount") or "0"
    try:
        follower_count = int(str(follower_count_raw).replace(",", ""))
    except (ValueError, TypeError):
        follower_count = None

    now = datetime.now(timezone.utc).isoformat()

    return {
        # Scraped fields
        "name": full_name,
        "linkedinUrl": linkedin_url,
        "bio": bio,
        "followerCountRange": follower_count_range(follower_count),
        "followerCount": follower_count,
        "location": location,
        "firmAffiliation": firm,
        "dateAdded": now,
        # Role detected from bio keywords; AI may refine if needed
        "primaryRole": _detect_primary_role(bio),
        "contentNiche": None,
        "topVoiceStyle": None,
        "credibility": None,
        # Computed fields (populated by run_pipeline.py after posts are mapped)
        "growthStage": None,
        "postingFrequency": None,
        "crossPlatformCount": 0,
        # Static / geography
        "geographyFocus": None,
        # Manual fields — left blank for team to fill in
        "overallNotes": None,
        "collaborationPotential": None,
        "connectionStatus": DEFAULT_CONNECTION_STATUS,
        "haveInteracted": False,
        "haveDMed": False,
        "relationshipNotes": None,
        # Nested posts (populated by run_pipeline.py)
        "posts": [],
    }
