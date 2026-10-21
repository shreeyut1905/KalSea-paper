#!/usr/bin/env python3
"""Render PDF pages to PNG with PyMuPDF (no poppler/ghostscript needed).

Examples
  # all pages of the paper -> render/page-01.png, page-02.png, ...
  render_pages.py main.pdf render --dpi 150 --clean
  # one figure at print resolution -> render/fig-fig_tradeoff-01.png
  render_pages.py figures/fig_tradeoff.pdf render --dpi 300 --prefix fig-fig_tradeoff
  # selected pages
  render_pages.py main.pdf render --pages 1,5-6

Run with the tools venv: ~/.local/share/paper-tools/venv/bin/python (PyMuPDF 1.28).
"""
import argparse
import glob
import os
import sys

import pymupdf


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return [p for p in out if 0 <= p < n]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--pages", default="", help="1-based, e.g. 1,3-5 (default: all)")
    ap.add_argument("--prefix", default="page")
    ap.add_argument("--clean", action="store_true", help="delete <outdir>/<prefix>-*.png first")
    a = ap.parse_args()

    os.makedirs(a.outdir, exist_ok=True)
    if a.clean:
        for f in glob.glob(os.path.join(a.outdir, f"{a.prefix}-*.png")):
            os.remove(f)
    doc = pymupdf.open(a.pdf)
    pages = parse_pages(a.pages, doc.page_count)
    if not pages:
        sys.exit(f"no pages selected (document has {doc.page_count})")
    for i in pages:
        pix = doc[i].get_pixmap(dpi=a.dpi, alpha=False)
        out = os.path.join(a.outdir, f"{a.prefix}-{i + 1:02d}.png")
        pix.save(out)
        print(out)


if __name__ == "__main__":
    main()
