"""INTERNAL: where the FLUX.1-dev DrawBench-200 runs live and which internal run names map to which method.

This is the only file in figures/src with absolute paths and internal run names. Do not ship it (or figures/src at
all) in a supplementary-material archive without cleaning it; the generated data files (data/*.json, qual_tiles/*)
are keyed by method name and contain no paths.

Runs: 50 steps, 1024x1024, guidance 3.5, seed = prompt index, 200 DrawBench prompts (held out; COCO-64 was the
development set). Per-image metrics vs. the 50-step reference were computed by research_v2/techA/harness/eval2.py.
"""
EVAL_DIR = "/home/ubuntu/KalSea-dev/research_v2/runs/drawbench_eval"   # eval_*.json + one symlink per run directory
REF_RUN = "ref"                                                        # 50-step reference images

# main comparison: method -> run-name pattern ({d} = SEA-gate threshold delta, identical for all methods)
MAIN = {"seacache": "reuse_{d}",            # SEA gate + residual reuse (SeaCache, re-run in our harness)
        "kalsea": "speckcast_{d}",          # SEA gate + Kalman residual forecasting (DCT bands), no gap smoothing
        "ours": "kalsea_dct_pcgs_{d}"}      # KalSea (DCT bands) + predictor-corrector gap smoothing
DELTAS = ["0.2", "0.3", "0.37", "0.5", "0.6", "0.8", "1.0"]

# extra baseline at the two main budgets only (main table): first-order linear extrapolation of the block-stack
# residual from the last two computed steps, behind the same SEA gate (generic baseline; run name is internal)
EXTRA = {"linext": "linext_{d}"}
EXTRA_DELTAS = ["0.3", "0.6"]

# 2x2 ablation {DCT bands, per-element} x {gap smoothing off, on}
ABL = {("dct", "off"): "kalsea_main_{d}",       # same harness and code path as the smoothing-on run
       ("dct", "on"): "kalsea_dct_pcgs_{d}",
       ("elem", "off"): "speckcast_nodct_{d}",
       ("elem", "on"): "kalsea2_{d}"}
ABL_DELTAS = ["0.37", "0.6"]


def run_dir(run):
    return f"{EVAL_DIR}/{run}"
