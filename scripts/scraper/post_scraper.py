import logging
from datetime import datetime, timezone
from scripts.scraper.config import VIRAL_FLAG_MULTIPLIER, DEFAULT_ENGAGEMENT_RATE

logger = logging.getLogger(__name__)


def _detect_format(post: dict) -> str:
    """Detect post format from Proxycurl post data."""
    images = post.get("images") or []
    video = post.get("video") or post.get("video_url")
    article = post.get("article") or post.get("article_url")

    if video:
        return "VIDEO"
    if article:
        return "ARTICLE"
    if len(images) > 1:
        return "CAROUSEL"
    if post.get("poll"):
        return "POLL"
    if post.get("shared_post"):
        return "RESHARE"
    return "TEXT_ONLY"


def _parse_timestamp(ts) -> str | None:
    """Parse Proxycurl timestamp to ISO format."""
    if ts is None:
        return None
    if isinstance(ts, str):
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    return None


def map_posts_to_schema(posts: list[dict], creator_id: str, follower_count: int | None) -> list[dict]:
    """Map Proxycurl post responses to the Post schema."""
    mapped = []
    now = datetime.now(timezone.utc).isoformat()

    for post in posts:
        reactions = post.get("num_likes") or post.get("likes") or 0
        comments = post.get("num_comments") or post.get("comments") or 0
        reposts = post.get("num_shares") or post.get("shares") or post.get("num_reposts") or 0

        # Extract post URL
        post_url = post.get("post_url") or post.get("url") or post.get("share_url")
        if not post_url:
            logger.warning(f"Skipping post with no URL for creator {creator_id}")
            continue

        # Extract post text
        text = post.get("text") or post.get("content") or ""

        mapped_post = {
            "creatorId": creator_id,
            "postUrl": post_url,
            "publishedAt": _parse_timestamp(post.get("posted_at") or post.get("time")),
            "capturedAt": now,
            "format": _detect_format(post),
            "primaryTopic": None,  # filled by enrichment
            "secondaryTopics": [],
            "containsData": False,
            "containsCTA": False,
            "ctaType": None,
            "isOriginal": not bool(post.get("shared_post")),
            "reactions": reactions,
            "comments": comments,
            "reposts": reposts,
            "estimatedImpressions": None,
            "engagementRate": None,
            "viralFlag": False,
            "hookStrength": None,
            "angle": "EDUCATIONAL",  # default, overridden by enrichment
            "keyInsight": None,
            "relevanceToStrategy": None,
            "swipeFileFlag": False,
            "notes": None,
            "_text": text,  # internal field for enrichment, stripped before DB insert
        }
        mapped.append(mapped_post)

    # Compute engagement rates and viral flags
    _compute_engagement_metrics(mapped, follower_count)

    return mapped


def _compute_engagement_metrics(posts: list[dict], follower_count: int | None):
    """Compute engagementRate, viralFlag, and estimatedImpressions for posts."""
    if not posts:
        return

    fc = follower_count or 0

    # Calculate engagement rates
    for post in posts:
        total_engagement = post["reactions"] + post["comments"] + post["reposts"]
        if fc > 0:
            post["engagementRate"] = round(total_engagement / fc, 6)
        else:
            post["engagementRate"] = 0.0

    # Calculate average engagement rate for viral flag
    rates = [p["engagementRate"] for p in posts if p["engagementRate"] > 0]
    avg_rate = sum(rates) / len(rates) if rates else 0.0

    for post in posts:
        # Viral flag: engagement > 2x the creator's average
        if avg_rate > 0 and post["engagementRate"] > avg_rate * VIRAL_FLAG_MULTIPLIER:
            post["viralFlag"] = True

        # Estimated impressions heuristic
        if post["reactions"] > 0:
            rate = post["engagementRate"] if post["engagementRate"] > 0 else DEFAULT_ENGAGEMENT_RATE
            post["estimatedImpressions"] = int(post["reactions"] / rate)
