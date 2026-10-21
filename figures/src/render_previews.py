#!/usr/bin/env python3
"""Render 300-dpi PNG previews of figure PDFs: python render_previews.py ../fig_*.pdf  (PyMuPDF or pypdfium2)."""
import sys


def render(path, dpi=300):
    out = path[:-4] + ".png"
    try:
        import pymupdf
        pix = pymupdf.open(path)[0].get_pixmap(dpi=dpi, alpha=False)
        pix.save(out)
        size = (pix.width, pix.height)
    except ImportError:
        import pypdfium2 as pdfium
        img = pdfium.PdfDocument(path)[0].render(scale=dpi / 72).to_pil().convert("RGB")
        img.save(out, optimize=True)
        size = img.size
    print(out, size)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        render(p)
