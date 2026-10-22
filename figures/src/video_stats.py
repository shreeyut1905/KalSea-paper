#!/usr/bin/env python3
"""Collect the video results used by the tables into data/video_stats.json (keyed by model / budget / method, no paths).

    python video_stats.py      -> data/video_stats.json

Reads the full-reference evaluations listed in data_sources.VIDEO_FR. A model whose evaluation file does not exist yet
is written as null, and make_tables.py prints \\tbd for it.
"""
import json
import os

import data_sources as DS

HERE = os.path.dirname(os.path.abspath(__file__))


def pick(s):
    return {"n": s["n"], "nfe": s["nfe"], "psnr": s["psnr"], "ssim": s["ssim"], "lpips": s["lpips"]}


def main():
    out = {}
    for model, budgets in DS.VIDEO_RUNS.items():
        path = DS.VIDEO_FR.get(model)
        if not path or not os.path.exists(path):
            out[model] = None
            print(f"{model}: no evaluation yet ({path})")
            continue
        R = json.load(open(path))
        out[model] = {}
        for b, (delta, ours, sea) in budgets.items():
            S = R["summary"]
            assert S[ours]["n"] == S[sea]["n"] == 944, (model, b, S[ours]["n"], S[sea]["n"])
            out[model][b] = {"delta": delta, "ours": pick(S[ours]), "seacache_rerun": pick(S[sea]),
                             "ours_minus_seacache_rerun": R["pairs"][f"{ours}-{sea}"]}
            print(f"{model} {b}: delta {delta}, Ours {S[ours]['psnr']:.2f} dB at {S[ours]['nfe']:.2f} NFE")
    json.dump(out, open(os.path.join(HERE, "data", "video_stats.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
