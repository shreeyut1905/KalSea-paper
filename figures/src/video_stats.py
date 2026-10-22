#!/usr/bin/env python3
"""Collect the video results used by the tables into data/*.json (keyed by model / budget / method, no paths).

    python video_stats.py      -> data/video_stats.json  (main paper, Tab. 2)
                                  data/video_supp.json   (supplementary material: same-setup comparisons, schedules,
                                                          gate correction, budget matching, 20-prompt ablations and
                                                          budget sweep, reproducibility checks)

Reads the full-reference evaluations listed in data_sources.VIDEO_FR (and the other VIDEO_* entries), the per-video
stats of the run folders (computed steps, gate distances; read only) and the 20-prompt ablation summary
data_sources.VIDEO_ABL. A model whose evaluation file does not exist yet has only its delta, and make_tables.py prints
\\tbd for it.
"""
import glob
import json
import os

import numpy as np

import data_sources as DS

HERE = os.path.dirname(os.path.abspath(__file__))


def pick(s):
    return {"n": s["n"], "nfe": s["nfe"], "psnr": s["psnr"], "ssim": s["ssim"], "lpips": s["lpips"]}


def pair(p):
    """paired difference record (A minus B over videos): mean, 95% CI and fraction of videos where A is better."""
    return {k: {"mean": p[k]["mean"], "ci95": list(p[k]["ci95"]), "frac_better": p[k]["frac_better"]}
            for k in ("psnr", "ssim", "lpips")} | {"n": p["n"]}


def main_table():
    out = {}
    for model, budgets in DS.VIDEO_RUNS.items():
        out[model] = {}
        for b, (delta, ours, sea, *fr) in budgets.items():
            path = fr[0] if fr else DS.VIDEO_FR.get(model)
            out[model][b] = {"delta": delta}
            if not path or not os.path.exists(path):
                print(f"{model} {b}: no evaluation yet ({path})")
                continue
            R = json.load(open(path))
            S = R["summary"]
            assert S[ours]["n"] == S[sea]["n"] == 944, (model, b, S[ours]["n"], S[sea]["n"])
            out[model][b].update(ours=pick(S[ours]), seacache_rerun=pick(S[sea]),
                                 ours_minus_seacache_rerun=R["pairs"][f"{ours}-{sea}"])
            print(f"{model} {b}: delta {delta}, Ours {S[ours]['psnr']:.2f} dB at {S[ours]['nfe']:.2f} NFE")
    out["extra"] = {}
    for key, (path, run) in getattr(DS, "VIDEO_EXTRA", {}).items():
        if os.path.exists(path):
            out["extra"][key] = pick(json.load(open(path))["summary"][run])
    json.dump(out, open(os.path.join(HERE, "data", "video_stats.json"), "w"), indent=1)


# ------------------------------------------------------------------------------------------- supplementary material
def load_stats(model, cfg):
    """per-video stats of a run folder (read only): {file: record}; exactly one record per prompt."""
    rows = {}
    for f in sorted(glob.glob(os.path.join(DS.VIDEO_ROOT[model], cfg + "_meta", "stats", "*.jsonl"))):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                assert r["file"] not in rows, (cfg, r["file"])
                rows[r["file"]] = r
    return rows


def steps_of(model, r):
    c = r["cache"]
    if model == "hunyuan":
        return c["compute_steps"]
    # Wan2.1: conditional and unconditional passes have separate gate accumulators; the bookkeeping check requires the
    # block hooks of both passes and the gate to agree (checked below)
    assert c["hook_compute_steps_cond"] == c["hook_compute_steps_uncond"] == c["gate_compute_steps"], r["file"]
    assert c["nfe_forwards"] == 2 * c["nfe"] and c["gate_streams_agree"], r["file"]
    return c["hook_compute_steps_cond"]


def schedules(model, ours, sea):
    A, B = load_stats(model, ours), load_stats(model, sea)
    assert len(A) == len(B) == 944 and set(A) == set(B), (model, ours, sea, len(A), len(B))
    fs = sorted(A)
    na = np.array([A[f]["cache"]["nfe"] for f in fs], float)
    nb = np.array([B[f]["cache"]["nfe"] for f in fs], float)
    hist = lambda x: {str(int(v)): int(c) for v, c in zip(*np.unique(x, return_counts=True))}
    return {"n": len(fs), "n_identical_steps": int(sum(steps_of(model, A[f]) == steps_of(model, B[f]) for f in fs)),
            "n_equal_nfe": int((na == nb).sum()), "max_abs_dnfe": float(np.abs(na - nb).max()),
            "nfe_hist_ours": hist(na), "nfe_hist_seacache": hist(nb),
            "n_step1_ours": int(sum(1 in steps_of(model, A[f]) for f in fs)),
            "n_step1_seacache": int(sum(1 in steps_of(model, B[f]) for f in fs))}


def same_setup():
    out = {}
    for model, budgets in DS.VIDEO_RUNS.items():
        out[model] = {}
        for b, (delta, ours, sea, *fr) in budgets.items():
            R = json.load(open(fr[0] if fr else DS.VIDEO_FR[model]))
            S = R["summary"]
            out[model][b] = {"delta": delta, "ours": pick(S[ours]), "seacache": pick(S[sea]),
                             "ours_minus_seacache": pair(R["pairs"][f"{ours}-{sea}"]),
                             "schedules": schedules(model, ours, sea)}
            s = out[model][b]["schedules"]
            print(f"{model} {b}: identical steps {s['n_identical_steps']}/{s['n']}, equal NFE {s['n_equal_nfe']}, "
                  f"max |dNFE| {s['max_abs_dnfe']:g}")
    return out


def hv_first_lo():
    delta, ours, sea = DS.VIDEO_HV_FIRST_LO
    R = json.load(open(DS.VIDEO_FR["hunyuan"]))
    S = R["summary"]
    return {"delta": delta, "ours": pick(S[ours]), "seacache": pick(S[sea]),
            "ours_minus_seacache": pair(R["pairs"][f"{ours}-{sea}"]), "schedules": schedules("hunyuan", ours, sea)}


def gate():
    """HunyuanVideo: SeaCache's released gate (stale scheduler) vs. the corrected gate (sampler's noise level)."""
    R = json.load(open(DS.VIDEO_RELEASED_FR))
    A7 = json.load(open(DS.VIDEO_ABL))["models"]["hunyuan"]["gate_fix_A7"]["budgets"]
    out = {"released": {}, "corrected_minus_released": {}}
    for b, key in (("hi", "~24 NFE"), ("lo", "16 NFE")):
        delta, ours, sea = DS.VIDEO_RELEASED[b]
        S = R["summary"]
        assert S[ours]["n"] == S[sea]["n"] == 944
        out["released"][b] = {"delta": delta, "ours": pick(S[ours]), "seacache": pick(S[sea]),
                              "ours_minus_seacache": pair(R["pairs"][f"{ours}-{sea}"]),
                              "schedules": schedules("hunyuan", ours, sea)}
        f = A7[key]["full944"]
        assert f["seacache"]["released"]["config"] == sea and f["ours"]["released"]["config"] == ours
        assert f["seacache"]["corrected"]["config"] == DS.VIDEO_RUNS["hunyuan"][b][2]
        out["corrected_minus_released"][b] = {m: pair(f[m]["corrected_minus_released"]) for m in ("seacache", "ours")}
    # step 1 with the released gate at the ~24-NFE threshold: prompts that skip it vs. prompts that compute it
    delta, ours, sea = DS.VIDEO_RELEASED["hi"]
    L = json.load(open(DS.VIDEO_FR["hunyuan"]))
    st = {}
    for m, rel, cor in (("seacache", sea, DS.VIDEO_RUNS["hunyuan"]["hi"][2]), ("ours", ours, DS.VIDEO_RUNS["hunyuan"]["hi"][1])):
        rows = load_stats("hunyuan", rel)
        pr, pc = R["per_video"][rel], L["per_video"][cor]
        skip = sorted(f for f in rows if 1 not in rows[f]["cache"]["compute_steps"])
        comp = sorted(f for f in rows if 1 in rows[f]["cache"]["compute_steps"])
        st[m] = {"n_skip": len(skip), "n_compute": len(comp),
                 "psnr_skip": float(np.mean([pr[f]["psnr"] for f in skip])),
                 "psnr_compute": float(np.mean([pr[f]["psnr"] for f in comp])),
                 "corrected_minus_released_skip": float(np.mean([pc[f]["psnr"] - pr[f]["psnr"] for f in skip])),
                 "corrected_minus_released_compute": float(np.mean([pc[f]["psnr"] - pr[f]["psnr"] for f in comp]))}
    assert st["seacache"]["n_skip"] == st["ours"]["n_skip"]
    # step-1 gate distance with the stale and with the live noise level (identical up to step 1 for all methods)
    d_rel = np.array([r["cache"]["gate_dist"][1] for r in load_stats("hunyuan", sea).values()])
    d_live = np.array([r["cache"]["gate_dist"][1] for r in load_stats("hunyuan", DS.VIDEO_RUNS["hunyuan"]["hi"][2]).values()])
    pub_delta = 0.19   # SeaCache's published HunyuanVideo thresholds (its Table 3)
    st.update(delta=delta, d1_released=[float(d_rel.min()), float(d_rel.max())], d1_live=[float(d_live.min()), float(d_live.max())],
              n_skip_at_pub_hi=int((d_rel < pub_delta).sum()), n_skip_at_021=int((d_rel < 0.21).sum()), n=int(len(d_rel)))
    out["step1"] = st
    # corrected gate: at step 0 of every video, the gate's noise levels were compared with the sampler's (recorded flag)
    n_live = n_eq = 0
    for b in ("hi", "lo"):
        for cfg in DS.VIDEO_RUNS["hunyuan"][b][1:3]:
            for r in load_stats("hunyuan", cfg).values():
                n_live += 1
                n_eq += bool(r["cache"].get("live_sigma") and r["cache"].get("gate_sigmas_equal_live"))
    out["live_check"] = {"n_videos": n_live, "n_equal": n_eq}
    P = json.load(open(DS.VIDEO_HV_PILOT[0]))["summary"][DS.VIDEO_HV_PILOT[1]]
    out["released_pub_delta_pilot"] = {"delta": "0.19", "n": P["n"], "nfe": P["nfe"]}
    return out


def determinism():
    """bit-identical re-generations: full runs vs. earlier pilot runs (fr_metrics 'determinism') and the default-path
    check after the ablation options were added (VIDEO_ABL provenance)."""
    recs = []
    for model, path in (("hunyuan", DS.VIDEO_FR["hunyuan"]), ("hunyuan", DS.VIDEO_RELEASED_FR), ("wan", DS.VIDEO_FR["wan"])):
        for k, v in json.load(open(path)).get("determinism", {}).items():
            if v.get("kind") != "bitwise":
                continue
            s = v["summary"]
            ok = min(s["mp4_bytes_equal"], s["videos_all_frames_equal"], s["steps_equal"])
            recs.append({"model": model, "check": k.split("_vs_")[0], "n": s["n"], "n_bitwise": ok})
    A = json.load(open(DS.VIDEO_ABL))["provenance"]["default_path_bitwise_check"]
    after = [{"model": r["model"], "config": r["config"],
              "bitwise": bool(r["mp4_bytes_equal"] and r["frames_equal"] and r["steps_equal"])} for r in A["records"]]
    return {"rerun_vs_pilot": recs, "after_ablation_code": after}


def ablations():
    A = json.load(open(DS.VIDEO_ABL))
    keys = ("ours", "seacache", "pcgs_lin", "pcgs_stateonly", "reuse_pcgs", "linextrap", "linextrap_pcgs")
    out = {"meta": {k: A["meta"][k] for k in ("metrics", "ci")}, "models": {}}
    for model, M in A["models"].items():
        mm = {"n_prompts": len(M["subset_idx"]), "bookkeeping_mismatches": M["bookkeeping_mismatches"], "budgets": {},
              "sweep": []}
        for delta, B in M["budgets"].items():
            rec = {"delta": delta, "configs": {}}
            for k in keys:
                c = B[k]
                r = {"ablation": c["ablation"], "n": c["n"], "nfe": c["nfe"], "psnr": c["psnr"], "ssim": c["ssim"],
                     "lpips": c["lpips"]}
                if k == "ours":
                    r["vs_seacache"] = pair(c["vs_seacache"])
                else:
                    r["vs_ours"] = pair(c["vs_ours"])
                    chk = c["nfe_check_vs_ours"]
                    r["n_identical_schedules"] = chk["n_identical_schedules"]
                    r["n_nfe_mismatch"] = chk["n_nfe_mismatch"]
                rec["configs"][k] = r
            rec["pcgs_gain"] = {"reuse": pair(B["_extra_pairs"]["reuse_pcgs-seacache"]),
                                "linext": pair(B["_extra_pairs"]["linextrap_pcgs-linextrap"])}
            mm["budgets"][delta] = rec
        for s in M["sweep"]:
            chk = s["nfe_check_ours_vs_seacache"]
            mm["sweep"].append({"delta": s["delta"], "nfe_seacache": s["seacache"]["nfe"], "nfe_ours": s["ours"]["nfe"],
                                "seacache": {k: s["seacache"][k] for k in ("psnr", "psnr_ci95", "ssim", "lpips")},
                                "ours": {k: s["ours"][k] for k in ("psnr", "psnr_ci95", "ssim", "lpips")},
                                "ours_minus_seacache": pair(s["ours_minus_seacache"]),
                                "n_identical_schedules": chk["n_identical_schedules"],
                                "n_nfe_mismatch": chk["n_nfe_mismatch"], "max_abs_dnfe": chk["max_abs_dnfe"]})
        mm["sweep"].sort(key=lambda s: s["nfe_ours"])
        out["models"][model] = mm
    return out


def supp():
    out = {"same_setup": same_setup(), "hv_first_lo": hv_first_lo(), "gate": gate(), "determinism": determinism(),
           "ablations": ablations()}
    json.dump(out, open(os.path.join(HERE, "data", "video_supp.json"), "w"), indent=1)
    print("wrote", os.path.join(HERE, "data", "video_supp.json"))


if __name__ == "__main__":
    main_table()
    supp()
