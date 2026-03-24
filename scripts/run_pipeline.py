#!/usr/bin/env python3
"""ContentEngine LinkedIn scraping pipeline.

Usage:
    python -m scripts.run_pipeline --profile https://www.linkedin.com/in/williamhgates [--skip-enrich] [--dry-run]
    python -m scripts.run_pipeline --all [--skip-enrich] [--dry-run]

Profiles for --all are listed in data/profiles.txt (one LinkedIn URL per line).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

from scripts.scraper.config import (
    GEMINI_API_KEY,
    ENRICHED_OUTPUT_PATH,
    PHANTOMBUSTER_API_KEY,
    follower_count_range,
)
from scripts.scraper.phantombuster_client import (
    run_profile_scraper,
    run_activity_extractor,
    group_posts_by_profile,
)
from scripts.scraper.profile_scraper import map_profile_to_creator
from scripts.scraper.post_scraper import map_posts_to_schema
from scripts.scraper.enrichment import run_enrichment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROFILES_LIST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "profiles.txt"
)


def _compute_posting_frequency(posts: list[dict]) -> str | None:
    """Bucket posting cadence from post publish dates."""
    if not posts:
        return None
    dates = []
    for p in posts:
        pub = p.get("publishedAt")
        if pub:
            try:
                dt = datetime.fromisoformat(str(pub).replace("Z", "+00:00"))
                dates.append(dt)
            except (ValueError, TypeError):
                pass
    if len(dates) < 2:
        return None
    dates.sort()
    span_days = (dates[-1] - dates[0]).days
    if span_days == 0:
        return None
    rate = len(dates) / span_days
    if rate >= 0.85:
        return "Daily"
    if rate >= 0.4:
        return "3-4/week"
    if rate >= 0.14:
        return "1-2/week"
    return "< a month"


def _enrich_computed_fields(creator: dict):
    """Compute derived fields that depend on post data being present."""
    follower_count = creator.get("followerCount")
    posts = creator.get("posts", [])

    # Follower count range (in case it wasn't set in profile_scraper)
    if not creator.get("followerCountRange"):
        creator["followerCountRange"] = follower_count_range(follower_count)

    # Growth stage
    if not creator.get("growthStage") and follower_count is not None:
        creator["growthStage"] = (
            "Established Creator" if follower_count >= 50_000 else "Emerging Creator"
        )

    # Posting frequency
    if not creator.get("postingFrequency"):
        creator["postingFrequency"] = _compute_posting_frequency(posts)

    # Cross-platform presence count (PhantomBuster doesn't give us this,
    # so it stays 0 unless manually updated)
    if creator.get("crossPlatformCount") is None:
        creator["crossPlatformCount"] = 0


def scrape_creator(linkedin_url: str, max_posts: int | None = None) -> dict | None:
    """Scrape a single creator via PhantomBuster and map to schema."""
    profiles = run_profile_scraper(linkedin_url)
    if not profiles:
        logger.error(f"No profile data returned for: {linkedin_url}")
        return None

    creator = map_profile_to_creator(profiles[0])

    posts_raw = run_activity_extractor(linkedin_url)
    posts_by_profile = group_posts_by_profile(posts_raw)
    profile_key = linkedin_url.rstrip("/").lower()
    raw_posts = posts_by_profile.get(profile_key, posts_raw)
    if max_posts:
        raw_posts = raw_posts[:max_posts]
    posts = map_posts_to_schema(raw_posts, creator["linkedinUrl"], creator.get("followerCount"))
    creator["posts"] = posts

    logger.info(
        f"Scraped {creator['name']}: {creator.get('followerCount', 'N/A')} followers, "
        f"{len(posts)} posts"
    )
    return creator


def load_profile_list() -> list[str]:
    """Load LinkedIn URLs from data/profiles.txt."""
    if not os.path.exists(PROFILES_LIST_PATH):
        raise FileNotFoundError(f"Profile list not found: {PROFILES_LIST_PATH}")
    with open(PROFILES_LIST_PATH) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


def save_json(creators: list[dict], path: str):
    output = []
    for creator in creators:
        c = dict(creator)
        # Strip internal-only fields from posts before saving
        c["posts"] = [
            {k: v for k, v in post.items() if not k.startswith("_")}
            for post in creator.get("posts", [])
        ]
        output.append(c)
    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Saved {len(output)} creators to {path}")


def main():
    parser = argparse.ArgumentParser(description="ContentEngine LinkedIn pipeline")
    parser.add_argument("--profile", type=str, help="Scrape a single LinkedIn profile URL")
    parser.add_argument("--all", action="store_true", help="Scrape all profiles from data/profiles.txt")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip Gemini enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Skip DB ingestion (spreadsheet still written)")
    parser.add_argument("--max-posts", type=int, default=None, help="Limit posts per creator (e.g. 3 for a quick demo)")
    args = parser.parse_args()

    if not PHANTOMBUSTER_API_KEY:
        logger.error("PHANTOMBUSTER_API_KEY not set in .env")
        sys.exit(1)
    if not args.skip_enrich and not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set in .env or use --skip-enrich")
        sys.exit(1)

    if args.profile:
        urls = [args.profile]
    elif args.all:
        urls = load_profile_list()
    else:
        logger.error("Specify --profile URL or --all")
        parser.print_help()
        sys.exit(1)

    logger.info(f"Pipeline starting for {len(urls)} profile(s)")

    # ── Phase 1: Scrape ────────────────────────────────────────────────────────
    creators = []
    for url in urls:
        creator = scrape_creator(url, max_posts=args.max_posts)
        if creator:
            creators.append(creator)

    if not creators:
        logger.error("No creators scraped successfully. Exiting.")
        sys.exit(1)

    logger.info(
        f"Scraped {len(creators)} creators, "
        f"{sum(len(c['posts']) for c in creators)} total posts"
    )

    # ── Phase 2: AI Enrichment ─────────────────────────────────────────────────
    creators = run_enrichment(creators, skip=args.skip_enrich)

    # ── Phase 3: Computed / derived fields ────────────────────────────────────
    for creator in creators:
        _enrich_computed_fields(creator)

    # ── Phase 4: Save JSON ─────────────────────────────────────────────────────
    save_json(creators, ENRICHED_OUTPUT_PATH)

    # ── Phase 5: Write Excel spreadsheets ─────────────────────────────────────
    logger.info("Writing spreadsheets...")
    from scripts.write_spreadsheets import write_spreadsheets
    write_spreadsheets(creators)

    # ── Phase 6: Ingest to DB ──────────────────────────────────────────────────
    if args.dry_run:
        logger.info("Dry run — skipping DB ingestion")
    else:
        logger.info("Ingesting to database...")
        from scripts.ingest_data import main as ingest_main
        ingest_main()
        logger.info("Running validation...")
        from scripts.validate_data import main as validate_main
        validate_main()

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
