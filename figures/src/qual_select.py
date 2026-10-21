#!/usr/bin/env python3
"""Select the prompts and zoom windows for the qualitative figure by a fixed, stated rule, and export the image tiles.

Prompt rule (no hand-picking): among the DrawBench-200 prompts on which SeaCache, KalSea and Ours computed the identical
set of steps at the given threshold delta (so all three spend exactly the same transformer evaluations), take the
per-prompt PSNR gain g = PSNR(Ours) - PSNR(SeaCache) w.r.t. the 50-step reference, and for each target quantile of g
(default: median and upper quartile) select the K prompts whose g is closest to that quantile.

Zoom rule (no hand-placement): a fixed WxH-pixel window (default 256x128 of the 1024x1024 image) placed where the three
accelerated outputs disagree most: argmax over window positions (stride 8 px) of the window mean of
D = mean(|SeaCache - KalSea|, |SeaCache - Ours|, |KalSea - Ours|) (absolute RGB difference, averaged over channels).
The reference is not used to place the window.

Exports JPEG tiles (quality 92, 4:4:4): full images downscaled with Lanczos to --full_px, crops at native resolution.
Writes qual_tiles/<tag>/meta.json used by fig_qualitative.py.

    python qual_select.py --delta 0.6 --quantiles 50 75 --k 2 --tag nfe13
"""
import argparse
import glob
import json
import os

import numpy as np
from PIL import Image

import data_sources as DS

HERE = os.path.dirname(os.path.abspath(__file__))
METHODS = ("seacache", "kalsea", "ours")


def load_per_image():
    per = {}
    for f in sorted(glob.glob(os.path.join(DS.EVAL_DIR, "eval_*.json"))):
        for run, p in json.load(open(f))["per_image"].items():
            per.setdefault(run, p)
    return per


def prompts_from_stats(run_dir):
    out = {}
    for f in glob.glob(os.path.join(run_dir, "stats_shard*.jsonl")):
        for line in open(f):
            line = line.strip()
            if line:
                r = json.loads(line)
                out[r["file"]] = (r["idx"], r["prompt"])
    return out


def window_argmax(D, ww, wh, stride):
    H, W = D.shape
    I = np.zeros((H + 1, W + 1), dtype=np.float64)
    I[1:, 1:] = D.cumsum(0).cumsum(1)
    best, arg = -1.0, (0, 0)
    for y in range(0, H - wh + 1, stride):
        s = I[y + wh, ww:] - I[y, ww:] - I[y + wh, :-ww] + I[y, :-ww]   # sums for x = 0..W-ww
        s = s[::stride]
        j = int(np.argmax(s))
        if s[j] > best:
            best, arg = float(s[j]), (j * stride, y)
    return arg, best / (ww * wh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delta", default="0.6")
    ap.add_argument("--quantiles", type=float, nargs="+", default=[50, 75])
    ap.add_argument("--k", type=int, default=2)
    ap.add_argument("--win", type=int, nargs=2, default=[256, 128], help="window width height (px)")
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--full_px", type=int, default=400)
    ap.add_argument("--tag", default="nfe13")
    a = ap.parse_args()
    d = a.delta
    per = load_per_image()
    P = {m: per[DS.MAIN[m].format(d=d)] for m in METHODS}
    img_dir = {"reference": DS.run_dir(DS.REF_RUN), **{m: DS.run_dir(DS.MAIN[m].format(d=d)) for m in METHODS}}
    files = sorted(P["ours"])
    same = [f for f in files if P["ours"][f]["compute_steps"] == P["seacache"][f]["compute_steps"] == P["kalsea"][f]["compute_steps"]]
    g = np.array([P["ours"][f]["psnr"] - P["seacache"][f]["psnr"] for f in same])
    prompts = prompts_from_stats(img_dir["reference"])
    out_dir = os.path.join(HERE, "qual_tiles", a.tag)
    os.makedirs(out_dir, exist_ok=True)

    chosen, used = [], set()
    for q in a.quantiles:
        t = float(np.percentile(g, q))
        order = np.argsort(np.abs(g - t), kind="stable")
        picked = []
        for i in order:
            if same[i] not in used:
                picked.append(int(i))
                used.add(same[i])
            if len(picked) == a.k:
                break
        for i in picked:
            chosen.append(dict(file=same[i], quantile=q, target=t, gain=float(g[i])))

    ww, wh = a.win
    for c in chosen:
        f = c["file"]
        imgs = {m: np.asarray(Image.open(os.path.join(img_dir[m], f)).convert("RGB")) for m in ("reference",) + METHODS}
        A = {m: imgs[m].astype(np.float32) for m in METHODS}
        D = (np.abs(A["seacache"] - A["kalsea"]) + np.abs(A["seacache"] - A["ours"]) + np.abs(A["kalsea"] - A["ours"])).mean(2) / 3
        (x0, y0), score = window_argmax(D, ww, wh, a.stride)
        idx, prompt = prompts[f]
        c.update(idx=idx, prompt=prompt, window=[x0, y0, ww, wh], window_disagreement=score,
                 size=list(imgs["reference"].shape[1::-1]), n_same_steps=len(same),
                 compute_steps=P["ours"][f]["compute_steps"], nfe=P["ours"][f]["nfe"],
                 psnr={m: P[m][f]["psnr"] for m in METHODS}, ssim={m: P[m][f]["ssim"] for m in METHODS},
                 lpips={m: P[m][f]["lpips"] for m in METHODS}, tiles={})
        for m in ("reference",) + METHODS:
            im = Image.fromarray(imgs[m])
            full = im.resize((a.full_px, a.full_px), Image.LANCZOS)
            crop = im.crop((x0, y0, x0 + ww, y0 + wh))
            fn_full = f"{idx:03d}_{m}_full.jpg"
            fn_crop = f"{idx:03d}_{m}_crop.jpg"
            full.save(os.path.join(out_dir, fn_full), quality=92, subsampling=0, optimize=True)
            crop.save(os.path.join(out_dir, fn_crop), quality=92, subsampling=0, optimize=True)
            c["tiles"][m] = dict(full=fn_full, crop=fn_crop)
        print(f"q{c['quantile']:.0f} target {c['target']:+.3f}  {idx:3d} gain {c['gain']:+.3f}  window {x0},{y0} "
              f"(D={score:.1f})  PSNR S {c['psnr']['seacache']:.2f} K {c['psnr']['kalsea']:.2f} O {c['psnr']['ours']:.2f}  {prompt}")
    for c in chosen:
        c.pop("file", None)          # internal file name; idx + prompt identify the image
    meta = dict(delta=d, rule=dict(quantiles=a.quantiles, k=a.k, window=[ww, wh], stride=a.stride,
                                   n_identical_steps=len(same), n_total=len(files),
                                   gain_quantiles={str(q): float(np.percentile(g, q)) for q in (25, 50, 75)}),
                nfe=float(np.mean([P["ours"][f]["nfe"] for f in files])), prompts=chosen)
    json.dump(meta, open(os.path.join(out_dir, "meta.json"), "w"), indent=1)
    print("wrote", out_dir)


if __name__ == "__main__":
    main()
