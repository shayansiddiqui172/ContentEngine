import json
import logging
import os
from datetime import datetime, timezone
import psycopg2
from scripts.scraper.config import DATABASE_URL

logger = logging.getLogger(__name__)

# Fields to UPDATE on creator conflict (do not include id, createdAt, linkedinUrl)
CREATOR_UPSERT_FIELDS = [
    "fullName", "handle", "location", "firmOrCompany", "bio",
    "primaryRole", "contentNiche", "stageFocus", "geographyFocus", "tags",
    "followerCount", "followerCountUpdatedAt", "estimatedEngagementRate",
    "hasTwitter", "twitterUrl", "hasSubstack", "substackUrl",
    "hasYoutube", "youtubeUrl", "hasPodcast", "podcastUrl",
    "voiceStyle", "credibilityScore", "relevanceScore",
    "collaborationPotential", "collaborationNotes",
    "watchStatus", "connectionStatus",
    "hasInteractedWithContent", "hasDMedOrMet", "relationshipNotes",
    "addedBy", "source", "updatedAt",
]

POST_UPSERT_FIELDS = [
    "creatorId", "publishedAt", "capturedAt", "format",
    "primaryTopic", "secondaryTopics", "containsData", "containsCTA", "ctaType",
    "isOriginal", "reactions", "comments", "reposts",
    "estimatedImpressions", "engagementRate", "viralFlag",
    "hookStrength", "angle", "keyInsight", "summary", "whatItDoesWell",
    "relevanceToStrategy", "swipeFileFlag", "notes",
]

CREATOR_INSERT_FIELDS = ["fullName", "linkedinUrl"] + [
    f for f in CREATOR_UPSERT_FIELDS if f not in ("fullName", "updatedAt")
]
POST_INSERT_FIELDS = ["postUrl"] + POST_UPSERT_FIELDS

# Map internal primaryRole values → DB PrimaryRole enum
_ROLE_TO_DB = {
    "VC / Investor": "VC",
    "Startup": "FOUNDER",
    "AI": "OPERATOR",
    "Ecosystem Partner": "OPERATOR",
}

# Map new internal field names → DB column names for creators
_CREATOR_FIELD_MAP = {
    "name": "fullName",
    "firmAffiliation": "firmOrCompany",
    "topVoiceStyle": "voiceStyle",
    "credibility": "credibilityScore",
    "growthStage": "stageFocus",
    "haveInteracted": "hasInteractedWithContent",
    "haveDMed": "hasDMedOrMet",
}

# Map new internal field names → DB column names for posts
_POST_FIELD_MAP = {
    "postFormat": "format",
    "topicSubject": "keyInsight",
    "ctaText": "ctaType",
    "postWorkAnalysis": "whatItDoesWell",
}

# Map tone values → DB Angle enum
_TONE_TO_ANGLE = {
    "Educational": "EDUCATIONAL",
    "Contrarian": "CONTRARIAN",
    "Inspirational": "INSPIRATIONAL",
    "Tactical": "TACTICAL",
    "Personal": "OPINION",
}

# Map new post format values → DB Format enum
_FORMAT_TO_DB = {
    "Short Text": "TEXT_ONLY",
    "Long Text": "TEXT_ONLY",
    "Long Text + Image": "CAROUSEL",
    "Image": "CAROUSEL",
    "Video": "VIDEO",
}


def _resolve(record: dict, key: str):
    """Get value from a record, trying the new field name first, then the old DB name."""
    value = record.get(key)
    if value is None:
        # Try the reverse mapping (old name as fallback)
        old_name = _CREATOR_FIELD_MAP.get(key) or _POST_FIELD_MAP.get(key)
        if old_name:
            value = record.get(old_name)
    if key in ("tags", "secondaryTopics"):
        return value if value is not None else []
    return value


def _build_creator_db_record(creator: dict) -> dict:
    """Map internal creator dict to DB column values."""
    now = datetime.now(timezone.utc).isoformat()

    # Handle collaborationPotential: could be None, bool, or string like "Y" / notes
    collab_raw = (
        creator.get("collaborationPotential")
        or creator.get("collaborationNotes")
    )
    if isinstance(collab_raw, bool):
        collab_bool = collab_raw
        collab_notes = None
    elif isinstance(collab_raw, str):
        collab_bool = collab_raw.strip().upper().startswith("Y")
        collab_notes = collab_raw if len(collab_raw) > 1 else None
    else:
        collab_bool = False
        collab_notes = None

    linkedin_url = creator.get("linkedinUrl", "")
    handle = linkedin_url.rstrip("/").split("/")[-1] if linkedin_url else None

    return {
        "fullName": creator.get("name") or creator.get("fullName"),
        "linkedinUrl": linkedin_url,
        "handle": handle,
        "location": creator.get("location"),
        "firmOrCompany": creator.get("firmAffiliation") or creator.get("firmOrCompany"),
        "bio": creator.get("bio"),
        "primaryRole": _ROLE_TO_DB.get(creator.get("primaryRole", "Startup"), "FOUNDER"),
        "contentNiche": creator.get("contentNiche"),
        "stageFocus": creator.get("growthStage") or creator.get("stageFocus"),
        "geographyFocus": creator.get("geographyFocus"),
        "tags": [],
        "followerCount": creator.get("followerCount"),
        "followerCountUpdatedAt": creator.get("dateAdded") or now,
        "estimatedEngagementRate": creator.get("estimatedEngagementRate"),
        "hasTwitter": False,
        "twitterUrl": None,
        "hasSubstack": False,
        "substackUrl": None,
        "hasYoutube": False,
        "youtubeUrl": None,
        "hasPodcast": False,
        "podcastUrl": None,
        "voiceStyle": creator.get("topVoiceStyle") or creator.get("voiceStyle"),
        "credibilityScore": creator.get("credibility") or creator.get("credibilityScore"),
        "relevanceScore": None,
        "collaborationPotential": collab_bool,
        "collaborationNotes": collab_notes,
        "watchStatus": "PASSIVE",
        "connectionStatus": creator.get("connectionStatus", "NOT_CONNECTED"),
        "hasInteractedWithContent": bool(
            creator.get("haveInteracted") or creator.get("hasInteractedWithContent")
        ),
        "hasDMedOrMet": bool(creator.get("haveDMed") or creator.get("hasDMedOrMet")),
        "relationshipNotes": creator.get("relationshipNotes"),
        "addedBy": "scraper",
        "source": "phantombuster",
        "updatedAt": now,
    }


def _build_post_db_record(post: dict, creator_db_id: str) -> dict:
    """Map internal post dict to DB column values."""
    now = datetime.now(timezone.utc).isoformat()

    raw_format = post.get("postFormat") or post.get("format") or "Short Text"
    db_format = _FORMAT_TO_DB.get(raw_format, "TEXT_ONLY")

    tone = post.get("tone") or "Educational"
    db_angle = _TONE_TO_ANGLE.get(tone, "EDUCATIONAL")

    return {
        "creatorId": creator_db_id,
        "postUrl": post.get("postUrl"),
        "publishedAt": post.get("publishedAt"),
        "capturedAt": post.get("capturedAt") or now,
        "format": db_format,
        "primaryTopic": post.get("primaryTopic"),
        "secondaryTopics": [],
        "containsData": bool(post.get("containsData")),
        "containsCTA": bool(post.get("containsCTA")),
        "ctaType": post.get("ctaText") or post.get("ctaType"),
        "isOriginal": not bool(post.get("postUrl", "").find("sharedPost") >= 0),
        "reactions": post.get("reactions", 0),
        "comments": post.get("comments", 0),
        "reposts": post.get("reposts", 0),
        "estimatedImpressions": post.get("estimatedImpressions"),
        "engagementRate": post.get("engagementRate"),
        "viralFlag": bool(post.get("viralFlag")),
        "hookStrength": post.get("hookStrength"),
        "angle": db_angle,
        "keyInsight": post.get("topicSubject") or post.get("keyInsight"),
        "summary": post.get("topicSubject") or post.get("summary"),
        "whatItDoesWell": post.get("postWorkAnalysis") or post.get("whatItDoesWell"),
        "relevanceToStrategy": None,
        "swipeFileFlag": False,
        "notes": None,
    }


def main():
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "enriched_creators.json",
    )
    logger.info(f"Reading from {data_path}")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        with open(data_path, "r") as f:
            creators = json.load(f)

        creator_count = 0
        post_count = 0

        for creator in creators:
            db_creator = _build_creator_db_record(creator)

            insert_fields = [f'"{f}"' for f in CREATOR_INSERT_FIELDS]
            insert_values = [db_creator.get(f) for f in CREATOR_INSERT_FIELDS]

            update_set = ", ".join(
                f'"{f}" = EXCLUDED."{f}"' for f in CREATOR_UPSERT_FIELDS
            )

            insert_sql = f"""
                INSERT INTO creators ({', '.join(insert_fields)})
                VALUES ({', '.join(['%s'] * len(insert_fields))})
                ON CONFLICT ("linkedinUrl") DO UPDATE SET {update_set}
                RETURNING "id"
            """
            cur.execute(insert_sql, insert_values)
            result = cur.fetchone()
            creator_db_id = result[0] if result else None
            conn.commit()
            creator_count += 1
            logger.info(f"Upserted creator: {db_creator.get('fullName')} (id={creator_db_id})")

            for post in creator.get("posts", []):
                db_post = _build_post_db_record(post, creator_db_id)

                p_insert_fields = [f'"{f}"' for f in POST_INSERT_FIELDS]
                p_insert_values = [db_post.get(f) for f in POST_INSERT_FIELDS]

                p_update_set = ", ".join(
                    f'"{f}" = EXCLUDED."{f}"' for f in POST_UPSERT_FIELDS
                )

                post_sql = f"""
                    INSERT INTO posts ({', '.join(p_insert_fields)})
                    VALUES ({', '.join(['%s'] * len(p_insert_fields))})
                    ON CONFLICT ("postUrl") DO UPDATE SET {p_update_set}
                """
                cur.execute(post_sql, p_insert_values)
                conn.commit()
                post_count += 1

            logger.info(f"  -> {len(creator.get('posts', []))} posts ingested")

        logger.info(f"Done. Upserted {creator_count} creators and {post_count} posts.")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise

    finally:
        if "cur" in locals():
            cur.close()
        if "conn" in locals():
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
