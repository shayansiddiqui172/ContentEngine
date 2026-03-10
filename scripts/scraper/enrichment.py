import json
import logging
from google import genai
from scripts.scraper.config import GEMINI_API_KEY, GEMINI_RATE_LIMIT
from scripts.scraper.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_rate_limiter = RateLimiter(GEMINI_RATE_LIMIT)

POST_CLASSIFICATION_PROMPT = """Analyze this LinkedIn post and return a JSON object with these fields:
- primaryTopic: main topic (e.g., "AI", "Leadership", "Fundraising", "Product", "Career")
- secondaryTopics: list of 0-3 secondary topics
- angle: one of CONTRARIAN, EDUCATIONAL, INSPIRATIONAL, TACTICAL, OPINION, NARRATIVE
- hookStrength: 1-5 integer (5 = very compelling hook/opening)
- keyInsight: 1-2 sentence summary of the main takeaway
- containsData: true if post cites specific numbers, stats, or data
- containsCTA: true if post has a call to action
- ctaType: if containsCTA, describe the CTA type (e.g., "follow", "comment", "link click", "newsletter signup"), else null
- isOriginal: true if this appears to be original content (not a reshare with minimal commentary)

Respond ONLY with valid JSON, no markdown formatting.

Post text:
{post_text}"""

CREATOR_ENRICHMENT_PROMPT = """Based on these LinkedIn posts from a single creator, analyze their content patterns and return a JSON object:
- contentNiche: their primary content focus area (e.g., "AI/ML", "Venture Capital", "Leadership")
- voiceStyle: describe their writing style in 2-4 words (e.g., "data-driven analytical", "storytelling inspirational", "contrarian provocative")
- primaryRole: best fit from: LP, FOUNDER, VC, OPERATOR, JOURNALIST, ADVISOR

Creator bio: {bio}

Their recent posts:
{posts_text}

Respond ONLY with valid JSON, no markdown formatting."""


def _init_gemini():
    """Initialize Gemini client using the new google.genai SDK."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in environment")
    return genai.Client(api_key=GEMINI_API_KEY)


def _parse_json_response(text: str) -> dict | None:
    """Parse JSON from Gemini response, handling markdown code blocks."""
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

    _rate_limiter.wait()
    try:
        prompt = POST_CLASSIFICATION_PROMPT.format(post_text=text[:3000])
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        result = _parse_json_response(response.text)

        if result:
            post["primaryTopic"] = result.get("primaryTopic")
            post["secondaryTopics"] = result.get("secondaryTopics", [])[:3]
            angle = result.get("angle", "EDUCATIONAL")
            if angle in ("CONTRARIAN", "EDUCATIONAL", "INSPIRATIONAL", "TACTICAL", "OPINION", "NARRATIVE"):
                post["angle"] = angle
            hook = result.get("hookStrength")
            if isinstance(hook, int) and 1 <= hook <= 5:
                post["hookStrength"] = hook
            post["keyInsight"] = result.get("keyInsight")
            post["containsData"] = bool(result.get("containsData"))
            post["containsCTA"] = bool(result.get("containsCTA"))
            post["ctaType"] = result.get("ctaType")
            if result.get("isOriginal") is not None:
                post["isOriginal"] = bool(result.get("isOriginal"))
    except Exception as e:
        logger.error(f"Gemini enrichment failed for post {post.get('postUrl')}: {e}")

    return post


def enrich_creator(client, creator: dict) -> dict:
    """Enrich creator with aggregated insights from their posts."""
    posts = creator.get("posts", [])
    posts_with_text = [p for p in posts if p.get("_text", "").strip()]

    if not posts_with_text:
        logger.debug(f"No post text for creator enrichment: {creator.get('fullName')}")
        return creator

    posts_text = "\n---\n".join(
        p.get("_text", "")[:500] for p in posts_with_text[:5]
    )

    _rate_limiter.wait()
    try:
        prompt = CREATOR_ENRICHMENT_PROMPT.format(
            bio=creator.get("bio", "N/A"),
            posts_text=posts_text,
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        result = _parse_json_response(response.text)

        if result:
            creator["contentNiche"] = result.get("contentNiche")
            creator["voiceStyle"] = result.get("voiceStyle")
            role = result.get("primaryRole")
            valid_roles = ("LP", "FOUNDER", "VC", "OPERATOR", "JOURNALIST", "ADVISOR")
            if role in valid_roles:
                creator["primaryRole"] = role
    except Exception as e:
        logger.error(f"Gemini creator enrichment failed for {creator.get('fullName')}: {e}")

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
        creator = enrich_creator(client, creator)

    # Compute creator-level estimated engagement rate
    for creator in creators:
        rates = [p["engagementRate"] for p in creator.get("posts", []) if p.get("engagementRate")]
        if rates:
            creator["estimatedEngagementRate"] = round(sum(rates) / len(rates), 6)

    logger.info("Enrichment complete.")
    return creators
