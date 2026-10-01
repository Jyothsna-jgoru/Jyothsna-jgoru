"""
Render a photo as an animated ASCII-art SVG.

The source photo is deliberately NOT committed to this repo — pass its path
on the command line. Only the generated SVG is committed, so the repo never
carries a personal image file.

    python scripts/make_portrait_svg.py "C:/path/to/photo.png"

Animation: each row fades in on a short stagger, so the portrait appears to
print line by line, then freezes. GitHub strips <style> from markdown but
renders it inside an SVG, which is why the animation belongs in here rather
than in the README.
"""

import html
import pathlib
import sys

import numpy as np
from PIL import Image

OUT = pathlib.Path("assets/portrait.svg")

COLS = 56            # character columns — fewer averages away photo noise
FONT = 11.0          # px
CHAR_W = FONT * 0.6  # monospace advance width
LINE_H = FONT * 1.0
PAD = 14

# Crop to the subject before sampling. A wide shot spends most of its glyphs
# on background; these fractions keep the head and shoulders.
CROP = (0.14, 0.02, 0.86, 0.92)   # left, top, right, bottom (0..1)
GAMMA = 1.45                      # >1 darkens mid-tones, deepening the face

# Light -> dense. Luminance is inverted before lookup so dark hair reads as
# dense glyphs and the bright background falls away to spaces.
RAMP = " .:-=+*#%@"

INK = "#8fd3ff"
BG = "#0b0f1a"
EDGE = "#1b2436"


def load_glyph_rows(photo: pathlib.Path) -> list[str]:
    img = Image.open(photo).convert("L")

    w, h = img.size
    img = img.crop(
        (int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h))
    )

    # Contrast stretch: clip the extreme 2% at each end and rescale. Cheap
    # stand-in for CLAHE that avoids an OpenCV dependency.
    a = np.asarray(img, dtype=np.float32)
    lo, hi = np.percentile(a, 2), np.percentile(a, 98)
    a = np.clip((a - lo) / max(hi - lo, 1e-6), 0.0, 1.0)
    a = np.power(a, GAMMA)

    rows = max(1, int(round(a.shape[0] * (COLS / a.shape[1]) * (CHAR_W / LINE_H))))
    small = Image.fromarray((a * 255).astype(np.uint8)).resize(
        (COLS, rows), Image.LANCZOS
    )

    px = 1.0 - (np.asarray(small, dtype=np.float32) / 255.0)  # invert
    last = len(RAMP) - 1
    return ["".join(RAMP[int(round(v * last))] for v in row) for row in px]


def build_svg(rows: list[str]) -> str:
    width = int(COLS * CHAR_W + PAD * 2)
    height = int(len(rows) * LINE_H + PAD * 2 + 16)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="ASCII portrait">',
        "<style>",
        "  .bg   { fill: %s; }" % BG,
        "  .edge { fill: none; stroke: %s; stroke-width: 1; }" % EDGE,
        "  .cap  { font: 500 8px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;"
        "          fill: #5c6b86; }",
        "  .g    { font: %gpx ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;"
        "          fill: %s; white-space: pre; opacity: 0;"
        "          animation: rowIn .34s ease-out forwards; }" % (FONT, INK),
        "  @keyframes rowIn { from { opacity: 0 } to { opacity: .92 } }",
        "  @media (prefers-reduced-motion: reduce) {",
        "    .g { animation: none; opacity: .92; }",
        "  }",
        "</style>",
        f'<rect class="bg" width="{width}" height="{height}" rx="10"/>',
        f'<rect class="edge" x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="10"/>',
    ]

    for i, line in enumerate(rows):
        delay = 0.12 + i * 0.035
        y = PAD + (i + 1) * LINE_H
        out.append(
            f'<text class="g" x="{PAD}" y="{y:.1f}" '
            f'style="animation-delay:{delay:.2f}s">{html.escape(line)}</text>'
        )

    cap_delay = 0.12 + len(rows) * 0.035 + 0.2
    out.append(
        f'<text class="cap" x="{PAD}" y="{height - PAD + 4}" opacity="0">'
        f'<animate attributeName="opacity" to="1" dur=".4s" '
        f'begin="{cap_delay:.2f}s" fill="freeze"/>'
        f"jyothsna@github ~ $ render --portrait</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/make_portrait_svg.py <photo path>")

    photo = pathlib.Path(sys.argv[1])
    if not photo.exists():
        sys.exit(f"photo not found: {photo}")

    rows = load_glyph_rows(photo)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build_svg(rows), encoding="utf-8")
    print(f"wrote {OUT}  ({COLS} x {len(rows)} glyphs)")


if __name__ == "__main__":
    main()
