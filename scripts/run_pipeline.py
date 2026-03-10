#!/usr/bin/env python3
"""ContentEngine LinkedIn scraping pipeline.

Usage:
    python -m scripts.run_pipeline [--profile URL] [--all] [--skip-enrich] [--dry-run]
"""

import argparse
import json
import logging
import sys

from scripts.scraper.config import (
    PROXYCURL_API_KEY,
    GEMINI_API_KEY,
    ENRICHED_OUTPUT_PATH,
    load_target_profiles,
)
from scripts.scraper.proxycurl_client import get_profile, get_profile_posts
from scripts.scraper.profile_scraper import map_profile_to_creator
from scripts.scraper.post_scraper import map_posts_to_schema
from scripts.scraper.enrichment import run_enrichment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def scrape_creator(linkedin_url: str) -> dict | None:
    """Scrape a single creator's profile and posts."""
    profile = get_profile(linkedin_url)
    if not profile:
        logger.error(f"Failed to fetch profile: {linkedin_url}")
        return None

    creator = map_profile_to_creator(profile, linkedin_url)

    raw_posts = get_profile_posts(linkedin_url)
    # Use linkedinUrl as temporary creatorId placeholder; ingest will resolve
    posts = map_posts_to_schema(raw_posts, creator["linkedinUrl"], creator.get("followerCount"))
    creator["posts"] = posts

    logger.info(
        f"Scraped {creator['fullName']}: {creator.get('followerCount', 'N/A')} followers, "
        f"{len(posts)} posts"
    )
    return creator


def save_json(creators: list[dict], path: str):
    """Save creators to JSON, stripping internal fields."""
    output = []
    for creator in creators:
        c = {k: v for k, v in creator.items()}
        c["posts"] = []
        for post in creator.get("posts", []):
            p = {k: v for k, v in post.items() if not k.startswith("_")}
            c["posts"].append(p)
        output.append(c)

    with open(path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    logger.info(f"Saved {len(output)} creators to {path}")


def run_ingest():
    """Run the ingest_data script."""
    from scripts.ingest_data import main as ingest_main
    ingest_main()


def run_validation():
    """Run the validate_data script."""
    from scripts.validate_data import main as validate_main
    validate_main()


def main():
    parser = argparse.ArgumentParser(description="ContentEngine LinkedIn scraping pipeline")
    parser.add_argument("--profile", type=str, help="Scrape a single LinkedIn profile URL")
    parser.add_argument("--all", action="store_true", help="Scrape all profiles from target_profiles.json")
    parser.add_argument("--skip-enrich", action="store_true", help="Skip Gemini LLM enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Scrape and enrich but don't ingest to DB")
    args = parser.parse_args()

    # Validate API keys
    if not PROXYCURL_API_KEY:
        logger.error("PROXYCURL_API_KEY not set. Add it to .env")
        sys.exit(1)
    if not args.skip_enrich and not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set. Add it to .env or use --skip-enrich")
        sys.exit(1)

    # Determine which profiles to scrape
    if args.profile:
        urls = [args.profile]
    elif args.all:
        urls = load_target_profiles()
    else:
        logger.error("Specify --profile URL or --all")
        parser.print_help()
        sys.exit(1)

    logger.info(f"Pipeline starting for {len(urls)} profile(s)")

    # Phase 1: Scrape
    creators = []
    for url in urls:
        creator = scrape_creator(url)
        if creator:
            creators.append(creator)

    if not creators:
        logger.error("No creators scraped successfully. Exiting.")
        sys.exit(1)

    logger.info(f"Scraped {len(creators)} creators, {sum(len(c['posts']) for c in creators)} total posts")

    # Phase 2: Enrich
    creators = run_enrichment(creators, skip=args.skip_enrich)

    # Phase 3: Save JSON
    save_json(creators, ENRICHED_OUTPUT_PATH)

    # Phase 4: Ingest to DB
    if args.dry_run:
        logger.info("Dry run — skipping DB ingestion")
    else:
        logger.info("Ingesting to database...")
        run_ingest()

    # Phase 5: Validate
    if not args.dry_run:
        logger.info("Running validation...")
        run_validation()

    logger.info("Pipeline complete.")


if __name__ == "__main__":
    main()
