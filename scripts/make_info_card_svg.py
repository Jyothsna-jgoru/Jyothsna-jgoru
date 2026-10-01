"""
Render a neofetch-style info card as an animated SVG.

Edit CARD below to change the content; nothing here is scraped or inferred.
Lines fade and slide in on a stagger so the card assembles itself, then
freezes.

    python scripts/make_info_card_svg.py
"""

import html
import pathlib

OUT = pathlib.Path("assets/info-card.svg")

TITLE = "jyothsna@github: ~$ neofetch"

# (label, value). An empty tuple renders as a blank spacer row; a label that
# starts with "~" renders as a section heading.
CARD: list[tuple[str, str]] = [
    ("~", "whoami"),
    ("Name", "Jyothsna Devi Goru"),
    ("Now", "Software Engineer @ Capital One"),
    ("Prev", "Zomato · HealthPlix"),
    ("Edu", "M.S. Engineering Science (AI), Univ. at Buffalo"),
    ("", ""),
    ("~", "stack"),
    ("Backend", "Java, Spring Boot, Node.js, FastAPI, Kafka"),
    ("Frontend", "React, TypeScript, Blazor, .NET"),
    ("Cloud", "AWS, Azure, Kubernetes, Terraform"),
    ("AI / ML", "LangGraph, MCP, RAG, Bedrock, PyTorch"),
    ("Data", "PostgreSQL, Redis, Databricks, Delta Lake"),
    ("", ""),
    ("~", "highlights"),
    ("•", "25% lower transaction latency at 15K+ peak RPS"),
    ("•", "CRDT editor converging across 20 concurrent clients"),
    ("•", "KV store sustaining 10K+ ops/sec with replication"),
]

FONT = 11.0
LINE_H = 18.0
PAD = 18
LABEL_X = 18
VALUE_X = 108
WIDTH = 520
BAR_H = 26

BG = "#0b0f1a"
EDGE = "#1b2436"
LABEL = "#f0883e"
VALUE = "#adbac7"
HEAD = "#8fd3ff"
TITLE_C = "#6e7f99"


def build_svg() -> str:
    height = int(BAR_H + PAD * 2 + len(CARD) * LINE_H)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Profile summary card">',
        "<style>",
        "  .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }",
        "  .lbl  { font-size: %gpx; fill: %s; font-weight: 600; }" % (FONT, LABEL),
        "  .val  { font-size: %gpx; fill: %s; }" % (FONT, VALUE),
        "  .hd   { font-size: %gpx; fill: %s; font-weight: 600; }" % (FONT, HEAD),
        "  .ttl  { font-size: 9.5px; fill: %s; }" % TITLE_C,
        "  .row  { opacity: 0; animation: slideIn .4s cubic-bezier(.16,1,.3,1) forwards; }",
        "  @keyframes slideIn {",
        "    from { opacity: 0; transform: translateX(-8px) }",
        "    to   { opacity: 1; transform: translateX(0) }",
        "  }",
        "  @media (prefers-reduced-motion: reduce) {",
        "    .row { animation: none; opacity: 1; }",
        "  }",
        "</style>",
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="{BG}"/>',
        f'<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="10" '
        f'fill="none" stroke="{EDGE}"/>',
        # title bar with the three terminal dots
        f'<path d="M0 10a10 10 0 0 1 10-10h{WIDTH - 20}a10 10 0 0 1 10 10v{BAR_H - 10}H0z" '
        f'fill="#111826"/>',
        '<circle cx="18" cy="13" r="4.5" fill="#ff5f57"/>',
        '<circle cx="34" cy="13" r="4.5" fill="#febc2e"/>',
        '<circle cx="50" cy="13" r="4.5" fill="#28c840"/>',
        f'<text class="mono ttl" x="{WIDTH / 2}" y="17" text-anchor="middle">'
        f"{html.escape(TITLE)}</text>",
    ]

    for i, (label, value) in enumerate(CARD):
        if not label and not value:
            continue
        y = BAR_H + PAD + (i + 1) * LINE_H - 4
        delay = 0.25 + i * 0.07
        style = f'style="animation-delay:{delay:.2f}s"'

        if label == "~":
            out.append(
                f'<text class="mono hd row" x="{LABEL_X}" y="{y:.1f}" {style}>'
                f"~ {html.escape(value)}</text>"
            )
            continue

        out.append(
            f'<g class="row" {style}>'
            f'<text class="mono lbl" x="{LABEL_X}" y="{y:.1f}">{html.escape(label)}</text>'
            f'<text class="mono val" x="{VALUE_X}" y="{y:.1f}">{html.escape(value)}</text>'
            f"</g>"
        )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {OUT}  ({len(CARD)} rows)")


if __name__ == "__main__":
    main()
