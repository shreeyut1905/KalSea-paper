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
# per-image metrics (eval2) of the DrawBench ablation runs at delta 0.3 / 0.6: PCGS gain on each filler (run names below)
ABL_EVAL = "/home/ubuntu/KalSea-dev/research_v2/ablations/eval/eval_all.json"
FILLER_PAIRS = [  # (filler, run without PCGS, run with PCGS); {d} = delta
    ("reuse", "seacache_{d}", "abl_reuse_pcgs_{d}"),            # reuse (SeaCache) + PCGS with the linear smoother
    ("linext", "linextrap_{d}", "abl_linextrap_pcgs_{d}"),      # linear extrapolation + PCGS (pred. + linear innovation)
    ("kalsea", "kalsea_{d}", "ours_{d}"),                       # Kalman forecast (DCT) -> Ours
    ("calibfree", "abl_cf_pe_{d}", "abl_cf_pe_pcgs_{d}")]      # calibration-free per-element filter
FILLER_DELTAS = ["0.3", "0.6"]
# per-image metrics of the first-order linear-extrapolation baseline (linext_<d>) and of reuse (reuse_<d>) at all seven
# thresholds of the budget sweep, copied from one logged evaluation call (generic run names; see the file's "what")
LINEXT_SWEEP = "/home/ubuntu/KalSea-dev/paper_data/flux_linext_sweep.json"

# ---------------------------------------------------------------- video (video_stats.py -> data/video_stats.json)
# 944 VBench prompts, one video per prompt, seed 42, 65 frames, 50 steps. Full-reference metrics (TeaCache convention)
# and paired bootstrap CIs vs. our same-setup SeaCache re-run, written by video_code/video_metrics.py + fr_report.py.
# A missing file means "not evaluated yet" (the table prints \tbd).
VIDEO_FR = {"wan": "/home/ubuntu/video_runs/wan/eval/full/fr_metrics.json",
            # HunyuanVideo: gate with the sampler's live noise level (option A of paper_plan/hv_gate_fix.md)
            "hunyuan": "/home/ubuntu/video_runs/hunyuan/eval/full/fr_metrics_live.json"}
# HunyuanVideo with SeaCache's RELEASED gate (stale scheduler, delta 0.35, 16.0 NFE): quoted in the Tab. 2 footnote
VIDEO_EXTRA = {"hunyuan_released_gate_lo": ("/home/ubuntu/video_runs/hunyuan/eval/full/fr_metrics.json", "seacache_0.35")}
# budget -> (SEA-gate delta, Ours run, SeaCache re-run); "hi" ~ 24 NFE, "lo" ~ 17 (Wan) / 16.4 (HunyuanVideo) NFE
VIDEO_RUNS = {"wan": {"hi": ("0.2", "ours_0.2", "seacache_0.2"),
                      "lo": ("0.35", "ours_0.35", "seacache_0.35")},
              # HunyuanVideo low budget: delta 0.48 (16.0 NFE for every prompt, <= SeaCache's 16.4); the first run at 0.4637
              # used 16.7 NFE (> 16.4) and is not used. Optional 4th entry: evaluation file of that budget (else VIDEO_FR).
              "hunyuan": {"hi": ("0.2575", "ours_live_0.2575", "seacache_live_0.2575"),
                          "lo": ("0.48", "ours_live_0.48", "seacache_live_0.48",
                                 "/home/ubuntu/video_runs/hunyuan/eval/full/fr_metrics_live048.json")}}

# ---------------------------------------------------------------- video, supplementary material (video_stats.py -> data/video_supp.json)
# run folders (read only): per-video stats in <root>/<config>_meta/stats/*.jsonl (computed steps, gate distances, NFE)
VIDEO_ROOT = {"hunyuan": "/home/ubuntu/video_runs/hunyuan", "wan": "/home/ubuntu/video_runs/wan"}
# HunyuanVideo with SeaCache's RELEASED gate (stale scheduler), full 944-prompt runs: budget -> (delta, Ours run, SeaCache
# run); released delta 0.207 / 0.35 match the corrected 0.2575 / 0.48 in NFE (23.8 / 16.0)
VIDEO_RELEASED = {"hi": ("0.207", "ours_0.207", "seacache_0.207"), "lo": ("0.35", "ours_0.35", "seacache_0.35")}
VIDEO_RELEASED_FR = "/home/ubuntu/video_runs/hunyuan/eval/full/fr_metrics.json"
# HunyuanVideo, corrected gate, first low-budget threshold (calibrated on the 20 pilot prompts; 16.7 NFE on the full set,
# above SeaCache's 16.4, hence replaced by delta 0.48); evaluated in VIDEO_FR["hunyuan"]
VIDEO_HV_FIRST_LO = ("0.4637", "ours_live_0.4637", "seacache_live_0.4637")
# HunyuanVideo with the released gate at SeaCache's published delta 0.19 on the 20 pilot prompts (NFE above 24.0)
VIDEO_HV_PILOT = ("/home/ubuntu/video_runs/hunyuan/eval/pilot20.json", "seacache_0.19")
# 20-prompt video ablations (A2-A6), released-vs-corrected gate summary (A7) and the default-path bitwise checks; written
# by video_code/abl20/abl20_report.py from video_runs/{hunyuan,wan}/eval/abl20.json
VIDEO_ABL = "/home/ubuntu/KalSea-dev/paper_plan/video_ablations_20.json"

# ---------------------------------------------------------------- Fig. 1 collage (make_collage.py)
# FLUX.1-dev, 1024x1024, 50 steps, guidance 3.5, our cache (gate + Kalman forecaster + PCGS) at delta 0.2, generated with
# the released FLUX/kalsea_generate.py (seed = 2027 + line index of the prompt file; 4 candidates per prompt).
COLLAGE_RAW = "/home/ubuntu/KalSea-dev/v02_work/collage/raw"
# chosen candidate (line index of prompts_collage.txt) per tile: top row C V P R, bottom row 20 / KalSea billboard / 27
COLLAGE_PICK = {"C": 3, "V": 5, "P": 11, "R": 13, "20": 16, "KalSea": 22, "27": 24}

# ---------------------------------------------------------------- qualitative video examples (video_qual_select.py)
# Selection uses the low-budget runs of VIDEO_RUNS (per-video PSNR from their evaluation file, computed steps from the
# run stats). The videos of those runs were deleted to free disk; only the selected prompts were regenerated (same
# drivers, seeds and settings) into VIDEO_QUAL_DIR/<model>/{reference,seacache,ours}/<file>.mp4, and their frame
# checksums are compared with the ones recorded for the deleted videos (VIDEO_REF_STATS for the references; the
# run stats of VIDEO_ROOT/<config>_meta for the cached runs).
VIDEO_QUAL_DIR = "/home/ubuntu/KalSea-dev/v02_work/video_examples"
VIDEO_REF_STATS = {"hunyuan": "/home/ubuntu/video_runs/hunyuan/ref_meta/stats/*.jsonl",   # frames_sha1 (pre-encode)
                   "wan": "/home/ubuntu/KalSea-dev/video_logs/wan_ref/stats.jsonl"}       # frames_md5 (decoded)

# ---------------------------------------------------------------- TFLOPs / latency (cost_stats.py -> data/cost.json)
# One example per configuration of the main tables, released KalSea-v0.2 scripts (--no_cache / --reuse / default), all 8
# B200 GPUs in use at once (one job per GPU). Latency: <COST_DIR>/out/latency/<model>/<config>/stats*.jsonl, line 0 =
# warm-up, line 1 = timed call. TFLOPs: <COST_DIR>/out/flops_<model>_<config>.json (FlopCounterMode, Calflops convention).
# Prompts: FLUX DrawBench #0 (seed 0), video VBench #0 (seed 42); both have exactly the table NFE in the evaluated runs.
COST_DIR = "/home/ubuntu/KalSea-dev/cost_measure"
COST_CONFIGS = {"flux": {"ref": "ref", "hi": ("seacache_0.37", "kalsea_0.37"), "lo": ("seacache_0.6", "kalsea_0.6")},
                "hunyuan": {"model": "hv", "ref": "ref", "hi": ("seacache_0.2575", "kalsea_0.2575"),
                            "lo": ("seacache_0.48", "kalsea_0.48")},
                "wan": {"ref": "ref", "hi": ("seacache_0.2", "kalsea_0.2"), "lo": ("seacache_0.35", "kalsea_0.35")}}
# Published baselines of the main tables (TFLOPs as published; latency measured here, one example): FLUX via
# cost_measure/flux_baselines.py (official TeaCache4FLUX / TaylorSeer-diffusers code, release-script settings, warm-up + 3
# timed calls), video via the research baseline drivers (video_code/*/gen_vbench_baselines.py; warm-up prompt, then the
# example). Keys = make_tables.py SEACACHE_T1 / SEACACHE_VIDEO keys -> run folder under <COST_DIR>/out/latency_bl/<model>.
COST_BASELINES = {"flux": {"vanilla25": "vanilla_25", "vanilla15": "vanilla_15", "teacache0.3": "teacache_0.3",
                           "teacache0.6": "teacache_0.6", "taylorseer3": "taylorseer_s3", "taylorseer5": "taylorseer_s5"},
                  "hunyuan": {"hi": {"vanilla": "vanilla_25", "teacache": "teacache_0.12", "taylorseer": "taylorseer_s2"},
                              "lo": {"vanilla": "vanilla_15", "teacache": "teacache_0.2", "taylorseer": "taylorseer_s3"}},
                  "wan": {"hi": {"teacache": "teacache_0.09", "taylorseer": "taylorseer_s2"},
                          "lo": {"teacache": "teacache_0.15", "taylorseer": "taylorseer_s3"}}}
COST_VIDEO_PROMPT = "In a still frame, a stop sign"
