#!/usr/bin/env python3
"""Collect the FLUX.1-dev baselines of Tab. 1 into data/flux_baselines.json (for the markers of fig_tradeoff).

Source: /home/ubuntu/exp/flux/fidelity*.json (metrics.py: per-image PSNR / SSIM / LPIPS against the uncached 50-step
output of the same code; DrawBench-200, seed = prompt index, one B200). These are the runs behind the baseline rows of
Tab. 1 (make_tables.py MEASURED_BL): TeaCache, fewer steps, TaylorSeer (order 2), Spectrum and SADA, each at two
budgets. Mean over prompts and 95% bootstrap CI of the mean (2000 resamples, seed 0). No new generation is run.
Run: python collect_flux_baselines.py
"""
import json
import os

import numpy as np

EXP = "/home/ubuntu/exp/flux"
HERE = os.path.dirname(os.path.abspath(__file__))
# method -> list of (file, key, setting label), lower budget first
CONFIGS = {
    "teacache": [("fidelity.json", "flux/teacache_0.6", r"$\delta{=}0.6$"), ("fidelity.json", "flux/teacache_0.3", r"$\delta{=}0.3$")],
    "vanilla": [("fidelity.json", "flux/vanilla15", "15 steps"), ("fidelity.json", "flux/vanilla25", "25 steps")],
    "taylorseer": [("fidelity_taylorseer_o2.json", "flux/taylorseer_n5_o2", r"$S{=}5$"),
                   ("fidelity_taylorseer_o2.json", "flux/taylorseer_n3_o2", r"$S{=}3$")],
    "spectrum": [("fidelity.json", "flux/spectrum_a1.0", r"$\alpha{=}1.0$"), ("fidelity.json", "flux/spectrum_a0.3", r"$\alpha{=}0.3$")],
    "sada": [("fidelity_sada_fast.json", "flux/sada_fast", "faster"), ("fidelity_sada_default.json", "flux/sada_default", "default")],
}


def mean_ci(v, rng, n=2000):
    v = np.asarray(v, dtype=np.float64)
    boot = v[rng.integers(0, len(v), size=(n, len(v)))].mean(axis=1)
    return {"mean": float(v.mean()), "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]}


def main():
    rng = np.random.default_rng(0)
    out = {"what": __doc__.strip().splitlines()[0], "source": EXP, "methods": {}}
    for m, rows in CONFIGS.items():
        out["methods"][m] = []
        for f, key, setting in rows:
            r = json.load(open(os.path.join(EXP, f)))[key]
            per = list(r["per_image"].values())
            out["methods"][m].append({"config": key, "setting": setting, "n": len(per), "nfe": r["nfe"],
                                      "psnr": mean_ci([p["psnr"] for p in per], rng),
                                      "lpips": mean_ci([p["lpips"] for p in per], rng)})
            e = out["methods"][m][-1]
            print(f"{m:10s} {key:26s} n={e['n']} nfe={e['nfe']:5.2f} psnr={e['psnr']['mean']:.2f} lpips={e['lpips']['mean']:.3f}")
    json.dump(out, open(os.path.join(HERE, "data", "flux_baselines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
