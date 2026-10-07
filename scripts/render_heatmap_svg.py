"""
Render GitHub contributions + LeetCode submissions as one animated heatmap SVG.

Each day's square is shaded by the sum of both counts, so coding on either
platform shows up in the same grid. The tooltip on a square breaks the day
down by source. data/leetcode.json is optional; without it the grid is
GitHub-only.

Squares reveal on a diagonal sweep (delay scales with week + weekday) so the
grid fills left to right, then freezes. Month labels and a legend match
GitHub's own layout closely enough to read as familiar.

    python scripts/render_heatmap_svg.py
"""

import datetime as dt
import json
import pathlib

SRC = pathlib.Path("data/contributions.json")
LEETCODE = pathlib.Path("data/leetcode.json")
OUT = pathlib.Path("assets/contrib-heatmap.svg")

CELL = 11          # square size
GAP = 3            # gap between squares
LEFT = 30          # room for weekday labels
TOP = 24           # room for month labels
PAD = 14
FOOT = 30

# index 0 is "no contributions"; 1..4 are GitHub's green ramp
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG = "#0b0f1a"
EDGE = "#1b2436"
TEXT = "#6e7f99"

WEEKDAYS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count: int, thresholds: list) -> int:
    if count <= 0:
        return 0
    return 1 + sum(1 for t in thresholds if count > t)


def merge(data: dict, leetcode: dict) -> list:
    """Return [{date, github, leetcode, total, level}] over GitHub's window."""
    lc_counts = leetcode.get("counts", {})
    days = []
    for day in data["days"]:
        # Older contributions.json files carry only levels; treat a level as
        # that many contributions so the merge still degrades sensibly.
        gh = day.get("count", day["level"])
        lc = lc_counts.get(day["date"], 0)
        days.append({"date": day["date"], "github": gh, "leetcode": lc,
                     "total": gh + lc})

    # Quartiles of the non-zero days, like GitHub's own shading.
    active = sorted(d["total"] for d in days if d["total"] > 0)
    thresholds = [active[len(active) * q // 4] for q in (1, 2, 3)] if active else []
    for d in days:
        d["level"] = level_for(d["total"], thresholds)
    return days


def build() -> str:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    leetcode = (
        json.loads(LEETCODE.read_text(encoding="utf-8"))
        if LEETCODE.exists() else {}
    )
    days = merge(data, leetcode)

    first = dt.date.fromisoformat(days[0]["date"])
    # GitHub weeks start on Sunday; pad so the first column aligns.
    lead = (first.weekday() + 1) % 7

    cells = []  # (week, weekday, level, date, tooltip)
    for i, day in enumerate(days):
        slot = lead + i
        tip = f"{day['date']}: {day['github']} GitHub"
        if leetcode:
            tip += f" + {day['leetcode']} LeetCode"
        cells.append((slot // 7, slot % 7, day["level"], day["date"], tip))

    weeks = max(c[0] for c in cells) + 1
    width = LEFT + weeks * (CELL + GAP) + PAD
    height = TOP + 7 * (CELL + GAP) + FOOT + PAD

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Combined GitHub and LeetCode activity heatmap">',
        "<style>",
        "  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;"
        "          font-size: 9px; fill: %s; }" % TEXT,
        "  .d { opacity: 0; animation: pop .34s cubic-bezier(.16,1,.3,1) forwards; }",
        "  @keyframes pop {",
        "    from { opacity: 0; transform: scale(.4) }",
        "    to   { opacity: 1; transform: scale(1) }",
        "  }",
        "  @media (prefers-reduced-motion: reduce) {",
        "    .d { animation: none; opacity: 1; }",
        "  }",
        "</style>",
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>',
        f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="none" stroke="{EDGE}"/>',
    ]

    # month labels, printed when a month first appears
    seen = set()
    for week, weekday, _level, date, _tip in cells:
        d = dt.date.fromisoformat(date)
        if d.month not in seen and d.day <= 7:
            seen.add(d.month)
            x = LEFT + week * (CELL + GAP)
            out.append(f'<text class="mono" x="{x}" y="{TOP - 8}">{MONTHS[d.month - 1]}</text>')

    for row, label in WEEKDAYS.items():
        y = TOP + row * (CELL + GAP) + CELL - 1
        out.append(f'<text class="mono" x="4" y="{y}">{label}</text>')

    # squares — transform-box/origin keep the scale animation centred
    for week, weekday, level, date, tip in cells:
        x = LEFT + week * (CELL + GAP)
        y = TOP + weekday * (CELL + GAP)
        delay = 0.15 + (week * 0.012) + (weekday * 0.008)
        out.append(
            f'<rect class="d" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{COLORS[level]}" '
            f'style="animation-delay:{delay:.2f}s; transform-box:fill-box; '
            f'transform-origin:center">'
            f"<title>{tip}</title></rect>"
        )

    # footer: totals on the left, legend on the right
    base_y = TOP + 7 * (CELL + GAP) + 18
    summary = f"{sum(d['total'] for d in days)} contributions in the last year"
    out.append(f'<text class="mono" x="{LEFT}" y="{base_y}">{summary}</text>')

    best = run = 0
    for d in days:
        run = run + 1 if d["total"] > 0 else 0
        best = max(best, run)
    active_days = sum(1 for d in days if d["total"] > 0)
    out.append(
        f'<text class="mono" x="{LEFT}" y="{base_y + 13}">'
        f"longest streak: {best} days &#183; "
        f"active: {active_days} of {len(days)}</text>"
    )

    legend_x = width - PAD - (len(COLORS) * (CELL + GAP)) - 34
    out.append(f'<text class="mono" x="{legend_x - 26}" y="{base_y}">Less</text>')
    for i, colour in enumerate(COLORS):
        out.append(
            f'<rect x="{legend_x + i * (CELL + GAP)}" y="{base_y - 9}" '
            f'width="{CELL}" height="{CELL}" rx="2.5" fill="{colour}"/>'
        )
    out.append(
        f'<text class="mono" x="{legend_x + len(COLORS) * (CELL + GAP) + 4}" '
        f'y="{base_y}">More</text>'
    )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
