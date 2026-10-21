# Ablation plan, status and results (KalSea + predictor-corrector gap smoothing, CVPR 2027)

Status: 2026-10-21, 12:55 UTC. All FLUX ablations A1-A8, A10-A12 are DONE; A9 (video) is TO RUN after the video ports.
Paper tables generated from these runs (do not edit numbers by hand; regenerate with
`research_v2/ablations/make_tables.py`): `tables/tab_ablation_main.tex` (main paper, `\label{tab:ablation}`) and
`tables/tab_ablation_full.tex` (supplementary, `\label{tab:ablation-full}`). Both are `table*` (full width), booktabs,
both budgets side by side, NFE per row, paired delta-PSNR vs Ours with 95% bootstrap CI as a column; the main caption
also lists the paired gain of the correction on each filler.

## Key findings (DrawBench-200, held out; delta 0.3 / 0.6; paired dPSNR [95% CI]; matched NFE)

1. **The correction helps every filler.** Gain over the same filler without correction: KalSea (DCT) +0.83 [+0.63, +1.02]
   / +0.61 [+0.48, +0.76]; per-element KalSea +0.83 [+0.65, +1.01] / +0.58 [+0.44, +0.73]; tau = 0.1 +1.09 [+0.91, +1.27]
   / +0.83 [+0.68, +0.99]; calibration-free per-element +0.86 [+0.67, +1.05] / +0.55 [+0.42, +0.68]; first-order linear
   extrapolation +1.15 [+0.92, +1.38] / +0.80 [+0.62, +0.98]; reuse (SeaCache) +1.69 [+1.51, +1.88] / +0.74 [+0.62, +0.86].
2. **The gain comes from re-integrating the latent, not from a better forecaster state.** Feeding the smoothed gap
   residuals only into the forecaster changes nothing: -0.04 [-0.11, +0.03] / -0.02 [-0.04, +0.00] vs no correction.
3. **The smoother's gain shape is secondary; the RTS gains are not better than interpolation.** Over no correction:
   linear interpolation r_a -> r_b +0.97 / +0.62, prediction + linear innovation +0.97 / +0.63, Kalman RTS gains (Ours)
   +0.83 / +0.61. Ours vs interpolation: -0.14 [-0.25, -0.04] at delta 0.3, -0.00 [-0.06, +0.05] at 0.6; quadratic
   interpolation -0.05 / -0.08 vs Ours. On the development set the two were tied (interpolation vs RTS -0.13 [-0.31, +0.03]
   / +0.07 [-0.05, +0.20], per-element), which is where RTS was chosen. **The paper must not claim that the RTS gains beat
   interpolation.**
4. **The predictor matters to first order, the Kalman filter itself much less once corrected.** With the correction,
   first-order linear extrapolation ties Ours (+0.04 [-0.08, +0.16] / +0.07 [-0.05, +0.18]); reuse + correction stays
   below Ours (-1.03 [-1.39, -0.67] / -0.53 [-0.76, -0.29]) because the next computed step is evaluated at a worse latent.
   Without correction, the Kalman forecast beats linear extrapolation by +0.28 [+0.16, +0.42] / +0.11 [-0.02, +0.25] and
   reuse by +1.90 [+1.54, +2.26] / +0.66 [+0.42, +0.88].
5. **Exact re-integration matters at the larger budget:** batched zeroth-order re-integration loses -0.22 [-0.34, -0.09]
   / -0.06 [-0.13, +0.01] (development set -0.36 / -0.10).
6. **Gate-state refresh and the continuation variant have no measurable effect:** removing the refresh gives +0.03
   [-0.04, +0.10] / +0.01 [-0.01, +0.03] (NFE 20.90 vs 20.84); holding the block output instead of the residual fixed at b
   +0.03 / +0.01; additionally re-referencing the forecaster -0.01 / +0.01. These are optional details.
7. **Forecaster parametrisation is irrelevant once corrected:** DCT vs per-element -0.01 / +0.01; tau 0.5 vs 0.1 +0.08
   [-0.12, +0.29] / -0.05 [-0.22, +0.11]; calibration-free vs calibrated per-element -0.02 / +0.03. (Without correction,
   tau 0.5 beats 0.1 by +0.34 [+0.18, +0.52] / +0.17 [+0.02, +0.32]; DCT vs per-element -0.00 / -0.02.)
8. **Forecasting target:** x0, eps or velocity targets (DCT filters, no correction) are no better than the residual:
   residual minus target = -0.07 [-0.23, +0.08] / +0.09 [-0.01, +0.20] (x0), +0.20 [-0.08, +0.48] / +0.02 [-0.13, +0.16]
   (eps), -0.07 [-0.22, +0.08] / -0.02 [-0.12, +0.09] (velocity); the development set agrees (all within +-0.13 dB).
9. **Noise floor:** a second run of Ours differs by +0.02 [-0.04, +0.08] / +0.04 [-0.00, +0.10] dB; differences below
   about 0.1 dB are not interpretable.

**Implications for the writing (owner decisions).** The defensible contribution is the predictor-corrector
re-integration of each skipped gap once the next step is computed (zero extra transformer-block evaluations), which
works across fillers and forecaster parametrisations. The Kalman RTS gains are one principled instance (MMSE under the
forecaster's own model), but the simplest instance (linear interpolation between the two computed residuals, i.e. the
RTS smoother of a random-walk model) is as good on DrawBench (better by 0.14 dB at delta 0.3). Switching the default
smoother now would be selection on the held-out set; if the simpler smoother is preferred, justify it with the
development-set tie and simplicity, and report both. The gate refresh can be dropped or kept as a cost-free detail.

## Conventions (apply to every FLUX entry)

- **Model / protocol (SeaCache's FLUX protocol).** FLUX.1-dev, bf16, 1024x1024, 50 Euler flow-matching steps, distilled
  guidance 3.5, max_sequence_length 512, seed = prompt index, one B200 per process. Reference = the 50-step uncached output
  of the same seed (`<flux_data>/runs/drawbench/ref`).
- **Prompts.** Paper numbers: **DrawBench-200, held out** (used only to score finished configurations). Every design
  choice (smoother, re-integration, constants) was made on the **COCO-64 development set**
  (`<flux_data>/prompts/coco_tune64.txt`, halves A = 0..31 for development, B = 32..63 for confirmation);
  development-set numbers are labelled as such and never mixed into paper tables.
- **Budgets.** Same SEA gate threshold for every variant: delta = 0.3 (about 20.8 NFE; SeaCache's "about 50%" budget) and
  delta = 0.6 (13.0 NFE; "about 30%"). NFE = mean number of full transformer evaluations per image, counted by forward
  pre-hooks on all 19 + 38 blocks and cross-checked against the forward's own counter for every bench2 run (0
  mismatches, 0 partial stacks); the older runs made with `<flux_data>/benchmark.py` (SeaCache, KalSea, linear
  extrapolation, tau 0.1 and per-element controls) report the forward's counter. The gate is closed-loop, so a variant can move NFE; every row reports its NFE; all DrawBench ablation rows
  are within 0.06 NFE of Ours at delta 0.3 and at exactly 13.00 NFE at delta 0.6 (matched-NFE comparisons only;
  `ablations/eval/nfe_check.txt`).
- **Base configuration ("Ours").** SEA gate (SeaCache) + KalSea DCT-band Kalman residual forecaster (tau = 0.5,
  R = 1e-3, online process-noise adaptation, FLUX calibration from 16 COCO prompts disjoint from DrawBench) + PCGS
  (Kalman RTS smoothing gains, exact sequential re-integration with output layers only, residual held fixed at the
  computed step b, gate-state refresh). Zero extra transformer-block evaluations.
- **Metrics.** PSNR / SSIM (scikit-image, uint8 RGB, data_range 255) and LPIPS (AlexNet) against the reference
  (`research_v2/techA/harness/eval2.py`). Paired differences to Ours over the 200 prompts with a 95% percentile bootstrap
  CI (10,000 resamples, numpy default_rng(0), identical to every other eval2 table of the project) and the win rate.
- **Noise floor.** The DCT filter's atomic `scatter_add_` (process-noise adaptation) is not bitwise reproducible, so two
  runs of the same configuration differ slightly. A second independent run of Ours measures this (entry A11); claims
  below 0.1 dB are not made.
- **Cost unit.** One FLUX DrawBench-200 configuration costs about 8 GPU-min at delta 0.3 and 5.5 GPU-min at delta 0.6 on
  a B200 (plus about 1 min model load per process); scoring costs about 1 CPU-min per run (LPIPS on CPU or GPU).

## Ablation list

Run names below are directories under `research_v2/ablations/runs/` (our runs, or per-file mirrors of existing runs so
that eval2's cache stays in our tree). Mirrors: `seacache_<d>` = `<flux_data>/runs/drawbench/reuse_<d>`,
`linextrap_<d>` = `.../linext_<d>` (first-order linear extrapolation of the last two computed residuals, the
w = 0 setting of that code path; used only as a generic baseline), `kalsea_<d>` = `.../speckcast_<d>`, `kalsea_pe_<d>` = `.../speckcast_nodct_<d>`,
`kalsea_tau0.1_<d>` = `.../speckcast_paper_<d>`, `ours_<d>` = `research_v2/runs/drawbench/kalsea_dct_pcgs_<d>`,
`ours_pe_<d>` = `.../kalsea2_<d>`, `abl_pcgs_*` / `abl_tau01_pcgs_*` / `abl_reuse_pcgs_*` = `research_v2/runs/drawbench_abl/*`
(launched by the orchestrator with `techA/pcgs.py`, configs in `research_v2/techA/configs/drawbench_ablations.json`).
New plugin options live in `research_v2/ablations/pcgs_abl.py` (copy of `techA/pcgs.py`; `techA/pcgs.py` unchanged).

### A1. Skip-path filler at the same gate
- **Question.** With SeaCache's gate fixed, how much does the choice of what is written on skipped steps matter, and how
  much does the correction add on top of the best forecaster?
- **Configs.** reuse = SeaCache (`seacache_<d>`); first-order linear extrapolation of the last two computed residuals
  (`linextrap_<d>`); Kalman forecast = KalSea (`kalsea_<d>`); Kalman forecast + PCGS = Ours (`ours_<d>`).
- **Model / prompts / budgets.** FLUX.1-dev, DrawBench-200, delta 0.3 and 0.6.
- **Metric.** PSNR / SSIM / LPIPS, paired dPSNR vs Ours with CI.
- **Status.** DONE (all four runs existed; scored here).
- **Cost.** 0 GPU (scoring only).

### A2. What the corrector corrects and with which weights
- **Question.** Is the gain due to re-integrating the latent, or would feeding the new observation back into the
  forecaster be enough? Given re-integration, do the Kalman RTS gains matter, or is any interpolation as good?
- **Configs** (all on the DCT Kalman forecaster, exact re-integration, gate refresh):
  1. no correction = KalSea (`kalsea_<d>`);
  2. forecaster state only, no latent re-integration (`abl_stateonly_<d>`, `pcgs_abl.PCGS(apply='state_only')`): the
     filter is rolled back to its posterior at a, the RTS-smoothed gap residuals are assimilated as observations, then
     r_b; latent, returned velocity and gate are untouched. (Replacing the state at b by its RTS-smoothed estimate would
     be an exact no-op, because smoothed and filtered estimates coincide at the newest observation.)
  3. re-integration with linear interpolation r_a -> r_b, ignoring the forecast (`abl_pcgs_lin_<d>`, smoother `lin_step`;
     = RTS smoother of a random-walk model);
  4. re-integration with prediction + linearly weighted innovation, r~_i = pred_i + ((i-a)/(b-a)) e_b
     (`abl_predlin_<d>`, smoother `pred_lin_innov`; same innovation and coordinates as 5, only the gain shape differs);
  5. re-integration with the Kalman RTS gains g_i = [P_i^- Phi(b,i)^T]_00 / (P_b^-_00 + R) (Ours);
  6. extra: quadratic interpolation through the last three computed residuals (`abl_pcgs_quad_<d>`).
- **Model / prompts / budgets.** FLUX.1-dev, DrawBench-200, delta 0.3 and 0.6.
- **Metric.** As A1; plus the gain of each variant over "no correction".
- **Status.** DONE (2026-10-21). 1, 5 existed; 3, 6 from the orchestrator run `drawbench_abl`; 2 and 4 run in this step
  with the new, unit-tested plugin options.
- **Cost.** 4 configurations, about 0.5 GPU-h.

### A3. Exact sequential vs batched (zeroth-order) re-integration
- **Question.** Does the re-integration need the corrected latents (sequential x_embedder + output layers per gap step),
  or is one batched output-layer call on the stored inputs (zeroth order in the latent change) enough?
- **Configs.** Ours vs `abl_pcgs_batched_<d>` (`mode='batched'`).
- **Model / prompts / budgets / metric.** As A1.
- **Status.** DONE (2026-10-21, orchestrator run `drawbench_abl`).
- **Cost.** 2 configurations, about 0.25 GPU-h.

### A4. Gate-state refresh
- **Question.** After the latent is corrected, must the SEA gate's stored modulated input be recomputed from the
  corrected latent (one block-0 norm1 + SEA filter, no block call)?
- **Configs.** Ours vs `abl_pcgs_nogatefix_<d>` (`gate_fix=False`). NFE is reported because the gate is closed-loop.
- **Status.** DONE (2026-10-21, orchestrator run `drawbench_abl`).
- **Cost.** 2 configurations, about 0.25 GPU-h.

### A5. Forecaster parametrisation (is the correction robust to it?)
- **Question.** Does the correction's gain depend on the forecaster's parametrisation: DCT bands with band-specific
  warped time vs one per-element filter; damping tau = 0.1 (SpecKCast default) vs 0.5 (ours); calibrated vs
  calibration-free (the video ports will be calibration-free)?
- **Configs.** 2x2 {DCT, per-element} x {no correction, PCGS}: `kalsea_<d>`, `ours_<d>`, `kalsea_pe_<d>`,
  `ours_pe_<d>` (delta 0.6 existed; delta 0.3: `abl_pe_0.3`, `abl_pe_pcgs_0.3` run here). 2x2 {tau 0.1, 0.5} x
  {no correction, PCGS}: `kalsea_tau0.1_0.6` existed, `abl_tau01_0.3` run here, `abl_tau01_pcgs_<d>` orchestrator.
  Calibration-free per-element (unit p_warp, q = 7400, p22 = 15000, step time; `techA/configs/calibfree.json`):
  `abl_cf_pe_<d>`, `abl_cf_pe_pcgs_<d>` run here.
- **Model / prompts / budgets / metric.** As A1.
- **Status.** DONE (2026-10-21) at delta 0.3 and 0.6 (and 0.37 for the DCT / per-element 2x2): the delta-0.3 cells,
  the tau-0.1 control at 0.3 and the calibration-free runs were run in this step.
- **Cost.** 7 configurations, about 0.8 GPU-h.

### A6. Forecasting target
- **Question.** Is the block-stack residual the right quantity to forecast, or would a sampler quantity (x0, eps,
  velocity) reconstructed from the current latent be better (it feeds back latent drift)?
- **Configs.** Development set (COCO-64, `research_v2/techB/plugin_b.py`, `SamplerConsistent(param in {x0, eps, v},
  fc in {pe, dct})`, no correction) vs the residual forecaster with the same filter. Optional DrawBench confirmation with
  DCT filters: `abl_tgt_{x0,eps,v}_<d>`.
- **Status.** DONE. Development-set evidence (runs stopped at 57-60 of 64 prompts; scored on the common prompts) and a
  DrawBench confirmation with DCT filters (`abl_tgt_{x0,eps,v}_<d>`, run in this step).
- **Cost.** 6 configurations, about 0.7 GPU-h.

### A7. The corrector on other fillers
- **Question.** Is the corrector specific to the Kalman forecaster, or does it also repair SeaCache's plain reuse and
  linear extrapolation?
- **Configs.** reuse + PCGS with the linear smoother (`abl_reuse_pcgs_<d>`; for reuse, pred_i = r_a, so
  "prediction + linear innovation" = linear interpolation r_a -> r_b, the RTS smoother of a random walk; bitwise identical
  in the unit test) vs `seacache_<d>`; linear extrapolation + PCGS with prediction + linear innovation
  (`abl_linextrap_pcgs_<d>`, the prior forecast at b is recorded before the update) vs `linextrap_<d>`.
- **Status.** DONE (2026-10-21): reuse from the orchestrator run, linear extrapolation run in this step.
- **Cost.** 4 configurations, about 0.5 GPU-h.

### A8. Budget sweep (quality vs NFE)
- **Question.** Does the gain hold across budgets (9 to 27 NFE)?
- **Configs.** delta in {0.2, 0.3, 0.5, 0.6, 0.8, 1.0} for SeaCache, KalSea and Ours.
- **Status.** DONE (`research_v2/runs/drawbench_eval/eval_sweep_vs_seacache.txt`, `eval_sweep_vs_kalsea.txt`,
  `eval_two_budgets_vs_seacache.txt`). Feeds the quality-vs-NFE figure, not the ablation table.
- **Cost.** 0.

### A9. Video: correction on/off
- **Question.** Does the correction carry over to video DiTs (HunyuanVideo: flow Euler, direct port; Wan2.1: UniPC
  multistep + CFG, needs a UniPC replay of the gap)?
- **Configs.** KalSea vs KalSea + PCGS (and SeaCache) at SeaCache's two deltas: HunyuanVideo 0.19 / 0.35, Wan2.1 1.3B
  0.2 / 0.35; same gate, matched NFE.
- **Model / prompts.** HunyuanVideo 480x640x65f and Wan2.1-T2V-1.3B 832x480x81f, 50 steps, seed 42, on a 20-prompt
  VBench subset (`vbench_subset20.txt`, random with a published seed, as SeaCache's Fig. 8b ablation).
- **Metric.** PSNR / SSIM / LPIPS vs the 50-step reference video (TeaCache `common_metrics` definitions), paired CIs over
  the 20 prompts (wide; report them).
- **Status.** TO RUN after the video ports (forecaster + PCGS hooks in `video_code/*/gen_vbench.py`); references are
  being generated now.
- **Cost.** About 4 configurations x 20 videos x 0.3-0.5 reference-equivalents x 45-60 s per model, i.e. about
  0.5 GPU-h per model (about 5 min wall on 8 GPUs) plus model loading; a 6-delta curve would be about 5 GPU-h.

### A10. Allocation instead of correction (negative result, development set only)
- **Question.** Could the innovation be used to decide *when* to compute (error-controlled gate) instead of correcting
  the gap?
- **Configs.** `research_v2/techC/techc_errctl.py` (pure error control replacing the SEA gate, tolerance per budget),
  plus a fixed schedule equal to the controller's average schedule (`C2_fixedavg_*`).
- **Status.** Development set only (interim runs, C2 stopped at 30-32 of 64 prompts); see the development-set section.
  Not planned for DrawBench.

### A11. Run-to-run noise floor
- **Question.** How large are differences between two runs of the same configuration (DCT filter not bitwise
  reproducible)?
- **Configs.** `abl_ours_rerun_<d>` (our plugin copy, default arguments) vs `ours_<d>` (techA plugin).
- **Status.** DONE (2026-10-21). Also checks that the plugin copy reproduces the original plugin.
- **Cost.** 2 configurations, about 0.25 GPU-h.

### A12 (supplementary). Continuation at the computed step
- **Question.** At the computed step b the sampler continues from the corrected latent; should the *residual* r_b be
  held fixed (Ours: v_b' = Out(x_embedder(x_b') + r_b) + (x_b' - x_b)/dt_b) or the block output h_out (v_b unchanged,
  latent shifted), optionally with the forecaster re-updated with the re-referenced residual?
- **Configs.** `abl_hout_<d>` (`out_mode='hout'`), `abl_houtfc_<d>` (`out_mode='hout_fc'`).
- **Status.** DONE (2026-10-21, supplementary).
- **Cost.** 4 configurations, about 0.5 GPU-h.

## Results on DrawBench-200 (all rows; generated by make_tables.py from `ablations/eval/eval_all.json`)

Columns: mean NFE, PSNR, paired dPSNR vs Ours at the same delta [95% CI], SSIM, LPIPS. Run names in backticks (`{d}` = 0.3 or 0.6). Second table: additional paired comparisons (dPSNR with win rate, dLPIPS).

| variant | NFE 0.3 | PSNR 0.3 | dPSNR vs Ours 0.3 [95% CI] | SSIM 0.3 | LPIPS 0.3 | NFE 0.6 | PSNR 0.6 | dPSNR vs Ours 0.6 [95% CI] | SSIM 0.6 | LPIPS 0.6 |
|---|---|---|---|---|---|---|---|---|---|---|
| Ours (Kalman forecast + PCGS) (`ours_{d}`) | 20.84 | 29.62 | ref. | 0.9353 | 0.0528 | 13.00 | 22.53 | ref. | 0.8416 | 0.1539 |
| *(a) Skip-path filler at the same gate, no correction* | | | | | | | | | | |
| Reuse (SeaCache) (`seacache_{d}`) | 20.88 | 26.89 | -2.73 [-3.12, -2.34] | 0.9038 | 0.0859 | 13.00 | 21.26 | -1.27 [-1.52, -1.02] | 0.8001 | 0.2138 |
| First-order linear extrapolation (`linextrap_{d}`) | 20.84 | 28.51 | -1.11 [-1.34, -0.89] | 0.9255 | 0.0615 | 13.00 | 21.80 | -0.73 [-0.92, -0.54] | 0.8268 | 0.1708 |
| Kalman forecast (KalSea) (`kalsea_{d}`) | 20.82 | 28.79 | -0.83 [-1.02, -0.63] | 0.9273 | 0.0601 | 13.00 | 21.91 | -0.61 [-0.76, -0.48] | 0.8256 | 0.1716 |
| *(b) Gap correction on the Kalman forecast (Ours: RTS gains)* | | | | | | | | | | |
| Forecaster state only (no latent re-integration) (`abl_stateonly_{d}`) | 20.82 | 28.75 | -0.86 [-1.06, -0.68] | 0.9268 | 0.0607 | 13.00 | 21.89 | -0.63 [-0.78, -0.50] | 0.8233 | 0.1744 |
| Re-integrate with linear interpolation r_a -> r_b (`abl_pcgs_lin_{d}`) | 20.84 | 29.76 | +0.14 [+0.04, +0.25] | 0.9357 | 0.0520 | 13.00 | 22.53 | +0.00 [-0.05, +0.06] | 0.8394 | 0.1557 |
| Re-integrate with quadratic interpolation (last 3 computed residuals) (`abl_pcgs_quad_{d}`) | 20.84 | 29.57 | -0.05 [-0.16, +0.06] | 0.9346 | 0.0537 | 13.00 | 22.45 | -0.08 [-0.16, -0.00] | 0.8397 | 0.1559 |
| Re-integrate with prediction + linearly weighted innovation (`abl_predlin_{d}`) | 20.84 | 29.76 | +0.14 [+0.04, +0.25] | 0.9359 | 0.0519 | 13.00 | 22.55 | +0.02 [-0.03, +0.07] | 0.8401 | 0.1550 |
| *(c) Re-integration and continuation* | | | | | | | | | | |
| Batched (zeroth-order) re-integration (`abl_pcgs_batched_{d}`) | 20.84 | 29.40 | -0.22 [-0.34, -0.09] | 0.9335 | 0.0545 | 13.00 | 22.46 | -0.06 [-0.13, +0.01] | 0.8398 | 0.1556 |
| No gate-state refresh (`abl_pcgs_nogatefix_{d}`) | 20.90 | 29.65 | +0.03 [-0.04, +0.10] | 0.9361 | 0.0521 | 13.00 | 22.54 | +0.01 [-0.01, +0.03] | 0.8416 | 0.1539 |
| Continuation: block output (not residual) held fixed at b (`abl_hout_{d}`) | 20.84 | 29.65 | +0.03 [-0.03, +0.10] | 0.9354 | 0.0528 | 13.00 | 22.54 | +0.01 [-0.02, +0.04] | 0.8417 | 0.1536 |
| Continuation: block output held fixed + forecaster re-referenced (`abl_houtfc_{d}`) | 20.84 | 29.61 | -0.01 [-0.13, +0.13] | 0.9355 | 0.0528 | 13.00 | 22.54 | +0.01 [-0.02, +0.04] | 0.8418 | 0.1536 |
| *(d) Forecaster parametrisation* | | | | | | | | | | |
| Per-element filter (no DCT bands), no correction (`kalsea_pe_{d}`) | 20.84 | 28.79 | -0.82 [-1.03, -0.63] | 0.9273 | 0.0601 | 13.00 | 21.94 | -0.59 [-0.79, -0.40] | 0.8292 | 0.1693 |
| Per-element filter + PCGS (`ours_pe_{d}`) | 20.84 | 29.63 | +0.01 [-0.15, +0.14] | 0.9352 | 0.0531 | 13.00 | 22.52 | -0.01 [-0.15, +0.13] | 0.8429 | 0.1535 |
| tau = 0.1, no correction (`kalsea_tau0.1_{d}`) | 20.84 | 28.45 | -1.17 [-1.40, -0.95] | 0.9225 | 0.0655 | 13.00 | 21.74 | -0.79 [-0.97, -0.60] | 0.8171 | 0.1860 |
| tau = 0.1 + PCGS (`abl_tau01_pcgs_{d}`) | 20.85 | 29.54 | -0.08 [-0.29, +0.12] | 0.9342 | 0.0542 | 13.00 | 22.58 | +0.05 [-0.11, +0.22] | 0.8403 | 0.1563 |
| Calibration-free per-element filter, no correction (`abl_cf_pe_{d}`) | 20.84 | 28.75 | -0.87 [-1.07, -0.67] | 0.9273 | 0.0600 | 13.00 | 22.00 | -0.53 [-0.73, -0.33] | 0.8304 | 0.1686 |
| Calibration-free per-element filter + PCGS (`abl_cf_pe_pcgs_{d}`) | 20.84 | 29.60 | -0.02 [-0.11, +0.08] | 0.9357 | 0.0523 | 13.00 | 22.55 | +0.02 [-0.13, +0.17] | 0.8435 | 0.1528 |
| *(e) Correction on other fillers* | | | | | | | | | | |
| Reuse + PCGS (linear smoother = pred. + linear innovation) (`abl_reuse_pcgs_{d}`) | 20.88 | 28.58 | -1.03 [-1.39, -0.67] | 0.9268 | 0.0612 | 13.00 | 22.00 | -0.53 [-0.76, -0.29] | 0.8266 | 0.1730 |
| Linear extrapolation + PCGS (pred. + linear innovation) (`abl_linextrap_pcgs_{d}`) | 20.84 | 29.66 | +0.04 [-0.08, +0.16] | 0.9353 | 0.0524 | 13.00 | 22.59 | +0.07 [-0.05, +0.18] | 0.8436 | 0.1518 |
| *(f) Forecasting target, no correction (DCT filter)* | | | | | | | | | | |
| x0 target (velocity reconstructed from the current latent) (`abl_tgt_x0_{d}`) | 20.86 | 28.86 | -0.76 [-0.97, -0.55] | 0.9286 | 0.0587 | 13.00 | 21.82 | -0.71 [-0.86, -0.56] | 0.8305 | 0.1671 |
| eps target (velocity reconstructed from the current latent) (`abl_tgt_eps_{d}`) | 20.85 | 28.59 | -1.02 [-1.34, -0.72] | 0.9257 | 0.0618 | 13.00 | 21.89 | -0.63 [-0.82, -0.46] | 0.8260 | 0.1746 |
| velocity target (`abl_tgt_v_{d}`) | 20.86 | 28.86 | -0.76 [-0.97, -0.55] | 0.9289 | 0.0589 | 13.00 | 21.93 | -0.59 [-0.76, -0.44] | 0.8315 | 0.1672 |

| paired comparison | dPSNR 0.3 [95% CI], win% | dLPIPS 0.3 [95% CI] | dPSNR 0.6 [95% CI], win% | dLPIPS 0.6 [95% CI] |
|---|---|---|---|---|
| PCGS gain on the Kalman forecaster (DCT) (`ours_{d}` vs `kalsea_{d}`) | +0.83 [+0.63, +1.02], 81% | -0.0073 [-0.0087, -0.0058] | +0.61 [+0.48, +0.76], 78% | -0.0177 [-0.0208, -0.0148] |
| PCGS gain on the per-element Kalman forecaster (`ours_pe_{d}` vs `kalsea_pe_{d}`) | +0.83 [+0.65, +1.01], 80% | -0.0071 [-0.0089, -0.0051] | +0.58 [+0.44, +0.73], 76% | -0.0158 [-0.0195, -0.0120] |
| PCGS gain at tau = 0.1 (`abl_tau01_pcgs_{d}` vs `kalsea_tau0.1_{d}`) | +1.09 [+0.91, +1.27], 88% | -0.0114 [-0.0129, -0.0099] | +0.83 [+0.68, +0.99], 84% | -0.0297 [-0.0334, -0.0262] |
| PCGS gain on reuse (SeaCache) (`abl_reuse_pcgs_{d}` vs `seacache_{d}`) | +1.69 [+1.51, +1.88], 92% | -0.0248 [-0.0270, -0.0226] | +0.74 [+0.62, +0.86], 78% | -0.0408 [-0.0450, -0.0368] |
| PCGS gain on linear extrapolation (`abl_linextrap_pcgs_{d}` vs `linextrap_{d}`) | +1.15 [+0.92, +1.38], 82% | -0.0090 [-0.0108, -0.0072] | +0.80 [+0.62, +0.98], 78% | -0.0190 [-0.0234, -0.0146] |
| state-only vs no correction (`abl_stateonly_{d}` vs `kalsea_{d}`) | -0.04 [-0.11, +0.03], 52% | +0.0006 [+0.0002, +0.0010] | -0.02 [-0.04, +0.00], 44% | +0.0028 [+0.0021, +0.0036] |
| linear interpolation vs no correction (`abl_pcgs_lin_{d}` vs `kalsea_{d}`) | +0.97 [+0.75, +1.19], 80% | -0.0081 [-0.0099, -0.0064] | +0.62 [+0.46, +0.79], 76% | -0.0159 [-0.0194, -0.0126] |
| pred + linear innovation vs no correction (`abl_predlin_{d}` vs `kalsea_{d}`) | +0.97 [+0.75, +1.19], 82% | -0.0082 [-0.0099, -0.0064] | +0.63 [+0.49, +0.79], 79% | -0.0166 [-0.0202, -0.0132] |
| Kalman RTS vs pred + linear innovation (`ours_{d}` vs `abl_predlin_{d}`) | -0.14 [-0.25, -0.04], 43% | +0.0009 [+0.0002, +0.0017] | -0.02 [-0.07, +0.03], 46% | -0.0011 [-0.0025, +0.0002] |
| Kalman RTS vs linear interpolation (`ours_{d}` vs `abl_pcgs_lin_{d}`) | -0.14 [-0.25, -0.04], 43% | +0.0009 [+0.0002, +0.0016] | -0.00 [-0.06, +0.05], 50% | -0.0018 [-0.0029, -0.0007] |
| exact vs batched re-integration (`ours_{d}` vs `abl_pcgs_batched_{d}`) | +0.22 [+0.09, +0.34], 70% | -0.0016 [-0.0025, -0.0008] | +0.06 [-0.01, +0.13], 60% | -0.0017 [-0.0032, -0.0002] |
| gate refresh on vs off (`ours_{d}` vs `abl_pcgs_nogatefix_{d}`) | -0.03 [-0.10, +0.04], 44% | +0.0007 [+0.0002, +0.0012] | -0.01 [-0.03, +0.01], 41% | -0.0000 [-0.0003, +0.0002] |
| tau 0.5 vs 0.1 (with PCGS) (`ours_{d}` vs `abl_tau01_pcgs_{d}`) | +0.08 [-0.12, +0.29], 51% | -0.0013 [-0.0043, +0.0008] | -0.05 [-0.22, +0.11], 49% | -0.0023 [-0.0062, +0.0018] |
| tau 0.5 vs 0.1 (no correction) (`kalsea_{d}` vs `kalsea_tau0.1_{d}`) | +0.34 [+0.18, +0.52], 66% | -0.0055 [-0.0083, -0.0033] | +0.17 [+0.02, +0.32], 57% | -0.0143 [-0.0184, -0.0103] |
| DCT vs per-element (with PCGS) (`ours_{d}` vs `ours_pe_{d}`) | -0.01 [-0.14, +0.15], 44% | -0.0002 [-0.0031, +0.0017] | +0.01 [-0.13, +0.15], 46% | +0.0005 [-0.0026, +0.0036] |
| DCT vs per-element (no correction) (`kalsea_{d}` vs `kalsea_pe_{d}`) | -0.00 [-0.14, +0.14], 46% | -0.0000 [-0.0017, +0.0014] | -0.02 [-0.18, +0.14], 48% | +0.0023 [-0.0017, +0.0066] |
| Kalman forecast vs reuse (no correction) (`kalsea_{d}` vs `seacache_{d}`) | +1.90 [+1.54, +2.26], 82% | -0.0258 [-0.0301, -0.0218] | +0.66 [+0.42, +0.88], 67% | -0.0422 [-0.0496, -0.0349] |
| Kalman forecast vs linear extrapolation (no correction) (`kalsea_{d}` vs `linextrap_{d}`) | +0.28 [+0.16, +0.42], 66% | -0.0014 [-0.0025, -0.0002] | +0.11 [-0.02, +0.25], 56% | +0.0008 [-0.0032, +0.0052] |
| PCGS gain on the calibration-free per-element forecaster (`abl_cf_pe_pcgs_{d}` vs `abl_cf_pe_{d}`) | +0.86 [+0.67, +1.05], 82% | -0.0077 [-0.0096, -0.0060] | +0.55 [+0.42, +0.68], 74% | -0.0158 [-0.0192, -0.0124] |
| calibration-free vs calibrated per-element (no correction) (`abl_cf_pe_{d}` vs `kalsea_pe_{d}`) | -0.05 [-0.21, +0.13], 41% | -0.0001 [-0.0019, +0.0014] | +0.06 [+0.03, +0.09], 62% | -0.0007 [-0.0016, +0.0002] |
| calibration-free vs calibrated per-element (with PCGS) (`abl_cf_pe_pcgs_{d}` vs `ours_pe_{d}`) | -0.02 [-0.18, +0.16], 43% | -0.0007 [-0.0039, +0.0016] | +0.03 [-0.04, +0.10], 50% | -0.0006 [-0.0022, +0.0007] |
| residual held fixed (Ours) vs block output held fixed (`ours_{d}` vs `abl_hout_{d}`) | -0.03 [-0.10, +0.03], 48% | +0.0000 [-0.0006, +0.0006] | -0.01 [-0.04, +0.02], 46% | +0.0003 [-0.0007, +0.0011] |
| block output held fixed: forecaster re-referenced vs not (`abl_houtfc_{d}` vs `abl_hout_{d}`) | -0.04 [-0.16, +0.09], 44% | -0.0000 [-0.0009, +0.0008] | +0.00 [-0.03, +0.02], 46% | -0.0001 [-0.0009, +0.0007] |
| run-to-run: Ours rerun vs Ours (`abl_ours_rerun_{d}` vs `ours_{d}`) | +0.02 [-0.04, +0.08], 53% | -0.0003 [-0.0007, +0.0001] | +0.04 [-0.00, +0.10], 52% | -0.0008 [-0.0016, -0.0001] |
| residual target vs x0 target (no correction) (`kalsea_{d}` vs `abl_tgt_x0_{d}`) | -0.07 [-0.23, +0.08], 50% | +0.0014 [+0.0002, +0.0026] | +0.09 [-0.01, +0.20], 54% | +0.0045 [+0.0022, +0.0068] |
| residual target vs eps target (no correction) (`kalsea_{d}` vs `abl_tgt_eps_{d}`) | +0.20 [-0.08, +0.48], 52% | -0.0017 [-0.0050, +0.0009] | +0.02 [-0.13, +0.16], 50% | -0.0030 [-0.0067, +0.0009] |
| residual target vs velocity target (no correction) (`kalsea_{d}` vs `abl_tgt_v_{d}`) | -0.07 [-0.22, +0.08], 42% | +0.0012 [+0.0001, +0.0024] | -0.02 [-0.12, +0.09], 48% | +0.0045 [+0.0019, +0.0072] |

## Development-set evidence (COCO-64; never mixed into paper tables)

`research_v2/ablations/eval/eval_devset.txt` (eval2 vs `runs/tune/ref`, paired bootstrap 10k). Budgets: delta 0.37
(18.0 NFE) and 0.6 (13.0 NFE). Several runs of the round that produced them were stopped at 57-63 of 64 prompts; their
paired differences use the common prompts (n given). Forecaster = per-element KalSea unless noted.

| comparison (development set) | n | dPSNR @ 18 NFE [95% CI] | dPSNR @ 13 NFE [95% CI] |
|---|---|---|---|
| PCGS gain, DCT forecaster (`A_kal_main` vs `kalsea_main`) | 64 | +0.75 [+0.50, +1.00] | +0.73 [+0.46, +1.02] |
| PCGS gain, per-element forecaster (`A_kal_pe` vs `kalsea_pe`) | 64 | +1.09 [+0.83, +1.38] | +0.63 [+0.35, +0.92] |
| linear interpolation r_a -> r_b vs Kalman RTS (`A_lin_pe` vs `A_kal_pe`) | 63 / 62 | -0.13 [-0.31, +0.03] | +0.07 [-0.05, +0.20] |
| quadratic interpolation vs Kalman RTS (`A_quad_pe`) | 63 / 62 | -0.23 [-0.39, -0.09] | -0.05 [-0.12, +0.01] |
| batched (zeroth-order) vs exact re-integration (`A_kalb_pe`) | 63 / 62 | -0.36 [-0.61, -0.18] | -0.10 [-0.26, +0.02] |
| no gate-state refresh vs refresh (`A_kalng_pe`) | 63 / 62 | +0.02 [-0.00, +0.05] | -0.00 [-0.01, +0.00] |
| calibration-free vs calibrated, no correction (`Actl_cf` vs `kalsea_pe`) | 62 | -0.03 [-0.22, +0.15] | +0.07 [+0.02, +0.12] |
| PCGS gain, calibration-free forecaster (`A_kal_cf` vs `Actl_cf`) | 62 | +0.83 [+0.61, +1.05] | +0.51 [+0.19, +0.82] |
| reuse + PCGS (linear smoother) vs reuse (`A_lin_reuse` vs `reuse`) | 64 | +1.31 [+1.00, +1.59] | +0.77 [+0.57, +0.97] |
| target x0 vs residual, per-element (`B_x0_pe` vs `kalsea_pe`) | 60 / 58 | -0.06 [-0.32, +0.20] | -0.10 [-0.24, +0.04] |
| target x0 vs residual, DCT (`B_x0_dct` vs `kalsea_main`) | 59 / 57 | +0.12 [-0.13, +0.40] | -0.04 [-0.14, +0.07] |
| target eps vs residual, per-element (`B_eps_pe`) | 60 / 57 | -0.07 [-0.32, +0.18] | -0.12 [-0.44, +0.19] |
| target velocity vs residual, per-element (`B_v_pe`) | 60 / 57 | -0.10 [-0.30, +0.08] | -0.09 [-0.21, +0.03] |
| target velocity vs residual, DCT (`B_v_dct`) | 59 / 57 | -0.13 [-0.29, +0.03] | +0.01 [-0.08, +0.11] |
| x0/eps mix (Wiener weights) vs residual, per-element / DCT (`B_wiener_*`) | 57-60 | -0.07 / -0.03 | -0.06 / +0.03 |

A10 (allocation by an innovation-driven error controller, `research_v2/techC`, development set only):
- Pure error control replacing the SEA gate (C1, 64 prompts, tolerance grid did not hit the budgets exactly):
  per-element 13.36 NFE +2.76 [+1.75, +3.80] and DCT 13.11 NFE +2.05 [+1.05, +3.11] dB vs the SEA-gated KalSea at 13 NFE;
  heavy-tailed gains, per-prompt NFE varies (sd 1.6-2.4), so the mean NFE is matched but not the per-image budget.
- The gain is an allocation (schedule) effect, not a benefit of adaptivity: a FIXED schedule
  [0,1,2,3,4,6,8,11,16,23,31,42,49] (`C2_fixedavg_pe_13`, 13.00 NFE; SEA's modal schedule is
  [0,1,2,4,6,9,13,18,25,33,41,47,49]) gives +3.17 [+1.93, +4.55] dB over the SEA-gated per-element KalSea (30 prompts), and
  the matched error controller (`C2_pure_pe_t0.454`, 13.12 NFE) is -0.26 [-0.93, +0.44] dB relative to that fixed schedule
  (30 common prompts). At 18 NFE the analogous fixed schedule gives +0.55 [-0.32, +1.41] dB over SEA (30 prompts). The predictive variant (filter covariance only, `C2_pred`) is much worse: -5.07 [-6.01, -4.17] dB at 13 NFE
  and -8.44 [-10.02, -6.81] dB at 18 NFE (31 prompts).
- Caveats: C2 stopped at 30-32 of 64 prompts; the fixed schedule was apparently derived from the controller's schedules on
  these same development prompts (in-sample; the derivation is not recorded in `techC/`). Not evaluated on DrawBench.
- Reading for the paper: an innovation-driven gate does not beat a fixed schedule with the same allocation, and its
  predictive variant fails. The large schedule effect itself is a separate (allocation) question, outside this paper's
  scope (all methods in the paper share SeaCache's gate); it should not be presented as "error control is worse than SEA".

## Unit tests of the new plugin options (all pass)

CPU, no model (`research_v2/ablations/tests/test_cpu_math.py`, output `tests/test_cpu_math.out`; synthetic residuals on a
64x64 token grid, the FLUX calibration, a gate-like schedule with 9 gaps / 36 skipped steps):
- T1 Kalman RTS gains of the plugin vs brute-force joint-Gaussian conditioning of the damped-trend model (float64): max
  relative error 8e-16 (DCT bands) and 6e-16 (per-element).
- T2 `pred_lin_innov` equals pred_i + ((i-a)/(b-a)) (z_b - prior forecast at b): relative error <= 3.3e-3 (bf16 output
  rounding) for the Kalman forecaster; bitwise for linear extrapolation, whose recorded prior forecast at b equals that of an
  independent forecaster, and whose skip forecasts are unchanged by the tap (no side effects of the extra predict call).
- T3 plain reuse: `pred_lin_innov` is bitwise identical to `lin_step` (both are r_a + w (r_b - r_a)).
- T4 `apply='state_only'`: after each gap the forecaster state (m, nu, P, q-scale) is bitwise identical to a separate
  forecaster fed with z_0..z_a, r~_{a+1..b-1}, z_b; exactly one pseudo-observation per skipped step.
- T5 the identity smoother returns the forecasts bitwise.

GPU through the techA bench2 harness (`tests/gpu_tests.json`, 2 COCO development prompts, output `tests/check_gpu_tests.out`):
- U1/U2 every step computed (schedule = all 50 steps) with `state_only` / `pred_lin_innov`: images bitwise identical to the
  50-step reference (the plugin is a no-op without gaps).
- U3 identity smoother on per-element KalSea at delta 0.6: bitwise identical to the plain per-element KalSea run.
- U4 reuse + `pred_lin_innov`: bitwise identical to reuse + `lin_step` of the original `techA/pcgs.py`.
- U10 tap around the linear-extrapolation forecaster (identity smoother): bitwise identical to the run without plugin.
- U5 `state_only`: the returned output is the network's output object at every corrected step (asserted), zero
  output-layer / embedder / gate calls, #pseudo-observations (74) == #skipped steps (74); images differ from the
  uncorrected run (the variant is not a no-op; mean relative change of the trend state 4.6%).
- All runs: block-hook NFE == the forward's own count, no partial stacks, same compute schedule and NFE as the uncorrected
  control (13/13 at delta 0.6, 50 with the full schedule).
- At scale (DrawBench, `ablations/eval/nfe_check.txt`): every ablation run has 200 images, 0 NFE mismatches and 0 partial
  stacks.

## Still to run / open items

1. **A9 video ablation** (correction on/off, HunyuanVideo and Wan2.1, 20-prompt VBench subset, SeaCache's deltas
   0.19 / 0.35 and 0.2 / 0.35). Blocked on the video ports (KalSea forecaster + correction hooks in
   `video_code/*/gen_vbench.py`; Wan needs a UniPC replay of the gap instead of Euler). About 1 GPU-h for both models once
   the ports exist; the references are being generated now.
2. **Latency / TFLOPs** of every row are deliberately not in the ablation tables (owner rule: those columns stay blank in
   the main tables for now). Measured development-set overhead of the correction: +1.4-1.7% latency, about 3.4 GFLOP per
   skipped step (`research_v2/techA/RESULT.md`); a dedicated same-session timing run should re-measure exact vs batched
   re-integration when the main timing session is done.
3. **Owner decisions raised by these results** (see "Key findings"): the method description must not claim that the
   Kalman RTS gains beat plain interpolation; the gate-state refresh can be dropped or kept as a no-cost detail; the
   allocation effect seen in A10 (development set) is outside the paper's scope but is a likely reviewer question.
4. Optional if GPU time allows: A6 on DrawBench with per-element filters (only DCT was run); a quality-vs-NFE curve for
   "reuse + correction" (to show the correction alone vs the full method across budgets).

## Files

- Plugin copy with the new options: `research_v2/ablations/pcgs_abl.py` (`techA/pcgs.py` untouched).
- Configs: `research_v2/ablations/configs/drawbench_core.json`, `drawbench_extra_*.json` (our runs);
  `research_v2/techA/configs/drawbench_ablations.json` (orchestrator runs).
- Runs: `research_v2/ablations/runs/<name>/` (ours) and per-file mirrors of existing runs (`MIRROR_OF.txt` in each).
- Scores: `research_v2/ablations/eval/eval_all.{txt,json}` (all DrawBench rows, eval2 vs the reference, paired to Ours),
  `eval_devset.{txt,json}` (COCO-64), `nfe_check.txt` (hook consistency), `ablation_summary.md` (all rows + extra pairs).
- Table generator: `research_v2/ablations/make_tables.py` -> `paper/tables/tab_ablation_main.tex`,
  `paper/tables/tab_ablation_full.tex`.
- Launch with the GPU rule (>= 50 GiB free, at most one extra process per GPU, nice 10): `research_v2/ablations/launch.sh`,
  `gpu_pick.sh`; scoring: `run_final_eval.sh`.
