#!/usr/bin/env python3
"""Select the video examples (HunyuanVideo, Wan2.1) by a fixed rule, verify the regenerated videos, export frame tiles.

Prompt rule (no hand-picking; same rule as qual_select.py for FLUX.1-dev): at the lower video budget of the paper
(VIDEO_RUNS[model]["lo"]: HunyuanVideo delta 0.48 / 16 NFE, Wan2.1 delta 0.35 / 17 NFE), among the 944 VBench prompts on
which SeaCache and KalSea computed the identical set of steps, take the per-video PSNR gain g = PSNR(KalSea) - PSNR(SeaCache)
w.r.t. the 50-step reference (from the evaluation file) and pick the prompt whose g is closest to each target quantile of
g: the upper quartile (main paper; also used in the supplement) and the median (supplement).

    python video_qual_select.py select   -> qual_tiles/video_<model>/selection.json (+ index lists for regeneration)
    python video_qual_select.py export   -> verifies the regenerated MP4s (frame checksum = the one recorded for the
                                            deleted video; per-video PSNR recomputed from the decoded frames = the
                                            evaluation file), writes lossless PNG frames next to the MP4s and the JPEG
                                            tiles + meta.json used by fig_qual_models.py / fig_qual_video_supp.py

Frames are decoded exactly as in the evaluation (ffmpeg -pix_fmt rgb24 rawvideo; the binary named in the evaluation file).
"""
import argparse
import glob
import json
import os
import subprocess

import numpy as np
from PIL import Image

import data_sources as DS
from qual_select import window_argmax

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = ("hunyuan", "wan")
QUANTILES = (75.0, 50.0)          # first = main-paper example
FRAMES = (0, 16, 32, 48, 64)      # supplement strips (65 frames)
MAIN_FRAME = 32                   # main-paper panel: the middle frame of the 65
METHODS = ("seacache", "ours")


def load_stats(pattern):
    out = {}
    for f in sorted(glob.glob(pattern)):
        for line in open(f):
            line = line.strip()
            if line:
                r = json.loads(line)
                out[os.path.basename(r["file"])] = r
    return out


def steps(r):
    c = r["cache"]
    if "compute_steps" in c:                                  # HunyuanVideo (one stream)
        return tuple(c["compute_steps"])
    return tuple(c["hook_compute_steps_cond"]), tuple(c["hook_compute_steps_uncond"])   # Wan2.1 (cond, uncond)


def nfe(r):
    c = r["cache"]
    return c["nfe"] if "nfe" in c else c["nfe_steps"]


def runs(model):
    delta, ours, sea, *fr = DS.VIDEO_RUNS[model]["lo"]
    return delta, {"ours": ours, "seacache": sea}, (fr[0] if fr else DS.VIDEO_FR[model])


def select():
    for model in MODELS:
        delta, cfg, fr_path = runs(model)
        E = json.load(open(fr_path))["per_video"]
        S = {m: load_stats(os.path.join(DS.VIDEO_ROOT[model], cfg[m] + "_meta", "stats", "*.jsonl")) for m in METHODS}
        files = sorted(E[cfg["ours"]])
        assert len(files) == 944 and set(files) == set(E[cfg["seacache"]]) == set(S["ours"]) == set(S["seacache"])
        same = [f for f in files if steps(S["ours"][f]) == steps(S["seacache"][f])]
        g = np.array([E[cfg["ours"]][f]["psnr"] - E[cfg["seacache"]][f]["psnr"] for f in same])
        chosen = []
        for q in QUANTILES:
            t = float(np.percentile(g, q))
            i = int(np.argsort(np.abs(g - t), kind="stable")[0])
            f = same[i]
            chosen.append(dict(quantile=q, target=t, gain=float(g[i]), file=f, idx=S["ours"][f]["idx"],
                               prompt=S["ours"][f]["prompt"], nfe=nfe(S["ours"][f]),
                               compute_steps=steps(S["ours"][f]),
                               psnr={m: E[cfg[m]][f]["psnr"] for m in METHODS},
                               ssim={m: E[cfg[m]][f]["ssim"] for m in METHODS},
                               lpips={m: E[cfg[m]][f]["lpips"] for m in METHODS}))
            print(f"{model} q{q:.0f} target {t:+.3f}: idx {chosen[-1]['idx']} gain {g[i]:+.3f} "
                  f"S {chosen[-1]['psnr']['seacache']:.2f} O {chosen[-1]['psnr']['ours']:.2f}  {chosen[-1]['prompt']}")
        out = os.path.join(HERE, "qual_tiles", f"video_{model}")
        os.makedirs(out, exist_ok=True)
        sel = dict(model=model, delta=delta, n_identical_steps=len(same), n_total=len(files),
                   nfe=float(np.mean([nfe(S["ours"][f]) for f in files])),
                   gain_quantiles={str(q): float(np.percentile(g, q)) for q in (25, 50, 75)},
                   frames=list(FRAMES), prompts=chosen)
        json.dump(sel, open(os.path.join(out, "selection.json"), "w"), indent=1)
        # unique prompt indices to regenerate (internal work folder, not part of the figure data)
        os.makedirs(os.path.join(DS.VIDEO_QUAL_DIR, model), exist_ok=True)
        idx = sorted({c["idx"] for c in chosen})
        open(os.path.join(DS.VIDEO_QUAL_DIR, model, "indices.txt"), "w").write("".join(f"{i}\n" for i in idx))
        print(f"{model}: delta {delta}, {len(same)}/{len(files)} prompts with identical steps, regenerate {idx}")


def decode(path, ffmpeg, hw):
    """the evaluation's decode command (ffmpeg -i <mp4> -pix_fmt rgb24 -vcodec rawvideo -f image2pipe -), same binary"""
    raw = subprocess.run([ffmpeg, "-v", "error", "-i", path, "-pix_fmt", "rgb24", "-vcodec", "rawvideo",
                          "-f", "image2pipe", "-"], check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, hw[0], hw[1], 3)


def psnr_frames(a, b):
    """skimage peak_signal_noise_ratio(data_range=255) per frame (float64 MSE), capped at 100 dB as in the evaluation"""
    out = []
    for x, y in zip(a, b):
        mse = np.mean((x.astype(np.float64) - y.astype(np.float64)) ** 2)
        out.append(100.0 if mse == 0 else min(100.0, float(10 * np.log10(255.0 ** 2 / mse))))
    return out


def export(full_px):
    report = {}
    for model in MODELS:
        out = os.path.join(HERE, "qual_tiles", f"video_{model}")
        sel = json.load(open(os.path.join(out, "selection.json")))
        delta, cfg, fr_path = runs(model)
        EV = json.load(open(fr_path))
        E, ffmpeg = EV["per_video"], EV["meta"]["ffmpeg"]
        S = {m: load_stats(os.path.join(DS.VIDEO_ROOT[model], cfg[m] + "_meta", "stats", "*.jsonl")) for m in METHODS}
        S["reference"] = load_stats(DS.VIDEO_REF_STATS[model])
        work = os.path.join(DS.VIDEO_QUAL_DIR, model)
        key = "frames_sha1" if model == "hunyuan" else "frames_md5"
        report[model] = []
        for c in sel["prompts"]:
            f = c["file"]
            frames, chk = {}, {}
            for m in ("reference",) + METHODS:
                mp4 = os.path.join(work, m, f)
                new = load_stats(os.path.join(work, m + "_meta", "stats", "*.jsonl")).get(f, {})
                rec_old = S[m][f][key]
                rec_new = new.get(key)          # recorded by the driver for the regenerated video, same procedure
                hw = (new["height"], new["width"]) if model == "hunyuan" else tuple(new["frame_hw"])
                frames[m] = decode(mp4, ffmpeg, hw)
                chk[m] = dict(recorded=rec_old, regenerated=rec_new, match=rec_old == rec_new,
                              compute_steps_match=(m == "reference" or steps(new) == steps(S[m][f])) if new else None)
            ps = {m: psnr_frames(frames[m], frames["reference"]) for m in METHODS}
            for m in METHODS:
                p_new = float(np.mean(ps[m]))
                p_old = E[cfg[m]][f]["psnr"]
                chk[m].update(psnr_recomputed=p_new, psnr_eval=p_old, psnr_abs_diff=abs(p_new - p_old),
                              psnr_frames_max_abs_diff=float(np.max(np.abs(np.round(ps[m], 4) -
                                                                           np.array(E[cfg[m]][f]["psnr_frames"])))))
            report[model].append(dict(idx=c["idx"], quantile=c["quantile"], checks=chk))
            ok = all(chk[m]["match"] for m in chk) and all(chk[m]["psnr_abs_diff"] < 1e-6 for m in METHODS)
            print(f"{model} idx {c['idx']} q{c['quantile']:.0f}: {'OK' if ok else 'MISMATCH'}  " +
                  "  ".join(f"{m}: chk {chk[m]['match']}" + (f" psnr {chk[m]['psnr_recomputed']:.4f}/{chk[m]['psnr_eval']:.4f}"
                                                             if m in METHODS else "") for m in chk))
            # lossless frames (kept next to the MP4s) and JPEG tiles for the figures
            c["tiles"] = {}
            for m in ("reference",) + METHODS:
                png_dir = os.path.join(work, "frames", f"{c['idx']:03d}_{m}")
                os.makedirs(png_dir, exist_ok=True)
                c["tiles"][m] = {}
                for k in FRAMES:
                    im = Image.fromarray(frames[m][k])
                    im.save(os.path.join(png_dir, f"frame{k:02d}.png"))
                    t = im.resize((full_px, round(full_px * im.height / im.width)), Image.LANCZOS)
                    fn = f"{c['idx']:03d}_{m}_f{k:02d}.jpg"
                    t.save(os.path.join(out, fn), quality=92, subsampling=0, optimize=True)
                    c["tiles"][m][str(k)] = fn
            # zoom window on the main-paper frame, same rule as qual_select.py for FLUX.1-dev (window = 1/4 x 1/8 of the
            # frame width, stride 8 px, where SeaCache and KalSea disagree most; the reference is not used)
            W = frames["reference"].shape[2]
            ww, wh = W // 4, W // 8
            D = np.abs(frames["seacache"][MAIN_FRAME].astype(np.float32) -
                       frames["ours"][MAIN_FRAME].astype(np.float32)).mean(2)
            (x0, y0), score = window_argmax(D, ww, wh, 8)
            c["window"], c["window_disagreement"], c["main_frame"] = [x0, y0, ww, wh], score, MAIN_FRAME
            for m in ("reference",) + METHODS:
                fn = f"{c['idx']:03d}_{m}_f{MAIN_FRAME:02d}_crop.jpg"
                Image.fromarray(frames[m][MAIN_FRAME]).crop((x0, y0, x0 + ww, y0 + wh)).save(
                    os.path.join(out, fn), quality=92, subsampling=0, optimize=True)
                c["tiles"][m]["crop"] = fn
            c["psnr_frames"] = {m: [float(ps[m][k]) for k in FRAMES] for m in METHODS}
            c["size"] = [int(frames["reference"].shape[2]), int(frames["reference"].shape[1])]
        meta = {k: v for k, v in sel.items() if k != "prompts"}
        meta["prompts"] = [{k: v for k, v in c.items() if k != "file"} for c in sel["prompts"]]
        json.dump(meta, open(os.path.join(out, "meta.json"), "w"), indent=1)
    json.dump(report, open(os.path.join(DS.VIDEO_QUAL_DIR, "reproduction_checks.json"), "w"), indent=1)
    print("wrote", os.path.join(DS.VIDEO_QUAL_DIR, "reproduction_checks.json"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["select", "export"])
    ap.add_argument("--full_px", type=int, default=480, help="tile width (px) of the exported JPEG frames")
    a = ap.parse_args()
    select() if a.phase == "select" else export(a.full_px)


if __name__ == "__main__":
    main()
