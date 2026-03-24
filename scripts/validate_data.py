"""Post-pipeline data quality checks.

Validates both:
  1. The enriched_creators.json output (new schema fields)
  2. The PostgreSQL database (if DATABASE_URL is set)
"""

import json
import os
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
JSON_PATH = os.path.join(DATA_DIR, "enriched_creators.json")
DB1_PATH  = os.path.join(DATA_DIR, "DB1_Creator_Profiles.xlsx")
DB2_PATH  = os.path.join(DATA_DIR, "DB2_Post_Analysis.xlsx")

# Fields expected to be populated by the pipeline (not manual)
REQUIRED_CREATOR_FIELDS = [
    "name", "linkedinUrl", "followerCount", "bio",
    "primaryRole", "contentNiche", "topVoiceStyle", "credibility",
    "growthStage", "postingFrequency",
]
REQUIRED_POST_FIELDS = [
    "postUrl", "publishedAt", "postFormat", "primaryTopic",
    "topicSubject", "hook", "hookStyle", "hookStrength",
    "tone", "relevance", "shareability", "engagementScore",
    "postPerformance", "postWorkAnalysis",
]

VALID_POST_FORMATS   = {"Short Text", "Long Text", "Long Text + Image", "Image", "Video"}
VALID_HOOK_STYLES    = {"Personal", "Inspirational", "Story Telling", "Bold Statement", "Question", "Statistic", "Tactical"}
VALID_TONES          = {"Personal", "Educational", "Inspirational", "Contrarian", "Tactical"}
VALID_RELEVANCE      = {"Highly Relevant", "Strongly Relevant", "Moderately Relevant", "Slightly Relevant"}
VALID_PERFORMANCE    = {"Above Average Engagement", "Average Engagement", "Below Average Engagement"}
VALID_VOICE_STYLES   = {"Data Driven", "Story Telling", "Tactical", "Contrarian"}
VALID_PRIMARY_ROLES  = {"VC / Investor", "Ecosystem Partner", "Startup", "AI"}
VALID_GROWTH_STAGES  = {"Established Creator", "Emerging Creator"}
VALID_POSTING_FREQ   = {"Daily", "3-4/week", "1-2/week", "< a month"}


def _validate_json():
    """Validate the enriched_creators.json output against the new schema."""
    if not os.path.exists(JSON_PATH):
        print(f"  [SKIP] {JSON_PATH} not found")
        return

    with open(JSON_PATH) as f:
        creators = json.load(f)

    print(f"\n{'='*60}")
    print(f"JSON VALIDATION — {JSON_PATH}")
    print(f"{'='*60}")
    print(f"  Creators: {len(creators)}")
    print(f"  Posts:    {sum(len(c.get('posts', [])) for c in creators)}")

    creator_warnings = 0
    post_warnings = 0

    for creator in creators:
        name = creator.get("name") or creator.get("fullName") or "(unnamed)"

        # Check required fields
        missing = [f for f in REQUIRED_CREATOR_FIELDS if not creator.get(f)]
        if missing:
            print(f"  [WARN] {name}: missing fields: {missing}")
            creator_warnings += 1

        # Validate enum values
        if creator.get("topVoiceStyle") and creator["topVoiceStyle"] not in VALID_VOICE_STYLES:
            print(f"  [WARN] {name}: invalid topVoiceStyle='{creator['topVoiceStyle']}'")
            creator_warnings += 1
        if creator.get("primaryRole") and creator["primaryRole"] not in VALID_PRIMARY_ROLES:
            print(f"  [WARN] {name}: invalid primaryRole='{creator['primaryRole']}'")
            creator_warnings += 1
        if creator.get("growthStage") and creator["growthStage"] not in VALID_GROWTH_STAGES:
            print(f"  [WARN] {name}: invalid growthStage='{creator['growthStage']}'")
            creator_warnings += 1
        if creator.get("postingFrequency") and creator["postingFrequency"] not in VALID_POSTING_FREQ:
            print(f"  [WARN] {name}: invalid postingFrequency='{creator['postingFrequency']}'")
            creator_warnings += 1
        credibility = creator.get("credibility")
        if credibility is not None and not (isinstance(credibility, int) and 1 <= credibility <= 5):
            print(f"  [WARN] {name}: credibility out of range: {credibility}")
            creator_warnings += 1

        for post in creator.get("posts", []):
            post_url = post.get("postUrl", "(no url)")

            missing_p = [f for f in REQUIRED_POST_FIELDS if not post.get(f)]
            if missing_p:
                print(f"  [WARN] post {post_url[-60:]}: missing fields: {missing_p}")
                post_warnings += 1

            if post.get("postFormat") and post["postFormat"] not in VALID_POST_FORMATS:
                print(f"  [WARN] post {post_url[-60:]}: invalid format='{post['postFormat']}'")
                post_warnings += 1
            if post.get("hookStyle") and post["hookStyle"] not in VALID_HOOK_STYLES:
                print(f"  [WARN] post {post_url[-60:]}: invalid hookStyle='{post['hookStyle']}'")
                post_warnings += 1
            if post.get("tone") and post["tone"] not in VALID_TONES:
                print(f"  [WARN] post {post_url[-60:]}: invalid tone='{post['tone']}'")
                post_warnings += 1
            if post.get("relevance") and post["relevance"] not in VALID_RELEVANCE:
                print(f"  [WARN] post {post_url[-60:]}: invalid relevance='{post['relevance']}'")
                post_warnings += 1
            if post.get("postPerformance") and post["postPerformance"] not in VALID_PERFORMANCE:
                print(f"  [WARN] post {post_url[-60:]}: invalid postPerformance='{post['postPerformance']}'")
                post_warnings += 1
            for score_field in ("hookStrength", "shareability", "engagementScore"):
                val = post.get(score_field)
                if val is not None and not (isinstance(val, int) and 1 <= val <= 5):
                    print(f"  [WARN] post {post_url[-60:]}: {score_field}={val} out of 1-5 range")
                    post_warnings += 1

    if creator_warnings == 0 and post_warnings == 0:
        print("  All fields valid.")
    else:
        print(f"\n  Summary: {creator_warnings} creator warning(s), {post_warnings} post warning(s)")


def _validate_spreadsheets():
    """Report on what's in the spreadsheet files."""
    print(f"\n{'='*60}")
    print("SPREADSHEET STATUS")
    print(f"{'='*60}")
    for path, label in ((DB1_PATH, "DB1_Creator_Profiles.xlsx"), (DB2_PATH, "DB2_Post_Analysis.xlsx")):
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  {label}: {size_kb:.1f} KB")
        else:
            print(f"  {label}: NOT FOUND (will be created on next run)")


def _validate_db():
    """Run quality checks against the PostgreSQL database."""
    if not DATABASE_URL:
        print("\n  [SKIP] DATABASE_URL not set — skipping DB checks")
        return

    try:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"\n  [SKIP] Could not connect to DB: {e}")
        return

    print(f"\n{'='*60}")
    print("DATABASE VALIDATION")
    print(f"{'='*60}")

    try:
        cur.execute('SELECT COUNT(*) FROM creators')
        creators_count = cur.fetchone()[0]
        cur.execute('SELECT COUNT(*) FROM posts')
        posts_count = cur.fetchone()[0]
        print(f"  Total creators: {creators_count}")
        print(f"  Total posts:    {posts_count}")

        # Creator overview
        cur.execute("""
            SELECT "fullName", "followerCount", "voiceStyle", "connectionStatus"
            FROM creators
            ORDER BY "followerCount" DESC NULLS LAST
        """)
        rows = cur.fetchall()
        print(f"\n  {'Name':<25} {'Followers':<12} {'Voice Style':<20} {'Connection':<15}")
        print("  " + "-" * 72)
        for row in rows:
            name  = (row[0] or "N/A")[:24]
            foll  = str(row[1]) if row[1] is not None else "N/A"
            voice = (row[2] or "N/A")[:19]
            conn_ = (row[3] or "N/A")[:14]
            print(f"  {name:<25} {foll:<12} {voice:<20} {conn_:<15}")

        # Completeness check
        print("\n  --- Completeness (key DB fields) ---")
        cur.execute("""
            SELECT "fullName",
                (CASE WHEN "fullName"             IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "location"             IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "firmOrCompany"        IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "bio"                  IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "followerCount"        IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "contentNiche"         IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "voiceStyle"           IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "credibilityScore"     IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "estimatedEngagementRate" IS NOT NULL THEN 1 ELSE 0 END
                ) AS filled
            FROM creators
            ORDER BY filled ASC
        """)
        for row in cur.fetchall():
            print(f"  {(row[0] or 'N/A'):<28} {row[1]}/9 fields filled")

        # Staleness
        print("\n  --- Staleness (not updated in 30+ days) ---")
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        cur.execute("""
            SELECT "fullName", "updatedAt"
            FROM creators WHERE "updatedAt" < %s ORDER BY "updatedAt" ASC
        """, (threshold,))
        stale = cur.fetchall()
        if stale:
            print(f"  WARNING: {len(stale)} creator(s) stale:")
            for row in stale:
                print(f"    - {row[0] or 'N/A'}: last updated {row[1]}")
        else:
            print("  All creators updated within 30 days.")

        # Post enrichment coverage
        cur.execute('SELECT COUNT(*) FROM posts WHERE "primaryTopic" IS NOT NULL')
        enriched = cur.fetchone()[0]
        print(f"\n  Posts with AI enrichment: {enriched}/{posts_count}")

        cur.execute('SELECT COUNT(*) FROM posts WHERE "hookStrength" IS NOT NULL')
        with_hook = cur.fetchone()[0]
        print(f"  Posts with hook strength: {with_hook}/{posts_count}")

        # Posts per creator
        print("\n  --- Posts per creator ---")
        cur.execute("""
            SELECT c."fullName", COUNT(p.id) AS post_count,
                   ROUND(AVG(p."engagementRate")::numeric, 4) AS avg_eng
            FROM creators c
            LEFT JOIN posts p ON c.id = p."creatorId"
            GROUP BY c.id, c."fullName"
            ORDER BY post_count DESC
        """)
        for row in cur.fetchall():
            print(f"  {(row[0] or 'N/A'):<28} {row[1]} posts  avg eng: {row[2] or 'N/A'}")

    except Exception as e:
        print(f"  DB validation error: {e}")
    finally:
        cur.close()
        conn.close()


def main():
    _validate_json()
    _validate_spreadsheets()
    _validate_db()


if __name__ == "__main__":
    main()
