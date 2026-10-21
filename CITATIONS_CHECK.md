# Citation check (refs.bib), 2026-10-21

Every entry in `refs.bib` (55 entries, all cited in `sections/*.tex` or `tables/*.tex`) was checked for title, authors,
venue and year against at least one primary source. No entry was written from memory alone.

**Sources used.** arXiv API (`export.arxiv.org/api/query`: title, authors, dates, author comments such as
"Accepted to CVPR 2026"); CVF open access proceedings pages (BibTeX blocks copied, keys renamed); Crossref REST API
(DOI records of IEEE, ACM, Springer, AAAI, INFORMS, ASME, AIAA, Wiley, CUP and of the NeurIPS 2022-2025 proceedings);
OpenReview API (`notes/search`, venue fields such as "ICLR 2026 Poster", plus its mirror of DBLP records);
NeurIPS and PMLR proceedings pages (citation meta tags); Semantic Scholar API (DBLP key of one paper);
mlanthology.org (one venue). DBLP itself could not be queried (bot challenge for scripted and fetched requests), so
DBLP data were read through the OpenReview / Semantic Scholar mirrors. Raw responses are cached in
`paper/.cite_cache/` (git-ignored).

## Entries

| key | paper | venue / year in refs.bib | verified via | notes |
|---|---|---|---|---|
| ma2024deepcache | DeepCache: Accelerating Diffusion Models for Free | CVPR 2024, 15762-15772 | CVF BibTeX | |
| wimbauer2024cache | Cache Me if You Can: Accelerating Diffusion Models through Block Caching | CVPR 2024, 6211-6220 | CVF BibTeX | 14 authors |
| selvaraju2024fora | FORA: Fast-Forward Caching in Diffusion Transformer Acceleration | arXiv 2407.01425 (2024) | arXiv API | no peer-reviewed version found |
| chen2024deltadit | Delta-DiT: A Training-Free Acceleration Method Tailored for Diffusion Transformers | arXiv 2406.01125 (2024) | arXiv API | from tables/tables_refs.bib (re-checked) |
| zou2025toca | Accelerating Diffusion Transformers with Token-wise Feature Caching (ToCa) | ICLR 2025 | OpenReview (ICLR 2025 Poster), arXiv | from tables/tables_refs.bib |
| ma2024learningtocache | Learning-to-Cache: Accelerating Diffusion Transformer via Layer Caching | NeurIPS 2024, vol. 37, 133282-133304 | Crossref (10.52202/079017-4236), OpenReview, arXiv | |
| zhao2025pab | Real-Time Video Generation with Pyramid Attention Broadcast | ICLR 2025 | OpenReview (ICLR 2025 Poster), arXiv comment | |
| liu2025teacache | Timestep Embedding Tells: It's Time to Cache for Video Diffusion Model | CVPR 2025, 7353-7363 | CVF BibTeX, Crossref (10.1109/cvpr52734.2025.00689) | from tables/tables_refs.bib |
| kahatapitiya2025adacache | Adaptive Caching for Faster Video Generation with Diffusion Transformers | ICCV 2025, 15240-15252 | CVF BibTeX | |
| lv2025fastercache | FasterCache: Training-Free Video Diffusion Model Acceleration with High Quality | ICLR 2025 | OpenReview (ICLR 2025 Poster), arXiv | |
| ma2025magcache | MagCache: Fast Video Generation with Magnitude-Aware Cache | NeurIPS 2025, vol. 38, 38592-38624 | Crossref (10.52202/085713-1153), OpenReview, arXiv comment | |
| bu2026dicache | DiCache: Let Diffusion Model Determine Its Own Cache | ICLR 2026 | OpenReview (ICLR 2026 Poster), arXiv | ICLR version has 7 authors (a CoRR version lists 8) |
| chu2025omnicache | OmniCache: A Trajectory-Oriented Global Perspective on Training-Free Cache Reuse for DiT Models | ICCV 2025, 16302-16312 | CVF BibTeX, arXiv comment | |
| chung2026seacache | SeaCache: Spectral-Evolution-Aware Cache for Accelerating Diffusion Models | CVPR 2026, 14283-14294 | CVF BibTeX (entry by the LaTeX-setup agent), arXiv comment | prior work (main baseline) |
| peng2026ertacache | ERTACache: Error Rectification and Timesteps Adjustment for Efficient Diffusion | ICLR 2026 | OpenReview (ICLR 2026 Poster), arXiv | author order of the ICLR version |
| liu2025taylorseer | From Reusing to Forecasting: Accelerating Diffusion Models with TaylorSeers | ICCV 2025, 15853-15863 | CVF BibTeX, arXiv comment | from tables/tables_refs.bib |
| feng2026hicache | HiCache: A Plug-in Scaled-Hermite Upgrade for Taylor-Style Cache-then-Forecast Diffusion Acceleration | ICLR 2026 | OpenReview (ICLR 2026 Poster), arXiv | |
| zheng2026foca | Forecast then Calibrate: Feature Caching as ODE for Efficient Diffusion Transformers (FoCa) | AAAI 2026, 40(16), 13449-13457 | Crossref (10.1609/aaai.v40i16.38349), AAAI OJS, OpenReview/DBLP mirror, arXiv | method checked: BDF2 predictor + Heun calibrator, past features only, no revision of skipped steps |
| han2026spectrum | Adaptive Spectral Feature Forecasting for Diffusion Sampling Acceleration (Spectrum) | CVPR 2026, 43320-43330 | CVF BibTeX, OpenReview (CVPR 2026), arXiv comment | prior work |
| shen2026gprefiner | Accelerating Diffusion Transformers with Gaussian Process Rectified Feature Cache (GP-Refiner) | ECCV 2026 | arXiv API (2609.05981, posted 2026-09-05, "Accepted by ECCV 2026") | posted before Sep 15, 2026, so prior work; proceedings pages not yet available; method checked: forward-only correction of forecast features, no revision of skipped steps |
| liu2025speca | SpeCa: Accelerating Diffusion Transformers with Speculative Feature Caching | ACM MM 2025, 10024-10033 | Crossref (10.1145/3746027.3755331), arXiv | |
| rajabi2026speckcast | SpecKCast: Spectral Kalman Forecasting for Diffusion Acceleration | arXiv 2610.26837 (2026) | arXiv API (posted 2026-10-19); full text in KalSea-dev/SpecKCast_paper_2610.26837.txt | contemporaneous (after Sep 15, 2026); our predictor uses its state-space model, stated in Sec. 3.2 and Related Work |
| kalman1960new | A New Approach to Linear Filtering and Prediction Problems | J. Basic Eng. 82(1):35-45, 1960 | Crossref (10.1115/1.3662552) | |
| rauch1965maximum | Maximum Likelihood Estimates of Linear Dynamic Systems | AIAA J. 3(8):1445-1450, 1965 | Crossref (10.2514/3.3166) | |
| sarkka2013bayesian | Bayesian Filtering and Smoothing | Cambridge University Press, 2013 | Crossref (10.1017/CBO9781139344203, single author) | |
| barshalom2001estimation | Estimation with Applications to Tracking and Navigation | Wiley, 2001 | Crossref (10.1002/0471221279, 3 authors) | Crossref gives the online date 2002-01-04; print edition 2001 |
| mehra1972approaches | Approaches to Adaptive Filtering | IEEE TAC 17(5):693-698, 1972 | Crossref (10.1109/TAC.1972.1100100) | author as in Crossref ("R. Mehra") |
| gardner1985forecasting | Forecasting Trends in Time Series | Management Science 31(10):1237-1246, 1985 | Crossref (10.1287/mnsc.31.10.1237) | damped-trend smoothing |
| schober2019probabilistic | A Probabilistic Model for the Numerical Solution of Initial Value Problems | Stat. Comput. 29(1):99-122, 2019 | Crossref (10.1007/s11222-017-9798-7), arXiv | online 2018, issue 2019 |
| tronarp2019probabilistic | Probabilistic Solutions to ODEs as Nonlinear Bayesian Filtering: A New Perspective | Stat. Comput. 29(6):1297-1315, 2019 | Crossref (10.1007/s11222-019-09900-1), arXiv | |
| song2021score | Score-Based Generative Modeling through Stochastic Differential Equations | ICLR 2021 | arXiv comment ("ICLR 2021 (Oral)") | abstract confirms the predictor-corrector sampler |
| song2021ddim | Denoising Diffusion Implicit Models | ICLR 2021 | arXiv comment ("ICLR 2021") | |
| lu2022dpmsolver | DPM-Solver: A Fast ODE Solver for Diffusion Probabilistic Model Sampling in Around 10 Steps | NeurIPS 2022, vol. 35, 5775-5787 | Crossref (10.52202/068431-0418), arXiv comment | |
| lu2025dpmsolverpp | DPM-Solver++: Fast Solver for Guided Sampling of Diffusion Probabilistic Models | Machine Intelligence Research 22(4):730-751, 2025 | Crossref (10.1007/s11633-025-1562-4), arXiv comment | cited as a multistep solver (it has no corrector of its own; UniPC's corrector applies to it) |
| zhao2023unipc | UniPC: A Unified Predictor-Corrector Framework for Fast Sampling of Diffusion Models | NeurIPS 2023, vol. 36, 49842-49869 | Crossref (10.52202/075280-2170), OpenReview, arXiv | abstract confirms "corrector ... without extra model evaluations" |
| karras2022edm | Elucidating the Design Space of Diffusion-Based Generative Models | NeurIPS 2022, vol. 35, 26565-26577 | NeurIPS proceedings page, Crossref (10.52202/068431-1926) | Heun sampler |
| lipman2023flow | Flow Matching for Generative Modeling | ICLR 2023 | arXiv API; venue from mlanthology.org (iclr/2023) | OpenReview API blocked for this query |
| liu2023rectifiedflow | Flow Straight and Fast: Learning to Generate and Transfer Data with Rectified Flow | ICLR 2023 | arXiv API; Semantic Scholar (DBLP key conf/iclr/LiuG023) | |
| albergo2023interpolants | Building Normalizing Flows with Stochastic Interpolants | ICLR 2023 | arXiv comment ("ICLR 2023") | |
| esser2024scaling | Scaling Rectified Flow Transformers for High-Resolution Image Synthesis | ICML 2024, PMLR 235, 12606-12633 | PMLR page, OpenReview (ICML 2024 Oral) | 14 authors (proceedings list) |
| ho2022cfg | Classifier-Free Diffusion Guidance | arXiv 2207.12598 (2022) | arXiv API | |
| peebles2023dit | Scalable Diffusion Models with Transformers | ICCV 2023, 4195-4205 | CVF BibTeX | SpecKCast's reference list gives other pages; CVF is authoritative |
| blackforestlabs2024flux | FLUX (Black Forest Labs) | software, 2024 | GitHub repository black-forest-labs/flux exists (HTTP 200) | cited without URL (CVPR rules) |
| kong2024hunyuanvideo | HunyuanVideo: A Systematic Framework For Large Video Generative Models | arXiv 2412.03603 (2024) | arXiv API | from tables/tables_refs.bib |
| wan2025wan | Wan: Open and Advanced Large-Scale Video Generative Models | arXiv 2503.20314 (2025) | arXiv API | from tables/tables_refs.bib |
| saharia2022imagen | Photorealistic Text-to-Image Diffusion Models with Deep Language Understanding (Imagen; DrawBench) | NeurIPS 2022, vol. 35, 36479-36494 | Crossref (10.52202/068431-2643), OpenReview/DBLP mirror | 13 authors in the NeurIPS version (arXiv v1 lists 14) |
| huang2024vbench | VBench: Comprehensive Benchmark Suite for Video Generative Models | CVPR 2024, 21807-21818 | CVF BibTeX | |
| zhang2018lpips | The Unreasonable Effectiveness of Deep Features as a Perceptual Metric | CVPR 2018, 586-595 | CVF BibTeX (no pages), Crossref (10.1109/CVPR.2018.00068) | |
| wang2004ssim | Image Quality Assessment: From Error Visibility to Structural Similarity | IEEE TIP 13(4):600-612, 2004 | Crossref (10.1109/TIP.2003.819861) | |
| lin2014coco | Microsoft COCO: Common Objects in Context | ECCV 2014, 740-755 | Crossref (10.1007/978-3-319-10602-1_48), arXiv | 8 authors in the ECCV version |
| salimans2022progressive | Progressive Distillation for Fast Sampling of Diffusion Models | ICLR 2022 | arXiv comment ("Published as a conference paper at ICLR 2022") | |
| song2023consistency | Consistency Models | ICML 2023, PMLR 202, 32211-32252 | PMLR page, arXiv comment | |
| luo2023lcm | Latent Consistency Models | arXiv 2310.04378 (2023) | arXiv API | |
| sauer2024add | Adversarial Diffusion Distillation | ECCV 2024, 87-103 | Crossref (10.1007/978-3-031-73016-0_6) | |
| li2023qdiffusion | Q-Diffusion: Quantizing Diffusion Models | ICCV 2023, 17535-17545 | CVF BibTeX | |

## Claims about cited work that were checked against the source

- SeaCache: gate = TeaCache's accumulate-and-reset rule on the first block's modulated input, measured after the SEA
  filter (Wiener-type gain with a power-law spectrum, unit-mean normalization; beta = 2 images, 3 videos); Table 1:
  delta = 0.6 gives PSNR 21.332 at 773 TFLOPs, original 50 steps = 2976 TFLOPs (paper text in KalSea-dev/).
- SpecKCast: DCT of the model output, per-coefficient damped-trend Kalman filters, band-specific warped log-SNR time,
  band-shared covariances, uncertainty-based scheduling; ablation: removing the frequency decomposition costs 3.1 dB at
  14 NFE on FLUX (paper text in KalSea-dev/).
- FoCa, GP-Refiner: neither revises the latent of already-skipped steps (checked in the arXiv HTML versions).
- UniPC: corrector "without extra model evaluations" (arXiv abstract). Score SDE: predictor-corrector sampler
  (arXiv abstract). AdaCache, MagCache, DiCache, OmniCache, SpeCa, ERTACache: one-line descriptions checked against
  their arXiv abstracts.

## Literature searches for missing related work

- Queries (web search and arXiv): retrospective / retroactive correction of skipped steps in diffusion caching;
  Kalman filter or smoother for feature caching; predictor-corrector feature caching. Found and added: FoCa (AAAI
  2026), GP-Refiner (ECCV 2026, posted 2026-09-05), ERTACache (ICLR 2026), SpeCa (ACM MM 2025), OmniCache (ICCV 2025).
  No prior method that smooths a skipped gap and re-integrates the latent was found; the paper therefore says "none
  revises the latent of steps that have already been skipped" only about the methods it cites.
- Seen but not cited (space): FreqCa (arXiv 2510.08669), EOC (ACM MM 2025), ProCache (AAAI 2026), CacheScope (arXiv
  2610.12530, posted 2026-10-08, contemporaneous), the cache survey arXiv 2510.19755. Add if reviewers ask.
- Not used because the record could not be fully verified: Hairer, Norsett, Wanner, "Solving Ordinary Differential
  Equations I" (Crossref has the book, DOI 10.1007/978-3-540-78862-1, but no author list; Springer page blocked).
