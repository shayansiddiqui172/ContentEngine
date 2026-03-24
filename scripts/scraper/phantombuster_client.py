import csv
import io
import json
import logging
import time
import requests
from scripts.scraper.config import (
    PHANTOMBUSTER_API_KEY,
    PHANTOMBUSTER_PROFILE_AGENT_ID,
    PHANTOMBUSTER_ACTIVITY_AGENT_ID,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://api.phantombuster.com/api/v2"
HEADERS = {"X-Phantombuster-Key": PHANTOMBUSTER_API_KEY}


def _launch_agent(agent_id: str, linkedin_url: str) -> str:
    """Launch a PhantomBuster agent and return the container ID."""
    # Fetch existing saved argument so we preserve the session cookie
    fetch_resp = requests.get(
        f"{BASE_URL}/agents/fetch",
        headers=HEADERS,
        params={"id": agent_id},
        timeout=30,
    )
    fetch_resp.raise_for_status()
    saved_arg = json.loads(fetch_resp.json().get("argument") or "{}")
    saved_arg["spreadsheetUrl"] = linkedin_url

    resp = requests.post(
        f"{BASE_URL}/agents/launch",
        headers=HEADERS,
        json={"id": agent_id, "argument": saved_arg},
        timeout=30,
    )
    resp.raise_for_status()
    container_id = resp.json()["containerId"]
    logger.info(f"Launched agent {agent_id}, container {container_id}")
    return container_id


def _wait_for_completion(agent_id: str, container_id: str, timeout: int = 300) -> dict:
    """Poll until agent finishes, return final output."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(5)
        resp = requests.get(
            f"{BASE_URL}/containers/fetch",
            headers=HEADERS,
            params={"id": container_id},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        logger.info(f"Agent {agent_id} container {container_id} status: {status}")
        if status in ("finished", "error", "stopped"):
            return data
    raise TimeoutError(f"Agent {agent_id} did not finish within {timeout}s")


def _fetch_result_csv(agent_id: str) -> list[dict]:
    """Fetch the latest result CSV from an agent's S3 bucket."""
    agent_resp = requests.get(
        f"{BASE_URL}/agents/fetch",
        headers=HEADERS,
        params={"id": agent_id},
        timeout=30,
    )
    agent_resp.raise_for_status()
    agent = agent_resp.json()
    org_folder = agent["orgS3Folder"]
    s3_folder = agent["s3Folder"]

    csv_url = f"https://phantombuster.s3.amazonaws.com/{org_folder}/{s3_folder}/result.csv"
    logger.info(f"Downloading results from {csv_url}")
    csv_resp = requests.get(csv_url, timeout=30)
    csv_resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(csv_resp.text))
    rows = [r for r in reader if any(r.values())]
    logger.info(f"Fetched {len(rows)} rows from agent {agent_id}")
    return rows


def run_profile_scraper(linkedin_url: str) -> list[dict]:
    """Launch profile scraper phantom and return results."""
    container_id = _launch_agent(PHANTOMBUSTER_PROFILE_AGENT_ID, linkedin_url)
    _wait_for_completion(PHANTOMBUSTER_PROFILE_AGENT_ID, container_id)
    return _fetch_result_csv(PHANTOMBUSTER_PROFILE_AGENT_ID)


def run_activity_extractor(linkedin_url: str) -> list[dict]:
    """Launch activity extractor phantom and return results."""
    container_id = _launch_agent(PHANTOMBUSTER_ACTIVITY_AGENT_ID, linkedin_url)
    _wait_for_completion(PHANTOMBUSTER_ACTIVITY_AGENT_ID, container_id)
    return _fetch_result_csv(PHANTOMBUSTER_ACTIVITY_AGENT_ID)


def group_posts_by_profile(posts: list[dict]) -> dict[str, list[dict]]:
    """Group posts by profileUrl (normalized)."""
    grouped: dict[str, list[dict]] = {}
    for post in posts:
        url = (post.get("profileUrl") or "").rstrip("/").lower()
        if url:
            grouped.setdefault(url, []).append(post)
    return grouped
