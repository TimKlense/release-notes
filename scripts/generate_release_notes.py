import os
import argparse
import logging
from datetime import datetime, timedelta
import requests
from typing import List

logging.basicConfig(level=logging.INFO)

GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN not set in environment.")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def fetch_merged_prs(repo: str, since: str) -> List[dict]:
    url = f"{GITHUB_API_URL}/repos/{repo}/pulls?state=closed&sort=updated&direction=desc"
    prs = []
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        for pr in response.json():
            if pr.get("merged_at") and pr["merged_at"] > since:
                prs.append(pr)
    except requests.RequestException as e:
        logging.error(f"Error fetching PRs: {e}")
    return prs


def generate_notes(prs: List[dict]) -> str:
    notes = ["## 📝 Release Notes", ""]
    for pr in prs:
        notes.append(f"- {pr['title']} ([#{pr['number']}]({pr['html_url']}))")
    return "\n".join(notes)


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub release notes.")
    parser.add_argument("--repo", required=True, help="GitHub repo in 'owner/repo' format")
    parser.add_argument("--branch", required=False, default="main", help="Branch to base release from")
    parser.add_argument("--days", type=int, default=1, help="How many days back to look for merged PRs")
    parser.add_argument("--dry-run", action="store_true", help="Don't publish the release, just print")
    args = parser.parse_args()

    since = (datetime.utcnow() - timedelta(days=args.days)).isoformat()
    prs = fetch_merged_prs(args.repo, since)

    if not prs:
        logging.info("No PRs found.")
        return

    notes = generate_notes(prs)

    if args.dry_run:
        print(notes)
    else:
        # Create a release (you can expand this to add tag logic, etc.)
        logging.info("Creating release...")
        # implement GitHub release POST logic here

if __name__ == "__main__":
    main()
