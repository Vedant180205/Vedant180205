#!/usr/bin/env python3
"""Fetch the last year of contribution counts into data/contributions.json.

Uses the GitHub GraphQL API. Authenticates using GITHUB_TOKEN or GH_TOKEN.
Falls back safely to public API if needed, validating all returned data.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER") or (sys.argv[1] if len(sys.argv) > 1 else "Vedant180205")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
OUT = Path(__file__).resolve().parent.parent / "data" / "contributions.json"

QUERY = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from,to:$to){
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}"""


def fetch_graphql(user, token):
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "query": QUERY,
        "variables": {
            "login": user,
            "from": (now - dt.timedelta(days=371)).isoformat(),
            "to": now.isoformat(),
        },
    }
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"readme-cards-{user}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)

    if "errors" in res or not res.get("data", {}).get("user"):
        err = res.get("errors") or "User not found"
        raise RuntimeError(f"GraphQL API error: {err}")

    cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        {"date": d["date"], "count": d["contributionCount"]}
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]
    days.sort(key=lambda d: d["date"])
    return cal["totalContributions"], days


def fetch_fallback(user):
    url = f"https://github-contributions-api.jogruber.de/v4/{user}?y=last"
    req = urllib.request.Request(url, headers={"User-Agent": f"readme-cards-{user}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)

    raw_days = res.get("contributions", [])
    if not raw_days:
        raise RuntimeError("No contributions returned from fallback API")

    days = [{"date": d["date"], "count": d["count"]} for d in raw_days]
    days.sort(key=lambda d: d["date"])
    total = res.get("total", {}).get("lastYear", sum(d["count"] for d in days))
    return total, days


def main():
    print(f"Fetching contribution calendar for user: {USER}")
    total = None
    days = None

    if TOKEN:
        try:
            print("Attempting GitHub GraphQL API...")
            total, days = fetch_graphql(USER, TOKEN)
            print("Successfully fetched via GitHub GraphQL API.")
        except Exception as e:
            print(f"GraphQL request failed: {e}")
            print("Trying public fallback...")

    if not days:
        try:
            total, days = fetch_fallback(USER)
            print("Successfully fetched via fallback service.")
        except Exception as e:
            if OUT.exists():
                print(f"Fetch failed ({e}), but existing {OUT} will be preserved.")
                return
            sys.exit(f"Fatal: Unable to fetch contributions: {e}")

    # Validate data integrity
    if not isinstance(days, list) or len(days) < 300:
        sys.exit(f"Fatal: Invalid contribution data length: {len(days) if days else 0}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {"username": USER, "total": total, "days": days}
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(days)} days, {total} total contributions)")


if __name__ == "__main__":
    main()
