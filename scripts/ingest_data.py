import json
import logging
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger(__name__)

# Fields that should be updated on conflict (excluding id, createdAt, linkedinUrl)
CREATOR_UPSERT_FIELDS = [
    "fullName", "handle", "location", "firmOrCompany", "bio",
    "primaryRole", "contentNiche", "stageFocus", "geographyFocus", "tags",
    "followerCount", "followerCountUpdatedAt", "estimatedEngagementRate",
    "hasTwitter", "twitterUrl", "hasSubstack", "substackUrl", "hasYoutube",
    "youtubeUrl", "hasPodcast", "podcastUrl", "voiceStyle", "credibilityScore",
    "relevanceScore", "collaborationPotential", "collaborationNotes", "watchStatus",
    "connectionStatus", "hasInteractedWithContent", "hasDMedOrMet",
    "relationshipNotes", "addedBy", "source", "updatedAt",
]

POST_UPSERT_FIELDS = [
    "creatorId", "publishedAt", "capturedAt", "format",
    "primaryTopic", "secondaryTopics", "containsData", "containsCTA", "ctaType",
    "isOriginal", "reactions", "comments", "reposts", "estimatedImpressions",
    "engagementRate", "viralFlag", "hookStrength", "angle", "keyInsight",
    "relevanceToStrategy", "swipeFileFlag", "notes",
]

# All fields for INSERT (includes id/unique fields)
CREATOR_INSERT_FIELDS = ["fullName", "linkedinUrl"] + [
    f for f in CREATOR_UPSERT_FIELDS if f not in ("fullName", "updatedAt")
]

POST_INSERT_FIELDS = ["postUrl"] + POST_UPSERT_FIELDS


def _get_value(record: dict, key: str):
    """Get a value from a record, handling special types."""
    value = record.get(key)
    if key == "tags" or key == "secondaryTopics":
        return value if value is not None else []
    return value


def main():
    # Determine which JSON file to read
    enriched_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "enriched_creators.json")
    raw_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw_creators.json")

    data_path = enriched_path if os.path.exists(enriched_path) else raw_path
    logger.info(f"Reading from {data_path}")

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        with open(data_path, "r") as f:
            creators = json.load(f)

        creator_count = 0
        post_count = 0

        for creator in creators:
            # Build INSERT fields list
            insert_fields = [f'"{f}"' for f in CREATOR_INSERT_FIELDS]
            insert_values = [_get_value(creator, f) for f in CREATOR_INSERT_FIELDS]

            # Build UPDATE SET clause (exclude unique/id fields)
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
            logger.info(f"Upserted creator: {creator.get('fullName')} (id={creator_db_id})")

            # Insert posts
            for post in creator.get("posts", []):
                # Set creatorId to the DB-generated ID
                post["creatorId"] = creator_db_id

                p_insert_fields = [f'"{f}"' for f in POST_INSERT_FIELDS]
                p_insert_values = [_get_value(post, f) for f in POST_INSERT_FIELDS]

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
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    main()
