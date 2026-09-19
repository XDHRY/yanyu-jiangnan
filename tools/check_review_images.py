"""Pixel tripwire for the four cheap Jiangnan CI review frames.

This is intentionally not a beauty score. It rejects only obvious technical
failures such as black/white renders, fog wash, or completely flat frames.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageStat

ROOT = Path("ci_artifacts")
FILES = [
    ROOT / "review-01-rain-three-quarter.png",
    ROOT / "review-02-rain-front.png",
    ROOT / "review-03-snow-top.png",
    ROOT / "review-04-snow-front.png",
]

rows = []
problems = []
for path in FILES:
    if not path.is_file():
        problems.append(f"missing {path.name}")
        continue
    im = Image.open(path).convert("L")
    stat = ImageStat.Stat(im)
    hist = im.histogram()
    n = im.width * im.height
    ordered = []
    for value, count in enumerate(hist):
        ordered.extend([value] * count)
    p01 = ordered[max(0, n // 100)]
    p99 = ordered[min(n - 1, 99 * n // 100)]
    mean = stat.mean[0]
    stdev = stat.stddev[0]
    row = {
        "file": path.name,
        "size": [im.width, im.height],
        "mean": round(mean, 2),
        "stdev": round(stdev, 2),
        "p01": p01,
        "p99": p99,
    }
    rows.append(row)
    if mean < 8:
        problems.append(f"{path.name} nearly black mean={mean:.1f}")
    if mean > 220:
        problems.append(f"{path.name} nearly white mean={mean:.1f}")
    if stdev < 7:
        problems.append(f"{path.name} flat stdev={stdev:.1f}")
    if p01 == 0 and p99 < 24:
        problems.append(f"{path.name} crushed histogram")
    if p01 > 185:
        problems.append(f"{path.name} fog/white wash p01={p01}")

report = {"shots": rows, "problems": problems}
(ROOT / "review-pixel-qa.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
if problems:
    raise SystemExit(1)
