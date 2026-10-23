#!/usr/bin/env python3
"""Main-paper qualitative figure across the three models (one column): rows FLUX.1-dev / HunyuanVideo / Wan2.1,
columns Reference | SeaCache | KalSea, each at the lower budget of the paper, with the per-image / per-video PSNR.

Reads the upper-quartile example of qual_tiles/<flux_tag>/meta.json (qual_select.py) and of
qual_tiles/video_<model>/meta.json (video_qual_select.py; the middle frame of the 65). Writes fig_qual_models.tex here
and ../fig_qual_models.pdf (rasters embedded as the JPEG tiles, text and frames vector), same style as fig_qualitative.py.

    python fig_qual_models.py --no-crops      (the paper uses --no-crops; crops: zoom windows below each panel)
"""
import argparse
import json
import os

import fig_qualitative as FQ

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = ("seacache", "ours")
NAME = {"flux": "FLUX.1-dev", "hunyuan": "HunyuanVideo", "wan": "Wan2.1-1.3B"}

W_TOTAL = 236.25         # \columnwidth = 3.28125 in
GAP_COL = 1.5
GAP_ZOOM = 1.5
GAP_ROW = 3.0
TITLE_H = 10.0           # one line of 7/8 pt above each row
PSNR_H = 9.0
HEADER_H = 11.0


def load(flux_tag, q=75.0):
    rows = []
    m = json.load(open(os.path.join(HERE, "qual_tiles", flux_tag, "meta.json")))
    p = next(p for p in m["prompts"] if float(p["quantile"]) == q)
    rows.append(dict(model="flux", tag=flux_tag, prompt=p["prompt"], nfe=p["nfe"], psnr=p["psnr"], size=p["size"],
                     window=p["window"], full={k: v["full"] for k, v in p["tiles"].items()},
                     crop={k: v["crop"] for k, v in p["tiles"].items()}))
    for model in ("hunyuan", "wan"):
        tag = f"video_{model}"
        m = json.load(open(os.path.join(HERE, "qual_tiles", tag, "meta.json")))
        p = next(p for p in m["prompts"] if float(p["quantile"]) == q)
        k = str(p["main_frame"])
        rows.append(dict(model=model, tag=tag, prompt=p["prompt"], nfe=p["nfe"], psnr=p["psnr"], size=p["size"],
                         window=p["window"], full={m_: t[k] for m_, t in p["tiles"].items()},
                         crop={m_: t["crop"] for m_, t in p["tiles"].items()}))
    return rows


def build(rows, crops):
    w = (W_TOTAL - 2 * GAP_COL) / 3
    hs = [w * r["size"][1] / r["size"][0] for r in rows]
    zh = w / 2                                         # all zoom windows are 2:1
    row_h = [TITLE_H + h + (GAP_ZOOM + zh if crops else 0) + PSNR_H for h in hs]
    H = HEADER_H + sum(row_h) + GAP_ROW * (len(rows) - 1)
    L = [r"\begin{tikzpicture}[x=1bp,y=1bp,line join=round]",
         fr"\path[use as bounding box] (0,0) rectangle ({W_TOTAL:.2f},{-H:.2f});"]

    def gx(j):
        return j * (w + GAP_COL)

    L.append(fr"\node[anchor=south,inner sep=0] at ({w / 2:.2f},{-HEADER_H + 2.4:.2f}) {{\hdr Reference}};")
    for j, m in enumerate(METHODS, start=1):
        L.append(fr"\node[anchor=south,inner sep=0] (h{j}) at ({gx(j) + w / 2 + 3.0:.2f},{-HEADER_H + 2.4:.2f}) "
                 fr"{{\hdr {FQ.LABEL[m]}}};")
        L.append(r"\path (h%d.west) ++(-4.0,1.9) coordinate (mk);" % j)
        L.append(r"\begin{scope}[shift={(mk)}]" + FQ.marker(m, 0, 0) + r"\end{scope}")
    ytop = -HEADER_H
    for r, h, rh in zip(rows, hs, row_h):
        title = (fr"\textbf{{{NAME[r['model']]}}}, {int(r['nfe'])} NFE: "
                 fr"{{\itshape ``{FQ.tex_escape(r['prompt'])}''}}")
        L.append(fr"\node[anchor=south west,inner sep=0,font=\ttl] at (0,{ytop - TITLE_H + 2.2:.2f}) {{{title}}};")
        yimg = ytop - TITLE_H
        S = r["size"][0]
        x0w, y0w, ww, wh = r["window"]
        best = max(METHODS, key=lambda m: r["psnr"][m])
        for j, m in enumerate(("reference",) + METHODS):
            x = gx(j)
            L.append(fr"\node[anchor=north west,inner sep=0] at ({x:.2f},{yimg:.2f}) "
                     fr"{{\includegraphics[width={w:.3f}bp,height={h:.3f}bp]{{qual_tiles/{r['tag']}/{r['full'][m]}}}}};")
            yb = yimg - h
            if crops:
                rx0, rx1 = x + x0w / S * w, x + (x0w + ww) / S * w
                ry0, ry1 = yimg - y0w / S * w, yimg - (y0w + wh) / S * w
                L.append(fr"\draw[black,line width=1.1bp] ({rx0:.2f},{ry0:.2f}) rectangle ({rx1:.2f},{ry1:.2f});")
                L.append(fr"\draw[white,line width=0.5bp] ({rx0:.2f},{ry0:.2f}) rectangle ({rx1:.2f},{ry1:.2f});")
                yb -= GAP_ZOOM
                L.append(fr"\node[anchor=north west,inner sep=0] at ({x:.2f},{yb:.2f}) "
                         fr"{{\includegraphics[width={w:.3f}bp,height={zh:.3f}bp]{{qual_tiles/{r['tag']}/{r['crop'][m]}}}}};")
                yb -= zh
            if m == "reference":
                txt = r"\color{cInkTwo}PSNR (dB)"
            else:
                txt = f"{r['psnr'][m]:.2f}"
                txt = fr"\textbf{{{txt}}}" if m == best else txt
            L.append(fr"\node[anchor=north,inner sep=0] at ({x + w / 2:.2f},{yb - 1.6:.2f}) {{\num {txt}}};")
        ytop -= rh + GAP_ROW
    L.append(r"\end{tikzpicture}")
    return "\n".join(L), H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flux_tag", default="nfe13_teaser", help="qual_select.py tag at delta 0.6 with a q75 prompt")
    ap.add_argument("--no-crops", dest="crops", action="store_false")
    ap.add_argument("--name", default="fig_qual_models")
    ap.add_argument("--engine", default=FQ.default_engine())
    a = ap.parse_args()
    body, H = build(load(a.flux_tag), a.crops)
    pre = FQ.PREAMBLE.replace("fig_qualitative.py", "fig_qual_models.py").replace(
        r"\begin{document}", r"\newcommand{\ttl}{\fontsize{7}{8}\selectfont\color{cInk}}" + "\n" + r"\begin{document}")
    FQ.compile_standalone(a.name, body, H, a.engine, preamble=pre)


if __name__ == "__main__":
    main()
