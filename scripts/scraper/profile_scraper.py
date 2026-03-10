from datetime import datetime, timezone
from scripts.scraper.config import DEFAULT_WATCH_STATUS, DEFAULT_CONNECTION_STATUS, DEFAULT_PRIMARY_ROLE


def map_profile_to_creator(profile: dict, linkedin_url: str) -> dict:
    """Map a Proxycurl profile response to the Creator schema."""
    # Build location from city/state/country
    location_parts = [
        profile.get("city"),
        profile.get("state"),
        profile.get("country_full_name"),
    ]
    location = ", ".join(p for p in location_parts if p) or None

    # Get current company from experiences
    firm = None
    experiences = profile.get("experiences") or []
    for exp in experiences:
        if exp.get("ends_at") is None:  # current position
            firm = exp.get("company")
            break
    if not firm and experiences:
        firm = experiences[0].get("company")

    # Extract handle from public_identifier or URL
    handle = profile.get("public_identifier")
    if not handle:
        handle = linkedin_url.rstrip("/").split("/")[-1]

    # Social links from extra field
    extra = profile.get("extra") or {}
    twitter_url = extra.get("twitter_profile_id")
    if twitter_url and not twitter_url.startswith("http"):
        twitter_url = f"https://twitter.com/{twitter_url}"

    # Build tags from skills/industries
    tags = []
    for skill in (profile.get("skills") or []):
        if isinstance(skill, str):
            tags.append(skill)
        elif isinstance(skill, dict):
            tags.append(skill.get("name", ""))
    tags = [t for t in tags if t][:10]  # cap at 10

    now = datetime.now(timezone.utc).isoformat()

    creator = {
        "fullName": profile.get("full_name") or f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip(),
        "linkedinUrl": linkedin_url,
        "handle": handle,
        "location": location,
        "firmOrCompany": firm,
        "bio": profile.get("headline") or profile.get("summary"),
        "primaryRole": DEFAULT_PRIMARY_ROLE,
        "contentNiche": None,
        "stageFocus": None,
        "geographyFocus": None,
        "tags": tags,
        "followerCount": profile.get("follower_count"),
        "followerCountUpdatedAt": now,
        "estimatedEngagementRate": None,  # computed after posts
        "hasTwitter": bool(twitter_url),
        "twitterUrl": twitter_url,
        "hasSubstack": False,
        "substackUrl": None,
        "hasYoutube": False,
        "youtubeUrl": None,
        "hasPodcast": False,
        "podcastUrl": None,
        "voiceStyle": None,
        "credibilityScore": None,
        "relevanceScore": None,
        "collaborationPotential": False,
        "collaborationNotes": None,
        "watchStatus": DEFAULT_WATCH_STATUS,
        "connectionStatus": DEFAULT_CONNECTION_STATUS,
        "hasInteractedWithContent": False,
        "hasDMedOrMet": False,
        "relationshipNotes": None,
        "addedBy": "scraper",
        "source": "proxycurl",
        "posts": [],
    }

    # Check personal websites for substack/youtube/podcast
    websites = profile.get("personal_urls") or []
    for site in websites:
        url = site if isinstance(site, str) else site.get("url", "")
        url_lower = url.lower()
        if "substack.com" in url_lower:
            creator["hasSubstack"] = True
            creator["substackUrl"] = url
        elif "youtube.com" in url_lower or "youtu.be" in url_lower:
            creator["hasYoutube"] = True
            creator["youtubeUrl"] = url

    return creator
