#!/usr/bin/env python3
"""Supplementary video examples of one model: for each selected prompt (median and upper-quartile PSNR gain, see
video_qual_select.py) five frames spread over the 65-frame clip, rows Reference / SeaCache / KalSea, per-video PSNR in
the row labels. Same style as fig_qualitative.py (TikZ, JPEG tiles embedded, vector text).

    python fig_video_examples.py --model hunyuan      -> ../fig_video_examples_hunyuan.pdf
"""
import argparse
import json
import os

import fig_qualitative as FQ

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = ("seacache", "ours")
QORDER = (50.0, 75.0)    # median first, then upper quartile (as in the image figures)

W_TOTAL = 495.0          # \textwidth
LBL_W = 46.0             # row labels (method + PSNR)
GAP_COL = 1.5
GAP_ROW = 1.5
GAP_VIDEO = 7.0
TITLE_H = 11.0
HEADER_H = 10.0


def build(meta, tag):
    frames = [str(k) for k in meta["frames"]]
    n = len(frames)
    prompts = sorted(meta["prompts"], key=lambda p: QORDER.index(float(p["quantile"])))
    w = (W_TOTAL - LBL_W - (n - 1) * GAP_COL) / n
    h = w * prompts[0]["size"][1] / prompts[0]["size"][0]
    vid_h = TITLE_H + 3 * h + 2 * GAP_ROW
    H = HEADER_H + len(prompts) * vid_h + (len(prompts) - 1) * GAP_VIDEO
    L = [r"\begin{tikzpicture}[x=1bp,y=1bp,line join=round]",
         fr"\path[use as bounding box] (0,0) rectangle ({W_TOTAL:.2f},{-H:.2f});"]

    def gx(j):
        return LBL_W + j * (w + GAP_COL)

    for j, k in enumerate(frames):
        lab = f"Frame {k}" if j == 0 else k
        L.append(fr"\node[anchor=south,inner sep=0] at ({gx(j) + w / 2:.2f},{-HEADER_H + 2.0:.2f}) {{\sub {lab}}};")
    ytop = -HEADER_H
    for p in prompts:
        q = float(p["quantile"])
        title = fr"{{\color{{cInkTwo}}{FQ.QNAME[q]}:}} {{\itshape ``{FQ.tex_escape(p['prompt'])}''}}"
        L.append(fr"\node[anchor=south west,inner sep=0,font=\num] at ({LBL_W:.2f},{ytop - TITLE_H + 2.4:.2f}) {{{title}}};")
        y = ytop - TITLE_H
        best = max(METHODS, key=lambda m: p["psnr"][m])
        for m in ("reference",) + METHODS:
            for j, k in enumerate(frames):
                L.append(fr"\node[anchor=north west,inner sep=0] at ({gx(j):.2f},{y:.2f}) "
                         fr"{{\includegraphics[width={w:.3f}bp,height={h:.3f}bp]{{qual_tiles/{tag}/{p['tiles'][m][k]}}}}};")
            ym = y - h / 2
            if m == "reference":
                L.append(fr"\node[anchor=west,inner sep=0,align=left] at (7.0,{ym:.2f}) "
                         fr"{{\hdr Reference\\[-0.5bp]\sub 50 NFE}};")
            else:
                val = f"{p['psnr'][m]:.2f}\\,dB"
                val = fr"\textbf{{{val}}}" if m == best else val
                L.append(fr"\node[anchor=west,inner sep=0,align=left] (l{m}) at (7.0,{ym:.2f}) "
                         fr"{{\hdr {FQ.LABEL[m]}\\[-0.5bp]\num {val}}};")
                L.append(fr"\path (l{m}.north west) ++(-3.8,-3.3) coordinate (mk);")
                L.append(r"\begin{scope}[shift={(mk)}]" + FQ.marker(m, 0, 0) + r"\end{scope}")
            y -= h + GAP_ROW
        ytop -= vid_h + GAP_VIDEO
    L.append(r"\end{tikzpicture}")
    return "\n".join(L), H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["hunyuan", "wan"])
    ap.add_argument("--engine", default=FQ.default_engine())
    a = ap.parse_args()
    tag = f"video_{a.model}"
    meta = json.load(open(os.path.join(HERE, "qual_tiles", tag, "meta.json")))
    body, H = build(meta, tag)
    pre = FQ.PREAMBLE.replace("fig_qualitative.py", "fig_video_examples.py")
    FQ.compile_standalone(f"fig_video_examples_{a.model}", body, H, a.engine, preamble=pre)


if __name__ == "__main__":
    main()
