#!/usr/bin/env python3
"""Collect the video baselines measured in the shared harness into data/video_measured.json.

Source: /home/ubuntu/exp/{wan_main,hy_main}/<config>/fidelity.json (metrics_video.py: per-frame PSNR / SSIM / LPIPS
against the uncached 50-step video of the same prompt and seed 42, mean over the 944 unique VBench prompts) and
/home/ubuntu/exp/vbench/<root>/<config>_eval_results.json (official VBench, all 16 dimensions, standard prompt suite;
Total / Quality / Semantic with VBench's official weights and normalization, scripts/constant.py of VBench).
Same official repositories, resolution, frames, steps and seed as KalSea; the KalSea rows of this harness reproduce
data/video_stats.json exactly. Run: python collect_video_measured.py
"""
import glob
import json
import os
import sys

EXP = "/home/ubuntu/exp"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/home/ubuntu/refs/VBench/scripts")
from constant import DIM_WEIGHT, NORMALIZE_DIC, QUALITY_LIST, QUALITY_WEIGHT, SEMANTIC_LIST, SEMANTIC_WEIGHT  # noqa: E402

CONFIGS = {  # model -> budget -> row key -> (harness root, config, setting label)
    "hunyuan": {
        "ref": {"ref": ("hy_main", "official_ref", "50 steps")},
        "hi": {"vanilla": ("hy_main", "vanilla25", "25 steps"), "teacache": ("hy_main", "teacache0.12", r"$\delta{=}0.12$"),
               "taylorseer": ("hy_main", "taylorseer_s2", r"$S{=}2$"), "spectrum": ("hy_main", "spectrum23_state0.5", r"$\alpha$ for 23 steps"),
               "seacache": ("hy_main", "kalsearu0.2575", r"$\delta{=}0.2575$"), "ours": ("hy_main", "kalsea0.2575", r"$\delta{=}0.2575$")},
        "lo": {"vanilla": ("hy_main", "vanilla15", "15 steps"), "teacache": ("hy_main", "teacache0.2", r"$\delta{=}0.2$"),
               "taylorseer": ("hy_main", "taylorseer_s3", r"$S{=}3$"), "spectrum": ("hy_main", "spectrum16_state0.5", r"$\alpha$ for 16 steps"),
               "seacache": ("hy_main", "gatecur0.48_copy", r"$\delta{=}0.48$"), "ours": ("hy_main", "kalsea0.48", r"$\delta{=}0.48$")},
    },
    "wan": {
        "ref": {"ref": ("wan_main", "official_ref", "50 steps")},
        "hi": {"vanilla": ("wan_main", "vanilla25", "25 steps"), "teacache": ("wan_main", "teacache0.09", r"$\delta{=}0.09$"), "taylorseer": ("wan_main", "taylorseer_s2", r"$S{=}2$"),
               "spectrum": ("wan_main", "spectrum27_state0.5", r"$\alpha$ for 27 steps"),
               "seacache": ("wan_main", "kalsearu0.2", r"$\delta{=}0.2$"), "ours": ("wan_main", "kalsea0.2", r"$\delta{=}0.2$")},
        "lo": {"vanilla": ("wan_main", "vanilla15", "15 steps"), "teacache": ("wan_main", "teacache0.15", r"$\delta{=}0.15$"), "taylorseer": ("wan_main", "taylorseer_s3", r"$S{=}3$"),
               "spectrum": ("wan_main", "spectrum19_state0.5", r"$\alpha$ for 19 steps"),
               "seacache": ("wan_main", "kalsearu0.35", r"$\delta{=}0.35$"), "ours": ("wan_main", "kalsea0.35", r"$\delta{=}0.35$")},
    },
}


def vbench(root, c):
    p = os.path.join(EXP, "vbench", root, f"{c}_eval_results.json")
    if not os.path.exists(p):
        return None
    raw = {k.replace("_", " "): v[0] for k, v in json.load(open(p)).items()}
    n = {k: (raw[k] - NORMALIZE_DIC[k]["Min"]) / (NORMALIZE_DIC[k]["Max"] - NORMALIZE_DIC[k]["Min"]) * DIM_WEIGHT[k]
         for k in raw if k in NORMALIZE_DIC}
    q = sum(n[k] for k in QUALITY_LIST) / sum(DIM_WEIGHT[k] for k in QUALITY_LIST)
    s = sum(n[k] for k in SEMANTIC_LIST) / sum(DIM_WEIGHT[k] for k in SEMANTIC_LIST)
    t = (q * QUALITY_WEIGHT + s * SEMANTIC_WEIGHT) / (QUALITY_WEIGHT + SEMANTIC_WEIGHT)
    return {"total": 100 * t, "quality": 100 * q, "semantic": 100 * s, "dims": raw}


def fidelity(root, c):
    p = os.path.join(EXP, root, c, "fidelity.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))[f"{root}/{c}"]
    return {k: r[k] for k in ("n", "nfe", "psnr", "ssim", "lpips")}


def main():
    out = {"what": __doc__.strip().splitlines()[0], "source": "/home/ubuntu/exp (shared evaluation harness)"}
    for model, budgets in CONFIGS.items():
        out[model] = {}
        for b, rows in budgets.items():
            out[model][b] = {}
            for key, (root, c, setting) in rows.items():
                out[model][b][key] = {"config": c, "setting": setting, "fidelity": fidelity(root, c), "vbench": vbench(root, c)}
                f, v = out[model][b][key]["fidelity"], out[model][b][key]["vbench"]
                print(f"{model:8s} {b:3s} {key:10s} {c:22s} fid={'ok' if f else '--'} vbench={'%.2f' % v['total'] if v else '--'}")
    json.dump(out, open(os.path.join(HERE, "data", "video_measured.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
