import logging
import re
from datetime import datetime, timezone
from scripts.scraper.config import VIRAL_FLAG_MULTIPLIER, DEFAULT_ENGAGEMENT_RATE

logger = logging.getLogger(__name__)

# ── Computed field helpers ─────────────────────────────────────────────────────

def _extract_hook(text: str) -> str | None:
    """First 1-2 sentences of the post (the hook)."""
    if not text or len(text.strip()) < 10:
        return None
    text = text.strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return None
    hook = sentences[0]
    if len(hook) < 80 and len(sentences) > 1:
        hook = hook + " " + sentences[1]
    return hook[:300]


_DATA_RE = re.compile(
    r'\b\d+[\.,]?\d*\s*%'              # percentages: 75%, 3.5%
    r'|\$\s*\d[\d,\.]*[KkMmBb]?\b'    # dollar amounts: $1M, $500k
    r'|\b\d+\s*[xX]\b'                # multipliers: 3x, 10x
    r'|\b\d{1,3}(?:,\d{3})+\b'        # large numbers with commas: 1,000,000
    r'|\b(?:study|research|survey|report|according\s+to|data\s+shows?|statistics?)\b',
    re.IGNORECASE,
)

def _detect_contains_data(text: str) -> bool:
    return bool(_DATA_RE.search(text))


_CTA_RE = re.compile(
    r'\b(?:follow\s+(?:me|for|along)|subscribe|comment\s+below|drop\s+a\s+comment|'
    r'DM\s+me|send\s+me\s+a|reach\s+out|connect\s+with\s+me|link\s+in\s+(?:my\s+)?bio|'
    r'click\s+(?:the\s+)?link|share\s+this|repost\s+(?:this|if)|check\s+out|'
    r'let\s+me\s+know(?:\s+in\s+the\s+comments)?|tag\s+someone|'
    r'what(?:\'s|\s+is|\s+are)?\s+your\s+(?:thoughts?|take|opinion)|'
    r'thoughts?\s*\?|agree\s*\?|thoughts?\s+below)\b',
    re.IGNORECASE,
)

def _extract_cta(text: str) -> tuple[bool, str | None]:
    """Returns (containsCTA, ctaText). Checks last 3 paragraphs/sentences first."""
    if not text:
        return False, None
    # Split on double newlines (paragraphs) or sentence boundaries
    chunks = [s.strip() for s in re.split(r'\n\n+|(?<=[.!?])\s+', text.strip()) if s.strip()]
    # Check last 3 chunks where CTAs usually live
    for chunk in reversed(chunks[-3:]):
        if _CTA_RE.search(chunk):
            return True, chunk[:300]
    # Fallback: check full text
    if _CTA_RE.search(text):
        return True, None
    return False, None


def _detect_format(post: dict) -> str:
    """Map PhantomBuster type/content to DB2 POST FORMAT values."""
    t = (post.get("type") or "").lower()
    text = post.get("postContent") or ""
    has_image = bool(post.get("imgUrl"))

    if "video" in t:
        return "Video"
    if "document" in t:
        # LinkedIn document = carousel (image + text)
        return "Long Text + Image"
    if "article" in t:
        return "Long Text"
    if post.get("sharedPostUrl"):
        return "Short Text"
    if has_image:
        return "Long Text + Image" if len(text) > 300 else "Image"
    return "Long Text" if len(text) > 300 else "Short Text"


def _parse_timestamp(ts) -> str | None:
    if not ts:
        return None
    if isinstance(ts, str):
        if "T" in ts or "-" in ts[:10]:
            return ts
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    return None


def map_posts_to_schema(posts: list[dict], creator_id: str, follower_count: int | None) -> list[dict]:
    """Map PhantomBuster LinkedIn Activity Extractor rows to the Post schema."""
    mapped = []
    now = datetime.now(timezone.utc).isoformat()

    for post in posts:
        post_url = post.get("postUrl") or ""
        if not post_url:
            continue

        try:
            reactions = int(post.get("likeCount") or 0)
        except (ValueError, TypeError):
            reactions = 0
        try:
            comments = int(post.get("commentCount") or 0)
        except (ValueError, TypeError):
            comments = 0
        try:
            reposts = int(post.get("repostCount") or 0)
        except (ValueError, TypeError):
            reposts = 0

        text = post.get("postContent") or ""
        published_at = _parse_timestamp(post.get("postTimestamp")) or _parse_timestamp(post.get("postDate"))

        contains_cta, cta_text = _extract_cta(text)

        mapped_post = {
            # Identification
            "creatorId": creator_id,
            "postUrl": post_url,
            # Timing
            "publishedAt": published_at,
            "capturedAt": now,
            # Format
            "postFormat": _detect_format(post),
            # Topic (AI-enriched)
            "primaryTopic": None,
            "topicSubject": None,
            # Content flags — containsData and CTA computed from text
            "containsData": _detect_contains_data(text),
            "relevance": None,
            # Hook — extracted from text; style/strength are AI-enriched
            "hook": _extract_hook(text),
            "hookStyle": None,
            "hookStrength": None,
            # Tone (AI-enriched)
            "tone": None,
            # CTA — presence and text computed from text
            "containsCTA": contains_cta,
            "ctaText": cta_text,
            # Raw engagement (from PhantomBuster)
            "reactions": reactions,
            "comments": comments,
            "reposts": reposts,
            # Computed engagement metrics
            "engagementRate": None,
            "estimatedImpressions": None,
            "viralFlag": False,
            "postPerformance": None,
            # Qualitative AI analysis
            "shareability": None,
            "engagementScore": None,
            "topicPopularity": None,
            "postFrequencyAssessment": None,
            "postWorkAnalysis": None,
            # Raw text for enrichment (stripped before saving to JSON)
            "_text": text,
        }
        mapped.append(mapped_post)

    _compute_engagement_metrics(mapped, follower_count)
    return mapped


def _compute_engagement_metrics(posts: list[dict], follower_count: int | None):
    """Compute per-post engagement rates, viral flags, estimated impressions, and post performance."""
    fc = follower_count or 0

    for post in posts:
        total = post["reactions"] + post["comments"] + post["reposts"]
        post["engagementRate"] = round(total / fc, 6) if fc > 0 else 0.0

    rates = [p["engagementRate"] for p in posts if p["engagementRate"] > 0]
    avg_rate = sum(rates) / len(rates) if rates else 0.0

    for post in posts:
        rate = post["engagementRate"]

        # Viral flag
        if avg_rate > 0 and rate > avg_rate * VIRAL_FLAG_MULTIPLIER:
            post["viralFlag"] = True

        # Estimated impressions
        if post["reactions"] > 0:
            effective_rate = rate if rate > 0 else DEFAULT_ENGAGEMENT_RATE
            post["estimatedImpressions"] = int(post["reactions"] / effective_rate)

        # Post performance tier (relative to creator average)
        if avg_rate > 0:
            if rate >= avg_rate * 1.5:
                post["postPerformance"] = "Above Average Engagement"
            elif rate <= avg_rate * 0.5:
                post["postPerformance"] = "Below Average Engagement"
            else:
                post["postPerformance"] = "Average Engagement"
