import json
import logging
import time
from google import genai
from scripts.scraper.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.0-flash"
_MAX_RETRIES = 3


def _call_gemini(client, prompt: str) -> str | None:
    """Call Gemini with exponential backoff on 429s."""
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                wait = 15 * (2 ** attempt)
                logger.warning(f"Rate limited by Gemini, waiting {wait}s before retry {attempt + 1}/{_MAX_RETRIES}...")
                time.sleep(wait)
            else:
                raise
    logger.error("Gemini request failed after all retries")
    return None

POST_CLASSIFICATION_PROMPT = """Analyze this LinkedIn post and return a JSON object with these exact fields:

- primaryTopic: main topic (e.g. "AI", "Leadership", "Fundraising", "Product", "VC", "Career")
- topicSubject: 1-2 sentence description of exactly what this post is about
- hookStyle: one of exactly: "Personal", "Inspirational", "Story Telling", "Bold Statement", "Question", "Statistic", "Tactical"
- hookStrength: integer 1-5 (1 = weak/boring opening, 5 = very compelling hook that demands attention)
- tone: one of exactly: "Personal", "Educational", "Inspirational", "Contrarian", "Tactical"
- relevance: one of exactly: "Highly Relevant", "Strongly Relevant", "Moderately Relevant", "Slightly Relevant" — assess relevance to startup founders and VCs
- shareability: integer 1-5 (1 = niche/low shareability, 5 = broadly shareable content that spreads easily)
- engagementScore: integer 1-5 — overall content quality and engagement potential based on structure, clarity, and value
- topicPopularity: 1-2 sentences on how popular or trending this topic is right now in the startup and VC community
- postFrequencyAssessment: 1 sentence on how often creators in this space typically post about this specific topic or content style
- postWorkAnalysis: a detailed paragraph (3-5 sentences) explaining specifically why this post works or doesn't work — analyze the hook effectiveness, content structure, value proposition, emotional resonance or lack thereof, and what the creator did well or could improve

Respond ONLY with valid JSON, no markdown formatting.

Post text:
{post_text}"""

CREATOR_ENRICHMENT_PROMPT = """Based on these LinkedIn posts from a single creator, analyze their content patterns and return a JSON object with these exact fields:

- contentNiche: their primary content focus area (e.g. "AI/ML", "Venture Capital", "Leadership", "Startups", "Deep Tech")
- topVoiceStyle: one of exactly: "Data Driven", "Story Telling", "Tactical", "Contrarian" — pick whichever best describes their dominant style
- credibility: integer 1-5 (1 = unclear expertise or low authority, 5 = highly credible thought leader with demonstrated domain expertise)

Creator bio: {bio}

Their recent posts:
{posts_text}

Respond ONLY with valid JSON, no markdown formatting."""

VALID_HOOK_STYLES = ("Personal", "Inspirational", "Story Telling", "Bold Statement", "Question", "Statistic", "Tactical")
VALID_TONES = ("Personal", "Educational", "Inspirational", "Contrarian", "Tactical")
VALID_RELEVANCE = ("Highly Relevant", "Strongly Relevant", "Moderately Relevant", "Slightly Relevant")
VALID_VOICE_STYLES = ("Data Driven", "Story Telling", "Tactical", "Contrarian")


def _init_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=GEMINI_API_KEY)


def _parse_json_response(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}\nResponse: {text[:500]}")
        return None


def enrich_post(client, post: dict) -> dict:
    """Enrich a single post with Gemini classification."""
    text = post.get("_text", "")
    if not text or len(text.strip()) < 20:
        logger.debug(f"Skipping enrichment for short/empty post: {post.get('postUrl')}")
        return post

    try:
        prompt = POST_CLASSIFICATION_PROMPT.format(post_text=text[:3000])
        raw = _call_gemini(client, prompt)
        result = _parse_json_response(raw) if raw else None

        if result:
            post["primaryTopic"] = result.get("primaryTopic")
            post["topicSubject"] = result.get("topicSubject")

            hook_style = result.get("hookStyle")
            if hook_style in VALID_HOOK_STYLES:
                post["hookStyle"] = hook_style

            hook_strength = result.get("hookStrength")
            if isinstance(hook_strength, int) and 1 <= hook_strength <= 5:
                post["hookStrength"] = hook_strength

            tone = result.get("tone")
            if tone in VALID_TONES:
                post["tone"] = tone

            relevance = result.get("relevance")
            if relevance in VALID_RELEVANCE:
                post["relevance"] = relevance

            shareability = result.get("shareability")
            if isinstance(shareability, int) and 1 <= shareability <= 5:
                post["shareability"] = shareability

            eng_score = result.get("engagementScore")
            if isinstance(eng_score, int) and 1 <= eng_score <= 5:
                post["engagementScore"] = eng_score

            post["topicPopularity"] = result.get("topicPopularity")
            post["postFrequencyAssessment"] = result.get("postFrequencyAssessment")
            post["postWorkAnalysis"] = result.get("postWorkAnalysis")

    except Exception as e:
        logger.error(f"Gemini enrichment failed for post {post.get('postUrl')}: {e}")

    return post


def enrich_creator(client, creator: dict) -> dict:
    """Enrich creator with aggregated insights from their posts."""
    posts = creator.get("posts", [])
    posts_with_text = [p for p in posts if p.get("_text", "").strip()]

    if not posts_with_text:
        logger.debug(f"No post text for creator enrichment: {creator.get('name')}")
        return creator

    posts_text = "\n---\n".join(
        p.get("_text", "")[:500] for p in posts_with_text[:5]
    )

    try:
        prompt = CREATOR_ENRICHMENT_PROMPT.format(
            bio=creator.get("bio", "N/A"),
            posts_text=posts_text,
        )
        raw = _call_gemini(client, prompt)
        result = _parse_json_response(raw) if raw else None

        if result:
            creator["contentNiche"] = result.get("contentNiche")

            voice_style = result.get("topVoiceStyle")
            if voice_style in VALID_VOICE_STYLES:
                creator["topVoiceStyle"] = voice_style

            credibility = result.get("credibility")
            if isinstance(credibility, int) and 1 <= credibility <= 5:
                creator["credibility"] = credibility

    except Exception as e:
        logger.error(f"Gemini creator enrichment failed for {creator.get('name')}: {e}")

    return creator


def run_enrichment(creators: list[dict], skip: bool = False) -> list[dict]:
    """Run Gemini enrichment on all creators and their posts."""
    if skip:
        logger.info("Skipping Gemini enrichment (--skip-enrich)")
        return creators

    client = _init_gemini()
    total_posts = sum(len(c.get("posts", [])) for c in creators)
    logger.info(f"Enriching {len(creators)} creators, {total_posts} posts with Gemini...")

    for creator in creators:
        for i, post in enumerate(creator.get("posts", [])):
            creator["posts"][i] = enrich_post(client, post)
        enrich_creator(client, creator)

    # Compute creator-level estimated engagement rate (average of post rates)
    for creator in creators:
        rates = [p["engagementRate"] for p in creator.get("posts", []) if p.get("engagementRate")]
        if rates:
            creator["estimatedEngagementRate"] = round(sum(rates) / len(rates), 6)

    logger.info("Enrichment complete.")
    return creators
