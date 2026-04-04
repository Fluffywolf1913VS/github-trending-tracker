#!/usr/bin/env python3
"""
Fetch the 10 fastest-growing GitHub repositories of the week from GitHub Trending.

Usage:
    python github_fastest_growing.py
    python github_fastest_growing.py --language python
    python github_fastest_growing.py --limit 10 --json out.json --csv out.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://github.com/trending"
USER_AGENT = "github-trending-weekly-fetcher/1.0"


@dataclass
class Repo:
    rank: int
    owner: str
    name: str
    url: str
    description: str
    language: str
    stars_total: Optional[int]
    forks: Optional[int]
    stars_this_week: Optional[int]


def parse_count(text: str) -> Optional[int]:
    text = (text or "").strip().replace(",", "")
    if not text:
        return None

    match = re.fullmatch(r"(\d+(?:\.\d+)?)([kKmM]?)", text)
    if not match:
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    value = float(match.group(1))
    suffix = match.group(2).lower()
    multiplier = 1
    if suffix == "k":
        multiplier = 1_000
    elif suffix == "m":
        multiplier = 1_000_000
    return int(value * multiplier)


def fetch_trending(language: Optional[str] = None, limit: int = 10) -> List[Repo]:
    params = {"since": "weekly"}
    if language:
        url = f"{BASE_URL}/{language}?{urlencode(params)}"
    else:
        url = f"{BASE_URL}?{urlencode(params)}"

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.Box-row")

    repos: List[Repo] = []
    for idx, article in enumerate(articles[:limit], start=1):
        header_link = article.select_one("h2 a")
        if not header_link:
            continue

        repo_path = header_link.get("href", "").strip()
        repo_path = repo_path if repo_path.startswith("/") else f"/{repo_path}"
        full_name = repo_path.strip("/")

        if "/" not in full_name:
            continue

        owner, name = full_name.split("/", 1)

        description_el = article.select_one("p")
        description = description_el.get_text(" ", strip=True) if description_el else ""

        language_el = article.select_one('[itemprop="programmingLanguage"]')
        language_name = language_el.get_text(" ", strip=True) if language_el else ""

        stars_total = None
        forks = None
        stars_this_week = None

        links = article.select("a.Link--muted")
        if len(links) >= 1:
            stars_total = parse_count(links[0].get_text(" ", strip=True))
        if len(links) >= 2:
            forks = parse_count(links[1].get_text(" ", strip=True))

        for span in article.select("span.d-inline-block.float-sm-right"):
            text = span.get_text(" ", strip=True)
            if "stars" in text.lower():
                stars_this_week = parse_count(text)
                break

        repos.append(
            Repo(
                rank=idx,
                owner=owner,
                name=name,
                url=f"https://github.com/{full_name}",
                description=description,
                language=language_name,
                stars_total=stars_total,
                forks=forks,
                stars_this_week=stars_this_week,
            )
        )

    return repos


def save_json(repos: List[Repo], path: Path) -> None:
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(repos),
        "repositories": [asdict(repo) for repo in repos],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def save_csv(repos: List[Repo], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "rank",
                "owner",
                "name",
                "url",
                "description",
                "language",
                "stars_total",
                "forks",
                "stars_this_week",
            ],
        )
        writer.writeheader()
        for repo in repos:
            writer.writerow(asdict(repo))


def print_table(repos: List[Repo]) -> None:
    print("\nTop fastest-growing GitHub repos this week\n")
    print(f"{'Rank':<5} {'Repository':<35} {'Weekly stars':>12} {'Total stars':>12} {'Language':<15}")
    print("-" * 88)
    for repo in repos:
        repo_name = f"{repo.owner}/{repo.name}"
        print(
            f"{repo.rank:<5} {repo_name:<35} "
            f"{str(repo.stars_this_week or ''):>12} {str(repo.stars_total or ''):>12} "
            f"{repo.language[:15]:<15}"
        )
    print("")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", help="Optional language filter, e.g. python, javascript, go")
    parser.add_argument("--limit", type=int, default=10, help="How many repositories to return")
    parser.add_argument("--json", default="trending_weekly.json", help="Path to JSON output")
    parser.add_argument("--csv", default="trending_weekly.csv", help="Path to CSV output")
    args = parser.parse_args()

    try:
        repos = fetch_trending(language=args.language, limit=args.limit)
    except requests.HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1

    if not repos:
        print("No repositories found. GitHub may have changed the Trending page markup.", file=sys.stderr)
        return 2

    print_table(repos)

    save_json(repos, Path(args.json))
    save_csv(repos, Path(args.csv))

    print(f"Saved JSON -> {args.json}")
    print(f"Saved CSV  -> {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
