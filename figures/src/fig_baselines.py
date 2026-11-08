#!/usr/bin/env python3
"""Supplementary qualitative figures with every baseline, on the prompts of the existing qualitative figures.

The prompts are those chosen by the fixed rule of qual_select.py / video_qual_select.py (qual_tiles/<tag>/meta.json:
quantiles of the per-prompt PSNR gain of KalSea over SeaCache among prompts with identical steps), so no prompt is picked
by looking at the baselines. Images / videos come from the shared evaluation harness (same prompts and seeds as the
tables): KalSea, SeaCache (--reuse) and the reference from KalSea's released code; TeaCache, TaylorSeer (order 2 on FLUX,
default order 1 on video), Spectrum, SADA and fewer steps from their released code (Spectrum on video: our implementation).
PSNR under each panel (FLUX) or next to each method (video) is the per-image / per-video PSNR w.r.t. the 50-step output
of the same code, as in the tables.

    ~/exp/venv-spectrum/bin/python fig_baselines.py     -> ../fig_baselines_{flux13,flux21,hunyuan,wan}.pdf + captions
"""
import json
import os
import textwrap

import imageio.v3 as iio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.dirname(HERE)
EXP = "/home/ubuntu/exp"
TEXTWIDTH = 6.875  # in, CVPR two-column \textwidth
plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
                     "font.size": 6.5, "pdf.fonttype": 42})

FLUX = {  # tag -> (title, columns: (label, nfe label, image dir, fidelity json, run key))
    "flux13": ("nfe13_supp", "13 NFE", [
        ("Reference", "50", "kalsea_flux_idx/ref", None, None),
        ("Fewer steps", "15", "flux/vanilla15", "flux/fidelity.json", "flux/vanilla15"),
        ("TeaCache", "15", "flux/teacache_0.6", "flux/fidelity.json", "flux/teacache_0.6"),
        ("TaylorSeer", "12", "flux/taylorseer_n5_o2", "flux/fidelity_taylorseer_o2.json", "flux/taylorseer_n5_o2"),
        ("Spectrum", "13", "flux/spectrum_a1.0", "flux/fidelity.json", "flux/spectrum_a1.0"),
        ("SeaCache", "13", "kalsea_flux_idx/reuse_0.6", "kalsea_flux_idx/fidelity.json", "kalsea_flux_idx/reuse_0.6"),
        ("KalSea", "13", "kalsea_flux_idx/kalsea_0.6", "kalsea_flux_idx/fidelity.json", "kalsea_flux_idx/kalsea_0.6")]),
    "flux21": ("nfe21_supp", "21 NFE", [
        ("Reference", "50", "kalsea_flux_idx/ref", None, None),
        ("Fewer steps", "25", "flux/vanilla25", "flux/fidelity.json", "flux/vanilla25"),
        ("TeaCache", "26", "flux/teacache_0.3", "flux/fidelity.json", "flux/teacache_0.3"),
        ("SADA (default)", "24", "flux/sada_default", "flux/fidelity_sada_default.json", "flux/sada_default"),
        ("SADA (faster)", "21.5", "flux/sada_fast", "flux/fidelity_sada_fast.json", "flux/sada_fast"),
        ("SeaCache", "20.9", "kalsea_flux_idx/reuse_0.3", "kalsea_flux_idx/fidelity_0.3.json", "kalsea_flux_idx/reuse_0.3"),
        ("KalSea", "20.8", "kalsea_flux_idx/kalsea_0.3", "kalsea_flux_idx/fidelity_0.3.json", "kalsea_flux_idx/kalsea_0.3")]),
}
VIDEO = {  # model -> (meta tag, columns: (label, nfe label, harness dir))
    "hunyuan": ("video_hunyuan", "HunyuanVideo, 16 NFE", [
        ("Reference", "50", "hy_main/official_ref"), ("Fewer steps", "15", "hy_main/vanilla15"),
        ("TeaCache", "17", "hy_main/teacache0.2"), ("TaylorSeer", "17", "hy_main/taylorseer_s3"),
        ("Spectrum", "16", "hy_main/spectrum16_state0.5"), ("SeaCache", "16", "hy_main/gatecur0.48_copy"),
        ("KalSea", "16", "hy_main/kalsea0.48")]),
    "wan": ("video_wan", "Wan2.1-1.3B, 17 NFE", [
        ("Reference", "50", "wan_main/official_ref"), ("TeaCache", "18", "wan_main/teacache0.15"),
        ("TaylorSeer", "17", "wan_main/taylorseer_s3"), ("Spectrum", "19", "wan_main/spectrum19_state0.5"),
        ("SeaCache", "17", "wan_main/kalsearu0.35"), ("KalSea", "17", "wan_main/kalsea0.35")]),
}


def per_item(json_path, key):
    r = json.load(open(os.path.join(EXP, json_path)))[key]
    return r.get("per_image") or r.get("per_video")


def thumb(arr, width):
    im = Image.fromarray(arr)
    h = round(im.height * width / im.width)
    return np.asarray(im.resize((width, h), Image.LANCZOS))


def flux_figure(tag):
    meta_tag, title, cols = FLUX[tag]
    meta = json.load(open(os.path.join(HERE, "qual_tiles", meta_tag, "meta.json")))
    prompts = meta["prompts"]
    per = [per_item(j, k) if j else None for _, _, _, j, k in cols]
    nc, nr = len(cols), len(prompts)
    tile = TEXTWIDTH / nc
    title_h, psnr_h, head_h = 0.17, 0.11, 0.2
    fig_h = head_h + nr * (title_h + tile + psnr_h)
    fig = plt.figure(figsize=(TEXTWIDTH, fig_h))
    for c, (lab, nfe, _, _, _) in enumerate(cols):
        fig.text((c + 0.5) / nc, 1 - 0.5 * head_h / fig_h, f"{lab} ({nfe})", ha="center", va="center",
                 fontweight="bold" if lab == "KalSea" else "normal")
    y = 1 - head_h / fig_h
    for p in prompts:
        name = f"{int(p['idx']):05d}.png"
        fig.text(0.002, y - 0.5 * title_h / fig_h, "“" + textwrap.shorten(p["prompt"], 150, placeholder="…")
                 + "”", ha="left", va="center", style="italic")
        y -= title_h / fig_h
        for c, (lab, _, d, _, _) in enumerate(cols):
            ax = fig.add_axes([c / nc + 0.002, y - tile / fig_h, 1 / nc - 0.004, tile / fig_h])
            ax.imshow(thumb(np.asarray(Image.open(os.path.join(EXP, d, name)).convert("RGB")), 280), interpolation="none")
            ax.set_axis_off()
            if per[c] is not None:
                fig.text((c + 0.5) / nc, y - (tile + 0.5 * psnr_h) / fig_h, f"{per[c][name]['psnr']:.2f} dB",
                         ha="center", va="center", fontweight="bold" if lab == "KalSea" else "normal")
        y -= (tile + psnr_h) / fig_h
    out = os.path.join(FIG, f"fig_baselines_{tag}.pdf")
    fig.savefig(out, dpi=250)
    plt.close(fig)
    return out, meta, prompts


def frames(path, idx):
    out = {}
    for i, f in enumerate(iio.imiter(path)):
        if i in idx:
            out[i] = f
        if i >= max(idx):
            break
    return [out[i] for i in idx]


def video_figure(model):
    meta_tag, title, cols = VIDEO[model]
    meta = json.load(open(os.path.join(HERE, "qual_tiles", meta_tag, "meta.json")))
    fidx = meta["frames"]
    prompts = sorted(meta["prompts"], key=lambda p: -float(p["quantile"]))
    plist = [l.strip() for l in open(os.path.join(EXP, "vbench944.txt"), encoding="utf-8") if l.strip()]
    nf, nv, nm = len(fidx), len(prompts), len(cols)
    label_w = 0.95
    tile_w = (TEXTWIDTH - label_w) / (nf * nv) - 0.01
    sample = frames(os.path.join(EXP, cols[0][2], f"{plist[int(prompts[0]['idx'])]}-0.mp4"), [0])[0]
    tile_h = tile_w * sample.shape[0] / sample.shape[1]
    head_h, row_gap = 0.34, 0.03
    fig_h = head_h + nm * (tile_h + row_gap)
    fig = plt.figure(figsize=(TEXTWIDTH, fig_h))
    gap = 0.06
    for v, p in enumerate(prompts):
        x0 = label_w / TEXTWIDTH + v * (nf * tile_w + gap) / TEXTWIDTH
        fig.text(x0 + nf * tile_w / TEXTWIDTH / 2, 1 - 0.1 / fig_h,
                 "“" + textwrap.shorten(p["prompt"], 70, placeholder="…") + "”", ha="center", va="center",
                 style="italic")
        for j, fr in enumerate(fidx):
            fig.text(x0 + (j + 0.5) * tile_w / TEXTWIDTH, 1 - 0.26 / fig_h, f"frame {fr}", ha="center", va="center",
                     color="0.35")
    y = 1 - head_h / fig_h
    for lab, nfe, d in cols:
        psnrs = []
        for v, p in enumerate(prompts):
            name = f"{plist[int(p['idx'])]}-0.mp4"
            fr = frames(os.path.join(EXP, d, name), fidx)
            x0 = label_w / TEXTWIDTH + v * (nf * tile_w + gap) / TEXTWIDTH
            for j, f in enumerate(fr):
                ax = fig.add_axes([x0 + j * tile_w / TEXTWIDTH, y - tile_h / fig_h, (tile_w - 0.01) / TEXTWIDTH,
                                   tile_h / fig_h])
                ax.imshow(thumb(f, 190), interpolation="none")
                ax.set_axis_off()
            if lab != "Reference":
                psnrs.append(per_item(os.path.join(d, "fidelity.json"), d)[name]["psnr"])
        txt = f"{lab} ({nfe})" + ("" if not psnrs else "\n" + " / ".join(f"{q:.1f}" for q in psnrs) + " dB")
        fig.text(0.004, y - 0.5 * tile_h / fig_h, txt, ha="left", va="center",
                 fontweight="bold" if lab == "KalSea" else "normal")
        y -= (tile_h + row_gap) / fig_h
    out = os.path.join(FIG, f"fig_baselines_{model}.pdf")
    fig.savefig(out, dpi=300)
    plt.close(fig)
    return out, meta, prompts


def write_caption(tag, text):
    open(os.path.join(FIG, f"fig_baselines_{tag}_caption.tex"), "w").write(
        "% Auto-generated by figures/src/fig_baselines.py.\n" + text + "\n")


def main():
    for tag in ("flux13", "flux21"):
        out, meta, prompts = flux_figure(tag)
        d, nfe, n_id, n = meta["delta"], meta["nfe"], meta["rule"]["n_identical_steps"], meta["rule"]["n_total"]
        write_caption(tag, (
            rf"\caption{{\textbf{{All baselines at {FLUX[tag][1].replace('NFE', r'\nfe')}}} (\flux, DrawBench), on the prompts of "
            rf"\cref{{fig:qualitative-supp-{'nfe13' if tag == 'flux13' else 'nfe21'}}}, selected by the same fixed rule (quantiles of"
            rf" the PSNR gain of \ours over \seacache among the {n_id} of {n} prompts with identical steps), not by the"
            r" baselines. \nfe in parentheses; PSNR w.r.t.\ the 50-step output under each panel. "
            + ("TeaCache, TaylorSeer (order 2), Spectrum and fewer steps" if tag == "flux13" else "TeaCache, SADA and fewer steps")
            + r": released code, same prompts and seeds.}"
            rf"\label{{fig:baselines-{tag}}}"))
        print("wrote", out)
    for model in ("hunyuan", "wan"):
        out, meta, prompts = video_figure(model)
        write_caption(model, (
            rf"\caption{{\textbf{{All baselines, {VIDEO[model][1].replace('NFE', r'\nfe')}}} (VBench prompts, frames"
            rf" {', '.join(map(str, meta['frames']))} of 65), on the two videos of"
            rf" \cref{{fig:video-examples-{model}}}, selected by its fixed rule (upper-quartile and median PSNR gain of \ours"
            r" over \seacache). \nfe in parentheses; next to each method, the per-video PSNR w.r.t.\ the 50-step output for"
            r" the two videos. Fewer steps, TeaCache and TaylorSeer (default order 1 of its forks): released code;"
            r" Spectrum: our implementation; same prompts and seed.}"
            rf"\label{{fig:baselines-{model}}}"))
        print("wrote", out)


if __name__ == "__main__":
    main()
