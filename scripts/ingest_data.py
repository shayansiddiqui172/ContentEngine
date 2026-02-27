import json
import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Read creators and posts from JSON
        with open("data/raw_creators.json", "r") as f:
            creators = json.load(f)

        creator_count = 0
        post_count = 0

        for creator in creators:
            # Column names quoted to preserve camelCase in Postgres
            creator_fields = [
                '"id"', '"fullName"', '"linkedinUrl"', '"handle"', '"location"', '"firmOrCompany"', '"bio"',
                '"primaryRole"', '"contentNiche"', '"stageFocus"', '"geographyFocus"', '"tags"',
                '"followerCount"', '"followerCountUpdatedAt"', '"estimatedEngagementRate"',
                '"hasTwitter"', '"twitterUrl"', '"hasSubstack"', '"substackUrl"', '"hasYoutube"',
                '"youtubeUrl"', '"hasPodcast"', '"podcastUrl"', '"voiceStyle"', '"credibilityScore"',
                '"relevanceScore"', '"collaborationPotential"', '"collaborationNotes"', '"watchStatus"',
                '"connectionStatus"', '"hasInteractedWithContent"', '"hasDMedOrMet"',
                '"relationshipNotes"', '"addedBy"', '"source"', '"createdAt"', '"updatedAt"'
            ]

            # JSON keys match camelCase exactly so we strip quotes to get the key
            creator_json_keys = [f.strip('"') for f in creator_fields]
            creator_values = [creator.get(k) for k in creator_json_keys]

            insert_creator_sql = f"""
                INSERT INTO creators ({', '.join(creator_fields)})
                VALUES ({', '.join(['%s'] * len(creator_fields))})
                ON CONFLICT ("linkedinUrl") DO NOTHING
            """
            cur.execute(insert_creator_sql, creator_values)
            conn.commit()
            creator_count += 1
            print(f"✅ Ingested creator: {creator['fullName']} ({creator.get('followerCount', 0)} followers)")

            # Insert posts for this creator
            for post in creator["posts"]:
                post_fields = [
                    '"id"', '"creatorId"', '"postUrl"', '"publishedAt"', '"capturedAt"', '"format"',
                    '"primaryTopic"', '"secondaryTopics"', '"containsData"', '"containsCTA"', '"ctaType"',
                    '"isOriginal"', '"reactions"', '"comments"', '"reposts"', '"estimatedImpressions"',
                    '"engagementRate"', '"viralFlag"', '"hookStrength"', '"angle"', '"keyInsight"',
                    '"relevanceToStrategy"', '"swipeFileFlag"', '"notes"'
                ]

                post_json_keys = [f.strip('"') for f in post_fields]
                post_values = []
                for key in post_json_keys:
                    value = post.get(key)
                    if key == "secondaryTopics":
                        value = value if value is not None else []
                    post_values.append(value)

                insert_post_sql = f"""
                    INSERT INTO posts ({', '.join(post_fields)})
                    VALUES ({', '.join(['%s'] * len(post_fields))})
                    ON CONFLICT ("postUrl") DO NOTHING
                """
                cur.execute(insert_post_sql, post_values)
                conn.commit()
                post_count += 1
                print(f"✅ Ingested post: {post['postUrl']} — Viral: {post.get('viralFlag', False)}")

        print(f"\n🎉 Done. Ingested {creator_count} creators and {post_count} posts into PostgreSQL.")

    except Exception as e:
        print(f"❌ Error during ingestion: {e}")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()