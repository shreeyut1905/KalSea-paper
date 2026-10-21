# Title candidates (method name: KalSea)

Written 2026-10-21 with the first full draft. CVPR titles are usually 8-14 words; all three keep "KalSea" as the
method name and say what is new (correcting skipped steps by Kalman smoothing) rather than only "faster".

1. **KalSea: Closing the Loop on Diffusion Transformer Caching with Kalman Gap Smoothing** (recommended)
   - Names the paper's central claim (existing caching fillers are open loop; we close the loop) and the mechanism
     (Kalman smoothing of the skipped gap). Short and memorable; "diffusion transformer caching" places it next to
     TeaCache, SeaCache, TaylorSeer and SpecKCast in search results.

2. **KalSea: Predictor-Corrector Kalman Smoothing of Skipped Steps for Training-Free Diffusion Transformer Acceleration**
   - Most descriptive: predictor (Kalman forecast), corrector (RTS smoothing + re-integration), training-free, DiTs.
     Longer (14 words), and "predictor-corrector" invites a comparison with UniPC/Heun that the paper does address.

3. **KalSea: Correcting Skipped Diffusion Steps at Zero Extra Cost with Kalman Smoothing**
   - Emphasizes the practical selling point (no extra transformer evaluations). Risk: "zero extra cost" is only true for
     transformer evaluations; the output-layer calls and memory are small but not zero (about 0.3% of one transformer
     evaluation per image and +0.02 GiB over the predictor alone), so a reviewer may object to the wording.

## Naming note for the owner (affects every section)

- The paper text uses the macros of `macros.tex`: `\ours` for the full method (Kalman residual forecasting + PCGS) and
  `\kalsea` for the predictor alone (SEA gate + Kalman residual forecasting, no gap smoothing). The sentences were
  written so that they read correctly with the intended final naming `\ours` -> "KalSea" and `\kalsea` -> a
  predictor-only name, e.g. "KalSea-P" or "KalSea w/o PCGS". With the current interim values ("Ours" / "KalSea") the
  abstract and introduction read "We propose Ours", and the tables label the predictor-only variant "KalSea",
  which contradicts "the method name stays KalSea".
- Change both macros in `macros.tex` and `LABEL` in `figures/src/figstyle.py` (figure legends) at the same time.
- The name KalSea was already used for the predictor-only method in a blog post / Space draft (`space_build/`). If
  that post is public, reviewers may find it; CVPR allows this, but the submission must neither cite nor link it.
  Using "KalSea" for the full method then makes the paper the extended version of the post, which is fine.
