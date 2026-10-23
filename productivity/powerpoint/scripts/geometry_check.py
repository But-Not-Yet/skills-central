#!/usr/bin/env python3
"""Pre-render layout lint for generated .pptx decks.

Parses EMU offsets/extents straight from ppt/slides/slideN.xml, computes
rotation-aware axis-aligned boxes, and flags coordinate-provable defects
before any rendering:
  EDGE    shape crosses the safe page margin
  OVL     two text-bearing shapes overlap (neither contains the other)
  GAP     stacked standalone blocks closer than --gap vertically

A text box sitting on a painted (solid-filled) shape that contains it is
treated as one visual unit, so badges straddling card borders and captions
on cards do not fire. Every flag is a CANDIDATE: designed pairs (kicker to
title, big stat to its note) must be re-checked against the rendered image;
only fix what the render actually shows as cramped.

Usage: python geometry_check.py deck.pptx [--edge 0.5] [--gap 0.3]
Exit code 0 always; read the FLAGS count.
"""
import argparse
import itertools
import math
import re
import sys
import zipfile

EMU = 914400.0


def canvas(z):
    xml = z.read("ppt/presentation.xml").decode("utf-8", "ignore")
    m = re.search(r'<p:sldSz[^>]*cx="(\d+)"[^>]*cy="(\d+)"', xml)
    return (int(m.group(1)) / EMU, int(m.group(2)) / EMU) if m else (13.333, 7.5)


def shape_boxes(xml):
    out = []
    for m in re.finditer(r"<p:(sp|graphicFrame)>.*?</p:\1>", xml, re.S):
        sp, kind = m.group(0), m.group(1)
        mm = re.search(
            r'<a:off x="(-?\d+)" y="(-?\d+)"/><a:ext cx="(\d+)" cy="(\d+)"/>', sp)
        if not mm:
            continue
        x, y, cx, cy = [int(v) / EMU for v in mm.groups()]
        if cx < 0.02 or cy < 0.02:
            continue
        rot = re.search(r'rot="(-?\d+)"', sp)
        rad = math.radians(abs(int(rot.group(1))) / 60000) if rot else 0.0
        ex = (cx * math.cos(rad) + cy * math.sin(rad) - cx) / 2
        ey = (cx * math.sin(rad) + cy * math.cos(rad) - cy) / 2
        text = " ".join(re.findall(r"<a:t>([^<]*)</a:t>", sp)).strip()[:36]
        pr = sp.find("<p:spPr>")
        head = sp[pr:pr + 700] if pr >= 0 else ""
        painted = (kind == "graphicFrame") or bool(
            re.search(r"<a:(solidFill|gradFill|blipFill)", head)) and "noFill" not in head
        out.append(((x - ex, y - ey, x + cx + ex, y + cy + ey), text, painted))
    return out


def contains(outer, inner, tol=0.03):
    return (inner[0] >= outer[0] - tol and inner[2] <= outer[2] + tol and
            inner[1] >= outer[1] - tol and inner[3] <= outer[3] + tol)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog="Flags are candidates — re-check designed pairs on the render.")
    ap.add_argument("pptx")
    ap.add_argument("--edge", type=float, default=0.5,
                    help="minimum margin from each slide edge, inches")
    ap.add_argument("--gap", type=float, default=0.3,
                    help="minimum vertical gap between stacked standalone blocks, inches")
    args = ap.parse_args()

    z = zipfile.ZipFile(args.pptx)
    W, H = canvas(z)
    lo, hi = args.edge - 0.02, args.edge - 0.02
    slides = sorted((n for n in z.namelist()
                     if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                    key=lambda n: int(re.search(r"\d+", n).group(0)))
    flags = []
    for sn in slides:
        idx = int(re.search(r"slide(\d+)", sn).group(1))
        boxes = shape_boxes(z.read(sn).decode("utf-8", "ignore"))
        for b in boxes:
            x0, y0, x1, y1 = b[0]
            if not (x0 >= lo and y0 >= hi and x1 <= W - hi and y1 <= H - hi):
                flags.append(f"slide{idx:02d} EDGE  ({x0:.2f},{y0:.2f})-({x1:.2f},{y1:.2f}) {b[1]!r}")
        for a, b in itertools.combinations(boxes, 2):
            ra, rb = a[0], b[0]
            xov = min(ra[2], rb[2]) - max(ra[0], rb[0])
            if xov < 0.4:
                continue
            overlap = not (ra[2] <= rb[0] or rb[2] <= ra[0] or ra[3] <= rb[1] or rb[3] <= ra[1])
            if overlap:
                if contains(ra, rb) or contains(rb, ra):
                    continue
                if a[1] and b[1]:
                    flags.append(f"slide{idx:02d} OVL   {a[1]!r} <-> {b[1]!r}")
            else:
                vgap = max(ra[1], rb[1]) - min(ra[3], rb[3])
                if xov >= 1.0 and 0 <= vgap < args.gap and (a[2] or b[2]):
                    flags.append(f"slide{idx:02d} GAP{vgap:.2f} {a[1]!r} <-> {b[1]!r}")
    for f in flags:
        print(f)
    print(f"FLAGS: {len(flags)}  (candidates — confirm on the rendered images)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
