#!/usr/bin/env python3
"""Run the pipeline from local PhantomBuster CSV exports.

Usage:
    python3 -m scripts.run_from_csv
    python3 -m scripts.run_from_csv --max-posts 3 --skip-enrich
"""

import argparse
import csv
import logging
import os
import sys

from scripts.scraper.config import GEMINI_API_KEY, ENRICHED_OUTPUT_PATH
from scripts.scraper.profile_scraper import map_profile_to_creator
from scripts.scraper.post_scraper import map_posts_to_schema
from scripts.scraper.enrichment import run_enrichment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_CSV = os.path.join(PROJECT_ROOT, "PB", "profileres.csv")
POSTS_CSV = os.path.join(PROJECT_ROOT, "PB", "postres.csv")


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if any(row.values())]


def main():
    parser = argparse.ArgumentParser(description="ContentEngine pipeline from local CSVs")
    parser.add_argument("--max-posts", type=int, default=None, help="Limit posts per creator")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip Gemini enrichment")
    args = parser.parse_args()

    if not args.skip_enrich and not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in .env — use --skip-enrich to bypass")
        sys.exit(1)

    # ── Load CSVs ──────────────────────────────────────────────────────────────
    logger.info(f"Reading profile from {PROFILE_CSV}")
    profiles = read_csv(PROFILE_CSV)
    if not profiles:
        logger.error("profileres.csv is empty")
        sys.exit(1)

    logger.info(f"Reading posts from {POSTS_CSV}")
    all_posts = read_csv(POSTS_CSV)
    logger.info(f"Loaded {len(profiles)} profile row(s), {len(all_posts)} post row(s)")

    # ── Map each profile row to a creator ──────────────────────────────────────
    creators = []
    for profile_row in profiles:
        creator = map_profile_to_creator(profile_row)
        linkedin_url = creator["linkedinUrl"].rstrip("/").lower()

        # Filter posts belonging to this creator
        creator_posts = [
            p for p in all_posts
            if (p.get("profileUrl") or "").rstrip("/").lower() == linkedin_url
        ]
        # Fallback: use all posts if no URL match (single-profile export)
        if not creator_posts:
            creator_posts = all_posts

        if args.max_posts:
            creator_posts = creator_posts[:args.max_posts]

        posts = map_posts_to_schema(creator_posts, creator["linkedinUrl"], creator.get("followerCount"))
        creator["posts"] = posts
        creators.append(creator)
        logger.info(f"Mapped {creator['name']}: {creator.get('followerCount', 'N/A')} followers, {len(posts)} posts")

    # ── Compute derived fields ─────────────────────────────────────────────────
    from scripts.run_pipeline import _enrich_computed_fields
    for creator in creators:
        _enrich_computed_fields(creator)

    # ── Gemini enrichment ──────────────────────────────────────────────────────
    creators = run_enrichment(creators, skip=args.skip_enrich)

    # ── Save JSON ──────────────────────────────────────────────────────────────
    from scripts.run_pipeline import save_json
    save_json(creators, ENRICHED_OUTPUT_PATH)

    # ── Write spreadsheets ─────────────────────────────────────────────────────
    logger.info("Writing spreadsheets...")
    from scripts.write_spreadsheets import write_spreadsheets
    write_spreadsheets(creators)

    logger.info("Done. Check data/DB1_Creator_Profiles.xlsx and data/DB2_Post_Analysis.xlsx")


if __name__ == "__main__":
    main()
