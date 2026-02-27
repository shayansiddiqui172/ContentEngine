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

        # Query 1: Count creators
        cur.execute("SELECT COUNT(*) FROM creators")
        creators_count = cur.fetchone()[0]
        print(f"Total creators: {creators_count}")

        # Query 2: Count posts
        cur.execute("SELECT COUNT(*) FROM posts")
        posts_count = cur.fetchone()[0]
        print(f"Total posts: {posts_count}")

        # Query 3: List creators by follower count
        cur.execute("""
            SELECT "fullName", "followerCount", "watchStatus"
            FROM creators
            ORDER BY "followerCount" DESC
        """)
        rows = cur.fetchall()
        print("\nCreators by follower count:")
        print("{:<20} {:<15} {:<15}".format("Full Name", "Follower Count", "Watch Status"))
        for row in rows:
            print("{:<20} {:<15} {:<15}".format(row[0], row[1], row[2]))

    except Exception as e:
        print(f"❌ Error during validation: {e}")

    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()