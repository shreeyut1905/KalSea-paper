#!/usr/bin/env python3
"""Generate the qualitative comparison figure (TikZ source + vector PDF with JPEG-embedded tiles).

Reads qual_tiles/<tag>/meta.json written by qual_select.py, emits <name>.tex next to this script and compiles it with a
LaTeX engine (XeLaTeX/tectonic: TeX Gyre Termes = Times; pdfLaTeX: times package), writing ../<name>.pdf.
The rasters are embedded as the JPEG files themselves (quality 92, 4:4:4), text and frames are vector.

    python fig_qualitative.py --tag nfe13 --name fig_qualitative [--engine /path/to/tectonic]
"""
import argparse
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.dirname(HERE)
METHODS = ("seacache", "ours")   # KalSea vs SeaCache
NC = 1 + len(METHODS)              # image columns per prompt group (reference + methods)
LABEL = {"reference": "Reference", "seacache": "SeaCache", "kalsea": "KalSea w/o PCGS", "ours": "KalSea"}
COLOR = {"seacache": "cSeaCache", "kalsea": "cKalSea", "ours": "cOurs"}
QNAME = {50.0: "Median gain", 75.0: "Upper-quartile gain", 25.0: "Lower-quartile gain"}

# ---- layout (bp = 1/72 in) ----
W_TOTAL = 495.0          # \textwidth = 6.875 in
LEFT = 10.0              # rotated row labels
GAP_COL = 1.5            # between tiles of one prompt
GAP_GROUP = 8.0          # between the two prompts of a row
GAP_ZOOM = 1.5           # image -> crop
GAP_ROW = 6.0
PROMPT_H = 18.5          # two lines of 7/8.1 pt + padding
PSNR_H = 8.5
HEADER_H = 24.0


def tex_escape(s):
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    out = "".join(rep.get(ch, ch) for ch in s)
    # typographic single quotes: opening after start/space/(, closing otherwise
    res = []
    for i, ch in enumerate(out):
        if ch == "'":
            prev = out[i - 1] if i > 0 else " "
            res.append("`" if prev in " (\t" else "'")
        else:
            res.append(ch)
    return "".join(res)


def marker(m, x, y, s=2.1):
    c = COLOR[m]
    if m == "seacache":
        return fr"\fill[{c}] ({x - s:.2f},{y - s:.2f}) rectangle ({x + s:.2f},{y + s:.2f});"
    if m == "kalsea":
        r = s * 1.3
        return fr"\fill[{c}] ({x:.2f},{y + r:.2f}) -- ({x + r:.2f},{y:.2f}) -- ({x:.2f},{y - r:.2f}) -- ({x - r:.2f},{y:.2f}) -- cycle;"
    return fr"\fill[{c}] ({x:.2f},{y - 0.25:.2f}) circle ({s * 1.05:.2f});"


def build(meta, tag, ncols_groups=2):
    prompts = meta["prompts"]
    nfes = sorted({int(p["nfe"]) for p in prompts})   # per-prompt NFE of the shown prompts (identical for the 3 methods)
    nfe_txt = str(nfes[0]) if len(nfes) == 1 else f"{nfes[0]}--{nfes[-1]}"
    # one rotated stratum label per row if both prompts of every row come from the same quantile, else one per prompt
    rows_q = [{float(p["quantile"]) for p in prompts[i:i + ncols_groups]} for i in range(0, len(prompts), ncols_groups)]
    per_group = any(len(q) > 1 for q in rows_q)
    gap_group = max(GAP_GROUP, LEFT) if per_group else GAP_GROUP
    w = (W_TOTAL - LEFT - ncols_groups * (NC - 1) * GAP_COL - (ncols_groups - 1) * gap_group) / (NC * ncols_groups)
    zh = w * meta["prompts"][0]["window"][3] / meta["prompts"][0]["window"][2]
    row_h = PROMPT_H + w + GAP_ZOOM + zh + PSNR_H
    nrows = (len(prompts) + ncols_groups - 1) // ncols_groups
    H = HEADER_H + nrows * row_h + (nrows - 1) * GAP_ROW
    L = []
    L.append(r"\begin{tikzpicture}[x=1bp,y=1bp,line join=round]")
    L.append(fr"\path[use as bounding box] (0,0) rectangle ({W_TOTAL:.2f},{-H:.2f});")

    def gx(gi, j):  # left x of column j (0..NC-1) in group gi
        return LEFT + gi * (NC * w + (NC - 1) * GAP_COL + gap_group) + j * (w + GAP_COL)

    # header: Reference column + a spanning "13 NFE" label over the three accelerated columns
    for gi in range(ncols_groups):
        x0 = gx(gi, 0)
        L.append(fr"\node[anchor=south,inner sep=0] at ({x0 + w / 2:.2f},{-HEADER_H + 2.2:.2f}) {{\hdr Reference}};")
        L.append(fr"\node[anchor=south,inner sep=0] at ({x0 + w / 2:.2f},{-HEADER_H + 12.6:.2f}) {{\sub 50 NFE}};")
        L.append(fr"\draw[cMuted,line width=0.4bp] ({x0 + 1:.2f},{-HEADER_H + 11.6:.2f}) -- ({x0 + w - 1:.2f},{-HEADER_H + 11.6:.2f});")
        xa, xb = gx(gi, 1), gx(gi, NC - 1) + w
        L.append(fr"\node[anchor=south,inner sep=0] at ({(xa + xb) / 2:.2f},{-HEADER_H + 12.6:.2f}) {{\sub {nfe_txt} NFE, identical computed steps}};")
        L.append(fr"\draw[cMuted,line width=0.4bp] ({xa + 1:.2f},{-HEADER_H + 11.6:.2f}) -- ({xb - 1:.2f},{-HEADER_H + 11.6:.2f});")
        for j, m in enumerate(METHODS, start=1):
            xc = gx(gi, j) + w / 2
            L.append(fr"\node[anchor=south,inner sep=0] (h{gi}{j}) at ({xc + 3.0:.2f},{-HEADER_H + 2.2:.2f}) {{\hdr {LABEL[m]}}};")
            L.append(r"\path (h%d%d.west) ++(-4.0,1.9) coordinate (mk);" % (gi, j))
            L.append(r"\begin{scope}[shift={(mk)}]" + marker(m, 0, 0) + r"\end{scope}")

    for k, p in enumerate(prompts):
        r, gi = divmod(k, ncols_groups)
        ytop = -HEADER_H - r * (row_h + GAP_ROW)
        # prompt text
        xg0, xg1 = gx(gi, 0), gx(gi, NC - 1) + w
        txt = tex_escape(p["prompt"])
        L.append(fr"\node[anchor=south west,inner sep=0,text width={xg1 - xg0:.2f}bp,align=flush left,font=\prm] "
                 fr"at ({xg0:.2f},{ytop - PROMPT_H + 2.0:.2f}) {{``{txt}''}};")
        yimg = ytop - PROMPT_H
        x0w, y0w, ww, wh = p["window"]
        S = p["size"][0]
        best = max(METHODS, key=lambda m: p["psnr"][m])
        for j, m in enumerate(("reference",) + METHODS):
            x = gx(gi, j)
            tf = f"qual_tiles/{tag}/{p['tiles'][m]['full']}"
            tc = f"qual_tiles/{tag}/{p['tiles'][m]['crop']}"
            L.append(fr"\node[anchor=north west,inner sep=0] at ({x:.2f},{yimg:.2f}) {{\includegraphics[width={w:.3f}bp,height={w:.3f}bp]{{{tf}}}}};")
            # zoom window on the full image
            rx0, rx1 = x + x0w / S * w, x + (x0w + ww) / S * w
            ry0, ry1 = yimg - y0w / S * w, yimg - (y0w + wh) / S * w
            L.append(fr"\draw[black,line width=1.3bp] ({rx0:.2f},{ry0:.2f}) rectangle ({rx1:.2f},{ry1:.2f});")
            L.append(fr"\draw[white,line width=0.6bp] ({rx0:.2f},{ry0:.2f}) rectangle ({rx1:.2f},{ry1:.2f});")
            yc = yimg - w - GAP_ZOOM
            L.append(fr"\node[anchor=north west,inner sep=0] at ({x:.2f},{yc:.2f}) {{\includegraphics[width={w:.3f}bp,height={zh:.3f}bp]{{{tc}}}}};")
            if m != "reference":
                val = f"{p['psnr'][m]:.2f}"
                val = fr"\textbf{{{val}}}" if m == best else val
                L.append(fr"\node[anchor=north,inner sep=0] at ({x + w / 2:.2f},{yc - zh - 1.8:.2f}) {{\num {val}}};")
            else:
                L.append(fr"\node[anchor=north,inner sep=0] at ({x + w / 2:.2f},{yc - zh - 1.8:.2f}) {{\num\color{{cInkTwo}}PSNR (dB)}};")
        # stratum label (rotated), once per row (homogeneous rows) or once per prompt
        if gi == 0 or per_group:
            q = float(p["quantile"])
            ymid = yimg - (w + GAP_ZOOM + zh) / 2
            L.append(fr"\node[rotate=90,anchor=south,inner sep=0] at ({gx(gi, 0) - 3.2:.2f},{ymid:.2f}) {{\sub {QNAME.get(q, f'{q:.0f}th pct.')}}};")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L), H


PREAMBLE = r"""%% Auto-generated by fig_qualitative.py -- do not edit by hand.
\documentclass[border=0pt]{standalone}
\usepackage{iftex}
\ifPDFTeX
  \usepackage[T1]{fontenc}\usepackage{times}
\else
  \usepackage{fontspec}\setmainfont{texgyretermes}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\fi
\usepackage{graphicx}
\usepackage{tikz}
\input{palette.tex}
\newcommand{\hdr}{\fontsize{7.5}{8.5}\selectfont}
\newcommand{\sub}{\fontsize{7}{8}\selectfont\color{cInkTwo}}
\newcommand{\prm}{\fontsize{7}{8.1}\selectfont\itshape\color{cInk}}
\newcommand{\num}{\fontsize{7}{8}\selectfont\color{cInk}}
\begin{document}
"""


def default_engine():
    tl = os.path.expanduser("~/texlive/2026/bin/x86_64-linux/pdflatex")       # project toolchain (build.sh)
    return os.environ.get("LATEX_ENGINE", tl if os.path.exists(tl) else "tectonic")


def compile_standalone(name, body, H, engine, preamble=None):
    """write <name>.tex next to this script (PREAMBLE + body) and compile it to ../<name>.pdf"""
    tex = os.path.join(HERE, name + ".tex")
    open(tex, "w").write((preamble or PREAMBLE) + body + "\n\\end{document}\n")
    print(f"wrote {tex}  ({W_TOTAL / 72:.3f} x {H / 72:.3f} in)" if preamble is None else f"wrote {tex}  (height {H / 72:.3f} in)")
    env = dict(os.environ, TECTONIC_CACHE_DIR=os.environ.get("TECTONIC_CACHE_DIR", "/tmp/figtools/tcache"))
    if os.path.basename(engine).startswith("tectonic"):
        cmd = [engine, "-X", "compile", "--outdir", FIG_DIR, tex]
    else:  # pdflatex / xelatex / lualatex
        cmd = [engine, "-interaction=nonstopmode", "-output-directory", FIG_DIR, tex]
    res = subprocess.run(cmd, cwd=HERE, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout[-3000:], res.stderr[-3000:])
        raise SystemExit("LaTeX failed")
    for ext in (".aux", ".log"):
        f = os.path.join(FIG_DIR, name + ext)
        if os.path.exists(f):
            os.remove(f)
    print("wrote", os.path.join(FIG_DIR, name + ".pdf"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="nfe13")
    ap.add_argument("--name", default="fig_qualitative")
    ap.add_argument("--groups", type=int, default=2, help="prompts per row")
    ap.add_argument("--engine", default=default_engine())
    a = ap.parse_args()
    meta = json.load(open(os.path.join(HERE, "qual_tiles", a.tag, "meta.json")))
    body, H = build(meta, a.tag, a.groups)
    compile_standalone(a.name, body, H, a.engine)


if __name__ == "__main__":
    main()
