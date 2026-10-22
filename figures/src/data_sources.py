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

# ---------------------------------------------------------------- supplementary material (make_supp_tables.py)
RUN_DIR = "/home/ubuntu/KalSea-dev/research_v2/runs/drawbench"          # stats_shard*.jsonl (plugin_stats) of our runs
PCGS_RUN = "kalsea_dct_pcgs_{d}"                                        # Ours, per delta (latent-correction statistics)
CALIB_JSON = "/home/ubuntu/KalSea-dev/flux_data/speckcast_calib_flux.json"     # FLUX calibration of the DCT forecaster (16 COCO prompts)
CALIB_TRAJ = "/home/ubuntu/KalSea-dev/flux_data/calib_data/traj_000.pt"         # one calibration trajectory (only its sigma schedule is read)
DEV_HALVES = "/home/ubuntu/KalSea-dev/research_v2/techA/halves_core.txt"         # COCO-64 development set, halves A/B
DEV_ABL = "/home/ubuntu/KalSea-dev/research_v2/ablations/eval/eval_devset.txt"  # COCO-64 development-set ablations
OPENLOOP = "/home/ubuntu/KalSea-dev/research_v2/techB/diag_summary.txt"         # open-loop forecast error, 6 dev trajectories

# ---------------------------------------------------------------- video (video_stats.py -> data/video_stats.json)
# 944 VBench prompts, one video per prompt, seed 42, 65 frames, 50 steps. Full-reference metrics (TeaCache convention)
# and paired bootstrap CIs vs. our same-setup SeaCache re-run, written by video_code/video_metrics.py + fr_report.py.
# A missing file means "not evaluated yet" (the table prints \tbd).
VIDEO_FR = {"wan": "/home/ubuntu/video_runs/wan/eval/full/fr_metrics.json",
            # HunyuanVideo: gate with the sampler's live noise level (option A of paper_plan/hv_gate_fix.md)
            "hunyuan": "/home/ubuntu/video_runs/hunyuan/eval/full/fr_metrics_live.json"}
# budget -> (SEA-gate delta, Ours run, SeaCache re-run); "hi" ~ 24 NFE, "lo" ~ 17 (Wan) / 16.4 (HunyuanVideo) NFE
VIDEO_RUNS = {"wan": {"hi": ("0.2", "ours_0.2", "seacache_0.2"),
                      "lo": ("0.35", "ours_0.35", "seacache_0.35")},
              "hunyuan": {"hi": ("0.2575", "ours_live_0.2575", "seacache_live_0.2575"),
                          "lo": ("0.4637", "ours_live_0.4637", "seacache_live_0.4637")}}
