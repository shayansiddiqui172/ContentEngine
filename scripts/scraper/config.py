import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
PHANTOMBUSTER_API_KEY = os.getenv("PHANTOMBUSTER_API_KEY")
PHANTOMBUSTER_PROFILE_AGENT_ID = os.getenv("PHANTOMBUSTER_PROFILE_AGENT_ID")
PHANTOMBUSTER_ACTIVITY_AGENT_ID = os.getenv("PHANTOMBUSTER_ACTIVITY_AGENT_ID")

# Thresholds
VIRAL_FLAG_MULTIPLIER = 2.0  # engagement > 2x creator average = viral
DEFAULT_ENGAGEMENT_RATE = 0.02  # 2% fallback for impression estimation

# Defaults for manual fields
DEFAULT_CONNECTION_STATUS = "NOT_CONNECTED"
DEFAULT_PRIMARY_ROLE = "Startup"

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENRICHED_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "data", "enriched_creators.json")
DB1_XLSX_PATH = os.path.join(PROJECT_ROOT, "data", "DB1_Creator_Profiles.xlsx")
DB2_XLSX_PATH = os.path.join(PROJECT_ROOT, "data", "DB2_Post_Analysis.xlsx")

# DB1 — Creator Profiles columns (exact order)
DB1_COLUMNS = [
    "NAME",
    "BIO",
    "FOLLOWER COUNT (RANGE)",
    "FOLLOWER COUNT (#)",
    "LOCATION",
    "FIRM AFFILIATION",
    "DATE ADDED",
    "OVERALL NOTES",
    "PRIMARY ROLE",
    "CONTENT NICHE",
    "GROWTH STAGE",
    "GEOGRAPHY FOCUS",
    "COUNT OF CROSS-PLATFORM PRESENCE",
    "TOP VOICE STYLE",
    "CREDIBILITY (1-5)",
    "COLLABORATION POTENTIAL?",
    "POSTING FREQUENCY",
    "CONNECTION STATUS",
    "HAVE INTERACTED W/CONTENT?",
    "HAVE DMED YET?",
    "NOTES FOR RELATIONSHIP HISTORY",
    "LINKEDIN LINK",
]

# DB2 — Post Analysis columns (exact order)
DB2_COLUMNS = [
    "NAME",
    "POST DATE",
    "POST FORMAT",
    "PRIMARY TOPIC",
    "TOPIC/SUBJECT OF THE POST",
    "DOES IT CONTAIN DATA/STATS?",
    "RELEVANCE (to startups/VC)",
    "HOOK",
    "HOOK STYLE",
    "HOOK STRENGTH (1-5)",
    "TONE",
    "DOES IT CONTAIN CTA?",
    "WHAT CTA?",
    "LIKES",
    "COMMENTS",
    "SHARES/REPOSTS",
    "SHAREABILITY (1-5)",
    "ENGAGEMENT SCORE (1-5)",
    "POST PERFORMANCE",
    "TOPIC/SUBJECT POPULARITY",
    "POST FREQUENCY",
    "LINK TO POST",
    "Does this post work or not work?",
]

# Helper-row descriptions for DB1 (row 2 in spreadsheet)
DB1_DESCRIPTIONS = {
    "NAME": "Full name of the creator",
    "BIO": "LinkedIn headline or bio",
    "FOLLOWER COUNT (RANGE)": "Bucketed follower range (e.g. 10k-25k, 500k+)",
    "FOLLOWER COUNT (#)": "Exact follower count from LinkedIn",
    "LOCATION": "City, region, or country",
    "FIRM AFFILIATION": "Company or firm they're associated with",
    "DATE ADDED": "Date first added to this tracker",
    "OVERALL NOTES": "General notes about this creator (manual)",
    "PRIMARY ROLE": "VC / Investor | Ecosystem Partner | Startup | AI",
    "CONTENT NICHE": "Main content focus area (e.g. AI/ML, VC, Leadership)",
    "GROWTH STAGE": "Established Creator (50k+) | Emerging Creator (<50k)",
    "GEOGRAPHY FOCUS": "Geographic focus of their content (e.g. Canada, Global)",
    "COUNT OF CROSS-PLATFORM PRESENCE": "# of platforms active on beyond LinkedIn",
    "TOP VOICE STYLE": "Data Driven | Story Telling | Tactical | Contrarian",
    "CREDIBILITY (1-5)": "1 = low, 5 = highly credible and authoritative",
    "COLLABORATION POTENTIAL?": "Y / N or notes on collaboration fit (manual)",
    "POSTING FREQUENCY": "Daily | 3-4/week | 1-2/week | < a month",
    "CONNECTION STATUS": "LinkedIn connection status (manual)",
    "HAVE INTERACTED W/CONTENT?": "Y / N — have we liked or commented? (manual)",
    "HAVE DMED YET?": "Y / N — have we sent a DM? (manual)",
    "NOTES FOR RELATIONSHIP HISTORY": "Notes on past interactions (manual)",
    "LINKEDIN LINK": "Full LinkedIn profile URL",
}

# Helper-row descriptions for DB2 (row 2 in spreadsheet)
DB2_DESCRIPTIONS = {
    "NAME": "Creator's name",
    "POST DATE": "Date the post was published (YYYY-MM-DD)",
    "POST FORMAT": "Short Text | Long Text | Long Text + Image | Image | Video",
    "PRIMARY TOPIC": "Main topic (e.g. AI, VC, Leadership, Fundraising)",
    "TOPIC/SUBJECT OF THE POST": "1-2 sentence description of what the post is about",
    "DOES IT CONTAIN DATA/STATS?": "Y / N — does it cite specific numbers or stats?",
    "RELEVANCE (to startups/VC)": "Highly Relevant | Strongly Relevant | Moderately Relevant | Slightly Relevant",
    "HOOK": "The opening line(s) that hook the reader",
    "HOOK STYLE": "Personal | Inspirational | Story Telling | Bold Statement | Question | Statistic | Tactical",
    "HOOK STRENGTH (1-5)": "1 = weak hook, 5 = very compelling hook",
    "TONE": "Personal | Educational | Inspirational | Contrarian | Tactical",
    "DOES IT CONTAIN CTA?": "Y / N — does it have a call to action?",
    "WHAT CTA?": "The actual call-to-action text if present",
    "LIKES": "Number of likes / reactions",
    "COMMENTS": "Number of comments",
    "SHARES/REPOSTS": "Number of shares or reposts",
    "SHAREABILITY (1-5)": "1 = low shareability, 5 = highly shareable content",
    "ENGAGEMENT SCORE (1-5)": "Overall content quality and engagement potential",
    "POST PERFORMANCE": "Above Average Engagement | Average Engagement | Below Average Engagement",
    "TOPIC/SUBJECT POPULARITY": "How popular or trending this topic is in the startup/VC space",
    "POST FREQUENCY": "How often this creator posts about this type of content",
    "LINK TO POST": "Direct URL to the LinkedIn post",
    "Does this post work or not work?": "Qualitative paragraph: why this post works or doesn't (manual edits preserved)",
}


def follower_count_range(count) -> str | None:
    """Bucket an exact follower count into a display range string."""
    if count is None:
        return None
    try:
        count = int(count)
    except (ValueError, TypeError):
        return None
    if count < 1_000:
        return "< 1k"
    if count < 5_000:
        return "1k-5k"
    if count < 10_000:
        return "5k-10k"
    if count < 25_000:
        return "10k-25k"
    if count < 50_000:
        return "25k-50k"
    if count < 100_000:
        return "50k-100k"
    if count < 250_000:
        return "100k-250k"
    if count < 500_000:
        return "250k-500k"
    return "500k+"
