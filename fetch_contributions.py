#!/usr/bin/env python3
"""Fetch the last year of contribution counts into data/contributions.json.

Uses the GitHub GraphQL API. Needs a token in GH_TOKEN (the Action's built-in
GITHUB_TOKEN works for public contributions). Username comes from GH_USER or
the first CLI argument.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("GH_USER") or (sys.argv[1] if len(sys.argv) > 1 else "Vedant180205")
TOKEN = os.environ["GH_TOKEN"]
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

now = dt.datetime.now(dt.timezone.utc)
payload = {
    "query": QUERY,
    "variables": {
        "login": USER,
        "from": (now - dt.timedelta(days=371)).isoformat(),
        "to": now.isoformat(),
    },
}
req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode(),
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": "readme-cards"},
)
with urllib.request.urlopen(req, timeout=30) as r:
    res = json.load(r)

if "errors" in res or not res.get("data", {}).get("user"):
    sys.exit(f"GraphQL error: {res.get('errors') or 'user not found'}")

cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = [
    {"date": d["date"], "count": d["contributionCount"]}
    for w in cal["weeks"]
    for d in w["contributionDays"]
]
days.sort(key=lambda d: d["date"])
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"username": USER, "total": cal["totalContributions"], "days": days}, indent=0))
print(f"wrote {OUT} ({len(days)} days, {cal['totalContributions']} contributions)")
