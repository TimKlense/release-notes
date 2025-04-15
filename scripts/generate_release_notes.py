import os
import argparse
import logging
from datetime import datetime, timedelta
import requests

logging.basicConfig(level=logging.INFO)

GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise EnvironmentError("Missing GITHUB_TOKEN in environment.")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_merged_prs(repo, since):
    url = f"{GITHUB_API}/repos/{repo}/pulls?state=closed&sort=updated&direction=desc"
    prs = []
    page = 1

    logging.info(f"Fetching merged PRs for {repo} since {since}...")
    while True:
        resp = requests.get(f"{url}&per_page=100&page={page}", headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()

        if not data:
            break

        for pr in data:
            if pr.get("merged_at") and pr["merged_at"] > since:
                prs.append(pr)

        page += 1

    logging.info(f"Found {len(prs)} merged PRs.")
    return prs


def generate_notes(prs):
    notes = ["## 📝 Release Notes", ""]
    for pr in prs:
        notes.append(f"- {pr['title']} ([#{pr['number']}]({pr['html_url']}))")
    return "\n".join(notes)


def create_release(repo, tag_name, notes):
    logging.info(f"Creating release {tag_name} on {repo}...")
    url = f"{GITHUB_API}/repos/{repo}/releases"
    data = {
        "tag_name": tag_name,
        "name": f"Release {tag_name}",
        "body": notes,
        "draft": False,
        "prerelease": False,
    }
    resp = requests.post(url, headers=HEADERS, json=data)
    resp.raise_for_status()
    logging.info("✅ Release created!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    since = (datetime.utcnow() - timedelta(days=args.days)).isoformat()
    prs = get_merged_prs(args.repo, since)

    if not prs:
        logging.info("No PRs merged in the given timeframe.")
        return

    notes = generate_notes(prs)

    if args.dry_run:
        print("🧪 Dry run output:\n")
        print(notes)
        return

    # Generate a tag like YYYYMMDD-HHMM
    tag = datetime.utcnow().strftime("%Y%m%d-%H%M")
    create_release(args.repo, tag, notes)


if __name__ == "__main__":
    main()
