#!/usr/bin/env python3
"""Submission checks for the paper PDF, or format checks for a single figure PDF.

Paper mode (default; build.sh runs this after every build):
  pdfcheck.py main.pdf --aux build/main.aux --log build/main.log [--strict]
  Reports the page count, the page where the body ends (\\label{endofbody} placed after the conclusion), the page
  of the "References" heading, font embedding and Type 3 fonts, undefined refs/citations, files the
  \\maybeinput/\\maybegraphics placeholders could not find, TODO/TBD markers left in the sources, PDF metadata and
  path leaks (double-blind), and whether the kit files are unchanged.
  --strict exits non-zero on anything that would block submission.

Supplement mode (build.sh runs this for supp.pdf):
  pdfcheck.py supp.pdf --supp --aux build/supp_main.aux --log build/supp_main.log [--strict]
  The same checks without the page limit and the end-of-body / references position; TODO/TBD markers are counted in
  the supplement's own sources (supp_main.tex, sections/supp*.tex, tables/supp_*.tex), which the paper mode skips.

Figure mode:
  pdfcheck.py figures/foo.pdf --figure
  Prints the size in inches relative to the CVPR \\columnwidth (3.28 in) and \\textwidth (6.875 in), and lists
  the fonts with their embedding and type.  Type 3 fonts are reported as problems.

Run with the tools venv: ~/.local/share/paper-tools/venv/bin/python
"""
import argparse
import glob
import hashlib
import os
import re
import sys

import pymupdf

PAPER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_LIMIT = 8                      # CVPR: 8 pages incl. figures/tables; extra pages only for references
COLUMN_W_IN = (6.875 - 0.3125) / 2  # \columnwidth in cvpr.sty = 3.28125 in
TEXT_W_IN = 6.875                   # \textwidth in cvpr.sty
# Official kit files must stay byte-identical (kit/KIT_SOURCE.txt; CVPR 2027 kit v1).
KIT_HASHES = {
    "cvpr.sty": "1cd7f434b13d41c475df4a1901a5d82d9ca8b80b8cf6205dc4602a5c164286b4",
    "ieeenat_fullname.bst": "e38e6166bd7b1e6d23a1b79dcdb55c656e4fcdbe91bdf6b50d827e6b5d1aacfc",
    "preamble.tex": "f666a85903f49929395951e7afb620e96d4e208334623f23135298b4d7f06228",
}
SOURCE_GLOBS = ["main.tex", "macros.tex", "sections/*.tex", "tables/*.tex"]
SUPP_GLOBS = ["supp_main.tex", "sections/supp*.tex", "tables/supp_*.tex"]     # supplement-only sources


def _is_supp_source(rel):
    return rel == "supp_main.tex" or os.path.basename(rel).startswith("supp")
MARKER_RE = re.compile(r"\\(TODO|todo|tbd)\b")
COMMENT_RE = re.compile(r"(?<!\\)%.*$", flags=re.S)
LEAK_PATTERNS = [rb"/home/", rb"ubuntu", rb"PTEX.FileName", rb"PTEX.InfoDict"]


def fonts_of(doc):
    """Unique fonts over all pages, including fonts inside included figure XObjects."""
    seen = {}
    for page in doc:
        for xref, ext, ftype, basefont, *_ in page.get_fonts(full=True):
            seen[(basefont, ftype, ext)] = xref
    return sorted(seen)


def font_problems(fonts):
    probs = []
    for basefont, ftype, ext in fonts:
        if ftype == "Type3":
            probs.append(f"Type 3 font: {basefont}")
        if ext in ("n/a", ""):
            probs.append(f"font not embedded: {basefont} ({ftype})")
    return probs


def endofbody_page(aux):
    if not aux or not os.path.exists(aux):
        return None
    txt = open(aux, encoding="latin-1").read()
    m = re.search(r"\\newlabel\{endofbody\}\{\{[^{}]*\}\{(\d+)\}", txt)
    return int(m.group(1)) if m else None


def references_heading(doc):
    """(page number, y0 in pt) of the first heading after the body: the mandatory 'LLM Usage Statement' (CVPR 2027;
    allowed on the extra pages, like the references) or the bold 'References' heading; None if neither is found."""
    for pno, page in enumerate(doc, start=1):
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = "".join(s["text"] for s in line["spans"]).strip()
                if text in ("References", "LLM Usage Statement") and max(s["size"] for s in line["spans"]) > 10.5:
                    return pno, line["bbox"][1]
    return None


def log_issues(log):
    out = {"undefined": [], "missing": [], "overfull": 0, "rerun": False, "errors": []}
    if not log or not os.path.exists(log):
        return out
    txt = open(log, encoding="latin-1").read()
    out["undefined"] = sorted(set(re.findall(r"(?:Reference|Citation) `([^']+)' on page \d+ undefined", txt)))
    out["missing"] = sorted(set(re.findall(r"MISSING-FILE: (\S+)", txt)))
    out["overfull"] = len(re.findall(r"^Overfull \\hbox", txt, flags=re.M))
    out["rerun"] = "Rerun to get" in txt or "Label(s) may have changed" in txt
    out["errors"] = re.findall(r"^! .*$", txt, flags=re.M)[:10]
    return out


def source_markers(supp=False):
    hits = []
    for g in (SUPP_GLOBS if supp else SOURCE_GLOBS):
        for path in sorted(glob.glob(os.path.join(PAPER_DIR, g))):
            if not supp and _is_supp_source(os.path.relpath(path, PAPER_DIR)):
                continue
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), start=1):
                code = COMMENT_RE.sub("", line)  # drop comments (unescaped % to end of line)
                if MARKER_RE.search(code) and "\\newcommand" not in code and "\\renewcommand" not in code:
                    hits.append(f"{os.path.relpath(path, PAPER_DIR)}:{i}")
    return hits


def kit_changes():
    changed = []
    for name, want in KIT_HASHES.items():
        p = os.path.join(PAPER_DIR, name)
        got = hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else "missing"
        if got != want:
            changed.append(name)
    return changed


def leaks(pdf_path, doc):
    raw = open(pdf_path, "rb").read()
    found = [p.decode() for p in LEAK_PATTERNS if p in raw]
    meta = doc.metadata or {}
    if (meta.get("author") or "").strip():
        found.append(f"metadata author={meta['author']!r}")
    return found


def figure_mode(path):
    doc = pymupdf.open(path)
    r = doc[0].rect
    w_in, h_in = r.width / 72, r.height / 72
    print(f"{path}: {doc.page_count} page(s), {w_in:.3f} x {h_in:.3f} in "
          f"({w_in * 2.54:.2f} x {h_in * 2.54:.2f} cm)")
    print(f"  width = {w_in / COLUMN_W_IN:.2f} x columnwidth ({COLUMN_W_IN:.3f} in), "
          f"{w_in / TEXT_W_IN:.2f} x textwidth ({TEXT_W_IN} in)")
    fonts = fonts_of(doc)
    for basefont, ftype, ext in fonts:
        print(f"  font {basefont}  type={ftype}  embedded={'no' if ext in ('n/a', '') else ext}")
    if not fonts:
        print("  no fonts (text converted to paths, or no text)")
    probs = font_problems(fonts)
    for p in probs:
        print("  PROBLEM:", p)
    return 1 if probs else 0


def paper_mode(a):
    doc = pymupdf.open(a.pdf)
    problems, notes = [], []
    n = doc.page_count
    r = doc[0].rect
    size_ok = abs(r.width - 612) < 1 and abs(r.height - 792) < 1
    body = None if a.supp else endofbody_page(a.aux)
    refs = references_heading(doc)
    print(f"PDF        {a.pdf}: {n} pages, {'US letter' if size_ok else f'{r.width:.0f}x{r.height:.0f} pt'}"
          + ("  (supplementary material: no page limit)" if a.supp else ""))
    if not size_ok:
        problems.append("page size is not US letter")
    if a.supp:
        pass
    elif body is None:
        notes.append("no \\label{endofbody} found in the aux file; body length unknown")
        print("Body       end page unknown (no \\label{endofbody})")
    else:
        print(f"Body       ends on page {body} (limit {PAGE_LIMIT})")
        if body > PAGE_LIMIT:
            problems.append(f"body ends on page {body} > {PAGE_LIMIT}")
    if refs:
        print(f"References heading on page {refs[0]} (y = {refs[1]:.0f} pt)")
        if not a.supp and (refs[0] > PAGE_LIMIT + 1 or (refs[0] == PAGE_LIMIT + 1 and refs[1] > 110)):
            problems.append(f"material before the references on page {refs[0]} (floats or text past page {PAGE_LIMIT}?)")
    else:
        print("References heading not found")
    fonts = fonts_of(doc)
    fprob = font_problems(fonts)
    print(f"Fonts      {len(fonts)} fonts, {len(fprob)} problems")
    problems += fprob
    li = log_issues(a.log)
    if li["errors"]:
        problems += [f"LaTeX error: {e}" for e in li["errors"]]
    if li["undefined"]:
        problems.append(f"undefined refs/citations: {', '.join(li['undefined'])}")
    if li["missing"]:
        problems.append(f"missing figure/table files (placeholders shown): {', '.join(li['missing'])}")
    if li["rerun"]:
        notes.append("LaTeX asked for a rerun (labels may have changed)")
    if li["overfull"]:
        notes.append(f"{li['overfull']} overfull hbox warnings beyond cvpr.sty's 30pt hfuzz")
    marks = source_markers(supp=a.supp)
    if marks:
        problems.append(f"{len(marks)} TODO/TBD markers left in the sources (first: {', '.join(marks[:6])})")
    lk = leaks(a.pdf, doc)
    if lk:
        problems.append(f"possible anonymity leaks in the PDF: {', '.join(lk)}")
    kc = kit_changes()
    if kc:
        problems.append(f"official kit files modified: {', '.join(kc)}")
    # The CVPR 2027 kit has no paper ID (removed to avoid leaking IDs); a leftover \paperID definition is flagged.
    main_tex = os.path.join(PAPER_DIR, "supp_main.tex" if a.supp else "main.tex")
    if os.path.exists(main_tex) and re.search(r"\\def\\paperID", open(main_tex, encoding="utf-8").read()):
        problems.append(f"{os.path.basename(main_tex)} still defines \\paperID (not used by the CVPR 2027 kit)")
    meta = doc.metadata or {}
    if (meta.get("author") or "").strip():
        found.append(f"metadata author={meta['author']!r}")
    return found


def figure_mode(path):
    doc = pymupdf.open(path)
    r = doc[0].rect
    w_in, h_in = r.width / 72, r.height / 72
    print(f"{path}: {doc.page_count} page(s), {w_in:.3f} x {h_in:.3f} in "
          f"({w_in * 2.54:.2f} x {h_in * 2.54:.2f} cm)")
    print(f"  width = {w_in / COLUMN_W_IN:.2f} x columnwidth ({COLUMN_W_IN:.3f} in), "
          f"{w_in / TEXT_W_IN:.2f} x textwidth ({TEXT_W_IN} in)")
    fonts = fonts_of(doc)
    for basefont, ftype, ext in fonts:
        print(f"  font {basefont}  type={ftype}  embedded={'no' if ext in ('n/a', '') else ext}")
    if not fonts:
        print("  no fonts (text converted to paths, or no text)")
    probs = font_problems(fonts)
    for p in probs:
        print("  PROBLEM:", p)
    return 1 if probs else 0


def paper_mode(a):
    doc = pymupdf.open(a.pdf)
    problems, notes = [], []
    n = doc.page_count
    r = doc[0].rect
    size_ok = abs(r.width - 612) < 1 and abs(r.height - 792) < 1
    body = None if a.supp else endofbody_page(a.aux)
    refs = references_heading(doc)
    print(f"PDF        {a.pdf}: {n} pages, {'US letter' if size_ok else f'{r.width:.0f}x{r.height:.0f} pt'}"
          + ("  (supplementary material: no page limit)" if a.supp else ""))
    if not size_ok:
        problems.append("page size is not US letter")
    if a.supp:
        pass
    elif body is None:
        notes.append("no \\label{endofbody} found in the aux file; body length unknown")
        print("Body       end page unknown (no \\label{endofbody})")
    else:
        print(f"Body       ends on page {body} (limit {PAGE_LIMIT})")
        if body > PAGE_LIMIT:
            problems.append(f"body ends on page {body} > {PAGE_LIMIT}")
    if refs:
        print(f"References heading on page {refs[0]} (y = {refs[1]:.0f} pt)")
        if not a.supp and (refs[0] > PAGE_LIMIT + 1 or (refs[0] == PAGE_LIMIT + 1 and refs[1] > 110)):
            problems.append(f"material before the references on page {refs[0]} (floats or text past page {PAGE_LIMIT}?)")
    else:
        print("References heading not found")
    fonts = fonts_of(doc)
    fprob = font_problems(fonts)
    print(f"Fonts      {len(fonts)} fonts, {len(fprob)} problems")
    problems += fprob
    li = log_issues(a.log)
    if li["errors"]:
        problems += [f"LaTeX error: {e}" for e in li["errors"]]
    if li["undefined"]:
        problems.append(f"undefined refs/citations: {', '.join(li['undefined'])}")
    if li["missing"]:
        problems.append(f"missing figure/table files (placeholders shown): {', '.join(li['missing'])}")
    if li["rerun"]:
        notes.append("LaTeX asked for a rerun (labels may have changed)")
    if li["overfull"]:
        notes.append(f"{li['overfull']} overfull hbox warnings beyond cvpr.sty's 30pt hfuzz")
    marks = source_markers(supp=a.supp)
    if marks:
        problems.append(f"{len(marks)} TODO/TBD markers left in the sources (first: {', '.join(marks[:6])})")
    lk = leaks(a.pdf, doc)
    if lk:
        problems.append(f"possible anonymity leaks in the PDF: {', '.join(lk)}")
    kc = kit_changes()
    if kc:
        problems.append(f"official kit files modified: {', '.join(kc)}")
    main_tex = os.path.join(PAPER_DIR, "supp_main.tex" if a.supp else "main.tex")
    if os.path.exists(main_tex) and re.search(r"\\def\\paperID\{\*+\}", open(main_tex, encoding="utf-8").read()):
        problems.append(f"paper ID not set in {os.path.basename(main_tex)} (\\def\\paperID{{*****}}); use the OpenReview ID")
    meta = doc.metadata or {}
    print(f"Metadata   title={meta.get('title')!r} author={meta.get('author')!r} producer={meta.get('producer')!r}")
    for x in notes:
        print("NOTE      ", x)
    for x in problems:
        print("PROBLEM   ", x)
    if not problems:
        print("OK         no blocking problems")
    return 1 if (a.strict and problems) else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--aux", default=os.path.join(PAPER_DIR, "build", "main.aux"))
    ap.add_argument("--log", default=os.path.join(PAPER_DIR, "build", "main.log"))
    ap.add_argument("--strict", action="store_true", help="non-zero exit on any blocking problem")
    ap.add_argument("--figure", action="store_true", help="figure mode: size + fonts of a figure PDF")
    ap.add_argument("--supp", action="store_true", help="supplement mode: no page limit, supplement sources")
    a = ap.parse_args()
    sys.exit(figure_mode(a.pdf) if a.figure else paper_mode(a))


if __name__ == "__main__":
    main()
