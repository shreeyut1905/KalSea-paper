#!/usr/bin/env python3
"""Aggregate the FLUX.1-dev DrawBench-200 per-image metrics into one stats file used by the figures and tables.

Input : eval_*.json of the evaluation harness (per-image PSNR/SSIM/LPIPS w.r.t. the 50-step reference, NFE and the
        list of computed steps); locations in data_sources.py.
Output: data/flux_drawbench_stats.json, keyed by method and threshold delta (no paths, no internal run names).

Statistics follow the evaluation harness exactly: 95% CI = percentile bootstrap over the 200 prompts, 10,000
resamples, numpy default_rng(seed=0) resampling indices (identical for every quantity with the same n). Paired
differences therefore reproduce the harness's reported CIs (e.g. Ours - SeaCache at delta=0.3: +2.725 [+2.335, +3.124]).
"""
import glob
import json
import os

import numpy as np

import data_sources as D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "flux_drawbench_stats.json")
N_BOOT, SEED = 10000, 0
METRICS = ("psnr", "ssim", "lpips")


def load_per_image():
    per = {}
    for f in sorted(glob.glob(os.path.join(D.EVAL_DIR, "eval_*.json"))):
        d = json.load(open(f))
        for run, p in d["per_image"].items():
            if run in per:  # the same run evaluated in several files must agree exactly
                a = per[run]
                assert set(a) == set(p), (run, f)
                for k in a:
                    for m in METRICS + ("nfe",):
                        assert a[k][m] == p[k][m], (run, k, m, f)
            else:
                per[run] = p
    return per


def boot_ci(x, n_boot=N_BOOT, seed=SEED):
    x = np.asarray(x, dtype=np.float64)
    idx = np.random.default_rng(seed).integers(0, len(x), size=(n_boot, len(x)))
    lo, hi = np.percentile(x[idx].mean(1), [2.5, 97.5])
    return [float(lo), float(hi)]


def run_summary(p):
    files = sorted(p)
    nfe = [p[f]["nfe"] for f in files]
    out = {"n": len(files), "nfe": float(np.mean(nfe)), "nfe_min": float(np.min(nfe)), "nfe_max": float(np.max(nfe))}
    for m in METRICS:
        v = np.array([p[f][m] for f in files], dtype=np.float64)
        assert np.all(np.isfinite(v))
        out[m] = {"mean": float(v.mean()), "ci95": boot_ci(v), "median": float(np.median(v)),
                  "q25": float(np.percentile(v, 25)), "q75": float(np.percentile(v, 75))}
    return out


def paired(pa, pb):
    """Per-prompt difference a - b over the common prompts."""
    files = sorted(set(pa) & set(pb))
    rec = {"n": len(files),
           "dnfe": float(np.mean([pa[f]["nfe"] for f in files]) - np.mean([pb[f]["nfe"] for f in files])),
           "n_same_steps": int(sum(pa[f].get("compute_steps") == pb[f].get("compute_steps") for f in files))}
    for m, better in (("psnr", 1), ("ssim", 1), ("lpips", -1)):
        d = np.array([pa[f][m] - pb[f][m] for f in files], dtype=np.float64)
        rec[m] = {"mean": float(d.mean()), "ci95": boot_ci(d), "frac_better": float((better * d > 0).mean())}
    return rec


def main():
    per = load_per_image()
    st = {"what": "FLUX.1-dev, DrawBench-200 (held out), 1024^2, 50 steps, guidance 3.5, seed = prompt index; metrics "
                  "w.r.t. the 50-step reference (PSNR/SSIM: skimage, data_range 255; LPIPS: AlexNet)",
          "bootstrap": {"n_boot": N_BOOT, "seed": SEED, "ci": "percentile 95%, over prompts"},
          "deltas": D.DELTAS, "summary": {}, "paired": {}, "ablation_2x2": {}}
    for d in D.DELTAS:
        P = {m: per[D.MAIN[m].format(d=d)] for m in D.MAIN}
        st["summary"][d] = {m: run_summary(P[m]) for m in D.MAIN}
        st["paired"][d] = {"ours-seacache": paired(P["ours"], P["seacache"]),
                           "ours-kalsea": paired(P["ours"], P["kalsea"]),
                           "kalsea-seacache": paired(P["kalsea"], P["seacache"])}
    for d in D.ABL_DELTAS:
        P = {f"{fc}_{sm}": per[D.ABL[(fc, sm)].format(d=d)] for (fc, sm) in D.ABL}
        st["ablation_2x2"][d] = {"summary": {k: run_summary(v) for k, v in P.items()},
                                 "dct_on-dct_off": paired(P["dct_on"], P["dct_off"]),
                                 "elem_on-elem_off": paired(P["elem_on"], P["elem_off"]),
                                 "dct_on-elem_on": paired(P["dct_on"], P["elem_on"]),
                                 "dct_off-elem_off": paired(P["dct_off"], P["elem_off"])}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(st, open(OUT, "w"), indent=1)

    print(f"{'delta':>5} {'method':>9} {'NFE':>6} {'PSNR':>6} {'95% CI':>15} {'SSIM':>6} {'LPIPS':>6}")
    for d in D.DELTAS:
        for m in ("seacache", "kalsea", "ours"):
            s = st["summary"][d][m]
            print(f"{d:>5} {m:>9} {s['nfe']:6.2f} {s['psnr']['mean']:6.2f} [{s['psnr']['ci95'][0]:5.2f},{s['psnr']['ci95'][1]:5.2f}]"
                  f" {s['ssim']['mean']:.4f} {s['lpips']['mean']:.4f}")
        for pk in ("ours-seacache", "ours-kalsea"):
            p = st["paired"][d][pk]
            print(f"      {pk:>15}: dPSNR {p['psnr']['mean']:+.3f} [{p['psnr']['ci95'][0]:+.3f},{p['psnr']['ci95'][1]:+.3f}] "
                  f"win {p['psnr']['frac_better']:.2f}  dLPIPS {p['lpips']['mean']:+.4f}  same-steps {p['n_same_steps']}")
    for d in D.ABL_DELTAS:
        a = st["ablation_2x2"][d]
        for k, s in a["summary"].items():
            print(f"2x2 {d:>4} {k:9s} NFE {s['nfe']:.2f} PSNR {s['psnr']['mean']:.3f} SSIM {s['ssim']['mean']:.4f} LPIPS {s['lpips']['mean']:.4f}")
        for pk in ("dct_on-dct_off", "elem_on-elem_off", "dct_on-elem_on", "dct_off-elem_off"):
            p = a[pk]
            print(f"    {pk:17s} dPSNR {p['psnr']['mean']:+.3f} [{p['psnr']['ci95'][0]:+.3f},{p['psnr']['ci95'][1]:+.3f}] "
                  f"dLPIPS {p['lpips']['mean']:+.4f} [{p['lpips']['ci95'][0]:+.4f},{p['lpips']['ci95'][1]:+.4f}]")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
