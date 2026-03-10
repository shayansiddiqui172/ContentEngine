import logging
import psycopg2
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import os

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger(__name__)


def main():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        # Basic counts
        cur.execute("SELECT COUNT(*) FROM creators")
        creators_count = cur.fetchone()[0]
        print(f"\nTotal creators: {creators_count}")

        cur.execute("SELECT COUNT(*) FROM posts")
        posts_count = cur.fetchone()[0]
        print(f"Total posts: {posts_count}")

        # Creators by follower count
        cur.execute("""
            SELECT "fullName", "followerCount", "watchStatus", "connectionStatus"
            FROM creators
            ORDER BY "followerCount" DESC NULLS LAST
        """)
        rows = cur.fetchall()
        print(f"\n{'Full Name':<25} {'Followers':<12} {'Watch':<15} {'Connection':<15}")
        print("-" * 67)
        for row in rows:
            name = row[0] or "N/A"
            followers = row[1] if row[1] is not None else "N/A"
            watch = row[2] or "N/A"
            conn_status = row[3] or "N/A"
            print(f"{name:<25} {str(followers):<12} {watch:<15} {conn_status:<15}")

        # Completeness check: count non-null fields per creator
        print("\n--- Completeness Check ---")
        cur.execute("""
            SELECT "fullName",
                (CASE WHEN "fullName" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "handle" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "location" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "firmOrCompany" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "bio" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "followerCount" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "contentNiche" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "voiceStyle" IS NOT NULL THEN 1 ELSE 0 END +
                 CASE WHEN "estimatedEngagementRate" IS NOT NULL THEN 1 ELSE 0 END
                ) as filled_fields
            FROM creators
            ORDER BY filled_fields ASC
        """)
        rows = cur.fetchall()
        print(f"{'Creator':<25} {'Filled (of 9 key fields)':<25}")
        print("-" * 50)
        for row in rows:
            print(f"{(row[0] or 'N/A'):<25} {row[1]}/9")

        # Staleness check: creators not updated in 30+ days
        print("\n--- Staleness Check ---")
        threshold = datetime.now(timezone.utc) - timedelta(days=30)
        cur.execute("""
            SELECT "fullName", "updatedAt"
            FROM creators
            WHERE "updatedAt" < %s
            ORDER BY "updatedAt" ASC
        """, (threshold,))
        stale = cur.fetchall()
        if stale:
            print(f"WARNING: {len(stale)} creator(s) not updated in 30+ days:")
            for row in stale:
                print(f"  - {row[0] or 'N/A'}: last updated {row[1]}")
        else:
            print("All creators updated within the last 30 days.")

        # Data quality: null names, placeholder URLs
        print("\n--- Data Quality ---")
        cur.execute('SELECT COUNT(*) FROM creators WHERE "fullName" IS NULL')
        null_names = cur.fetchone()[0]
        print(f"Creators with null name: {null_names}")

        cur.execute("""SELECT COUNT(*) FROM posts WHERE "postUrl" LIKE '%%/post_%%'""")
        placeholder_urls = cur.fetchone()[0]
        print(f"Posts with placeholder URLs: {placeholder_urls}")

        cur.execute('SELECT COUNT(*) FROM posts WHERE "primaryTopic" IS NOT NULL')
        enriched_posts = cur.fetchone()[0]
        print(f"Posts with topic enrichment: {enriched_posts}/{posts_count}")

        # Posts per creator
        print("\n--- Posts per Creator ---")
        cur.execute("""
            SELECT c."fullName", COUNT(p.id) as post_count,
                   ROUND(AVG(p."engagementRate")::numeric, 4) as avg_engagement
            FROM creators c
            LEFT JOIN posts p ON c.id = p."creatorId"
            GROUP BY c.id, c."fullName"
            ORDER BY post_count DESC
        """)
        rows = cur.fetchall()
        print(f"{'Creator':<25} {'Posts':<8} {'Avg Engagement':<15}")
        print("-" * 48)
        for row in rows:
            print(f"{(row[0] or 'N/A'):<25} {row[1]:<8} {row[2] or 'N/A'}")

    except Exception as e:
        print(f"Error during validation: {e}")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
