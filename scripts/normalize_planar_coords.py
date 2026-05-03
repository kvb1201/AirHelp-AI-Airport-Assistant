#!/usr/bin/env python3
"""
Example: min–max normalize source X/Y into 0–100 for the same bounding box as the terminal map.

Input CSV columns (example): name,x_src,y_src
Output: name,x_norm,y_norm

  x_norm = 100 * (x_src - xmin) / (xmax - xmin)
  y_norm = 100 * (y_src - ymin) / (ymax - ymin)

Usage:
  python3 scripts/normalize_planar_coords.py raw_shops.csv out_shops.csv xmin xmax ymin ymax

Replace with your pipeline (pixels on PDF, lat/lon in a bbox, etc.).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 7:
        print(__doc__)
        sys.exit(1)
    inp, outp = Path(sys.argv[1]), Path(sys.argv[2])
    xmin, xmax = float(sys.argv[3]), float(sys.argv[4])
    ymin, ymax = float(sys.argv[5]), float(sys.argv[6])
    dx = xmax - xmin
    dy = ymax - ymin
    if dx <= 0 or dy <= 0:
        raise SystemExit("Invalid bbox")

    with inp.open(encoding="utf-8", newline="") as fin, outp.open("w", encoding="utf-8", newline="") as fout:
        r = csv.DictReader(fin)
        w = csv.DictWriter(
            fout,
            fieldnames=["name", "x_norm", "y_norm", "x_src", "y_src"],
        )
        w.writeheader()
        for row in r:
            xs = float(row["x_src"])
            ys = float(row["y_src"])
            xn = 100.0 * (xs - xmin) / dx
            yn = 100.0 * (ys - ymin) / dy
            w.writerow(
                {
                    "name": row.get("name", ""),
                    "x_norm": round(xn, 4),
                    "y_norm": round(yn, 4),
                    "x_src": xs,
                    "y_src": ys,
                }
            )
    print(f"Wrote {outp}")


if __name__ == "__main__":
    main()
