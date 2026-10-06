"""
Fetch the LeetCode submission calendar from the public GraphQL endpoint.

No token: userCalendar is public profile data. With no `year` argument it
returns the past twelve months, which lines up with GitHub's calendar.

    python scripts/fetch_leetcode.py [username]

Writes data/leetcode.json. LeetCode sits behind Cloudflare and sometimes
refuses CI runners; on any failure this exits non-zero and leaves the
previous file in place, so the heatmap keeps the last good LeetCode data.
"""

import datetime as dt
import json
import pathlib
import sys
import urllib.request

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "Jyothsna_G"
URL = "https://leetcode.com/graphql"
OUT = pathlib.Path("data/leetcode.json")

QUERY = """
query($username: String!) {
  matchedUser(username: $username) {
    userCalendar { streak totalActiveDays submissionCalendar }
  }
}
"""


def fetch() -> dict:
    body = json.dumps({"query": QUERY, "variables": {"username": USERNAME}})
    req = urllib.request.Request(
        URL,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Referer": f"https://leetcode.com/u/{USERNAME}/",
            "User-Agent": "Mozilla/5.0 (profile-art/1.0)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    user = (fetch().get("data") or {}).get("matchedUser")
    if not user:
        raise SystemExit(f"LeetCode user {USERNAME!r} not found")

    calendar = user["userCalendar"]
    # submissionCalendar is a JSON string of {unix-seconds at UTC midnight: count}.
    raw = json.loads(calendar["submissionCalendar"] or "{}")
    counts = {}
    for ts, n in raw.items():
        date = dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).date().isoformat()
        counts[date] = counts.get(date, 0) + int(n)

    payload = {
        "username": USERNAME,
        "total": sum(counts.values()),
        "active_days": calendar.get("totalActiveDays"),
        "max_streak": calendar.get("streak"),
        "counts": dict(sorted(counts.items())),
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(
        f"wrote {OUT}: {payload['total']} submissions over {len(counts)} days"
    )


if __name__ == "__main__":
    main()
