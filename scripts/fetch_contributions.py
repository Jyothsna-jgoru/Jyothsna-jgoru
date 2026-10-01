"""
Fetch the contribution calendar from GitHub's public profile endpoint.

No token and no GraphQL: /users/<login>/contributions is public HTML, so the
scheduled workflow needs no secrets. Parsed with a regex rather than
BeautifulSoup to keep the Action's dependency list to one package.

    python scripts/fetch_contributions.py [login]

Writes data/contributions.json.
"""

import json
import pathlib
import re
import sys
import urllib.request

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "Jyothsna-jgoru"
URL = f"https://github.com/users/{LOGIN}/contributions"
OUT = pathlib.Path("data/contributions.json")

# Each day is a <td ... data-date="YYYY-MM-DD" data-level="0..4">. Attribute
# order is not guaranteed, so match the cell then pull each attribute out.
CELL = re.compile(r"<td[^>]*data-date=[\"'][^\"']+[\"'][^>]*>", re.I)
DATE = re.compile(r"data-date=[\"']([^\"']+)[\"']")
LEVEL = re.compile(r"data-level=[\"'](\d)[\"']")
TOTAL = re.compile(r"([\d,]+)\s*\n?\s*contributions", re.I)


def fetch(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "profile-art/1.0 (+https://github.com/%s)" % LOGIN,
            "Accept": "text/html",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> None:
    html_text = fetch(URL)

    days = []
    for cell in CELL.findall(html_text):
        date = DATE.search(cell)
        level = LEVEL.search(cell)
        if date and level:
            days.append({"date": date.group(1), "level": int(level.group(1))})

    if not days:
        raise SystemExit(
            "no contribution cells parsed — GitHub markup may have changed"
        )

    days.sort(key=lambda d: d["date"])

    total_match = TOTAL.search(html_text)
    total = int(total_match.group(1).replace(",", "")) if total_match else None

    # Longest run of consecutive days with any contribution.
    best = run = 0
    for day in days:
        run = run + 1 if day["level"] > 0 else 0
        best = max(best, run)

    payload = {
        "login": LOGIN,
        "total": total,
        "days": days,
        "active_days": sum(1 for d in days if d["level"] > 0),
        "longest_streak": best,
        "first": days[0]["date"],
        "last": days[-1]["date"],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(
        f"wrote {OUT}: {len(days)} days, {payload['active_days']} active, "
        f"total={total}, longest streak={best}"
    )


if __name__ == "__main__":
    main()
