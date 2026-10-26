#!/usr/bin/env python3
"""cost_stats.py: TFLOPs and latency of one example per configuration of the main tables -> data/cost.json.

    python cost_stats.py

Per model ("flux", "hunyuan", "wan") and entry ("ref", "<budget>_seacache", "<budget>_ours"): nfe, latency (s, timed call
after one warm-up call of the same prompt), tflops (Calflops convention: 2 x MACs of linear / conv / matmul in the sampling
loop, attention core not counted; text encoders and VAE excluded), tflops_attn (attention core, for reference). Missing
measurements are omitted (the table prints \\nodata).
"""
import ast
import glob
import json
import os
import statistics

from data_sources import COST_BASELINES, COST_CONFIGS, COST_DIR, COST_VIDEO_PROMPT

HERE = os.path.dirname(os.path.abspath(__file__))


def one(model, cfg):
    rec = {}
    st = sorted(glob.glob(f"{COST_DIR}/out/latency/{model}/{cfg}/stats*.jsonl"))
    lines = [json.loads(l) for f in st for l in open(f) if l.strip()]
    if len(lines) >= 2:
        rec.update(latency=statistics.median(r["latency"] for r in lines[1:]), latency_calls=[r["latency"] for r in lines],
                   nfe=lines[1]["nfe"], prompt=lines[1]["prompt"])
    fj = f"{COST_DIR}/out/flops_{model}_{cfg}.json"
    if os.path.exists(fj):
        F = json.load(open(fj))
        rec.update(tflops=F["tflops_calflops"], tflops_attn=F["tflops_attention_core"],
                   tflops_outside_forward=F["tflops_outside_denoiser_forward"])
    return rec


out = {}
for key, C in COST_CONFIGS.items():
    m = C.get("model", key)
    out[key] = {"ref": one(m, C["ref"])}
    for b in ("hi", "lo"):
        sc, ours = C[b]
        out[key][f"{b}_seacache"] = one(m, sc)
        out[key][f"{b}_ours"] = one(m, ours)


def baseline(model, run):
    """Latency of one published baseline: FLUX = median of the timed calls (call 0 = warm-up); video = the example
    (the driver's first prompt is the warm-up)."""
    B = f"{COST_DIR}/out/latency_bl/{model}/{run}"
    if model == "flux":
        L = [json.loads(l) for l in open(f"{B}/stats.jsonl")] if os.path.exists(f"{B}/stats.jsonl") else []
        if len(L) < 2:
            return {}
        return dict(latency=statistics.median(r["latency"] for r in L[1:]), latency_calls=[r["latency"] for r in L],
                    nfe=L[-1]["nfe"], prompt=L[-1]["prompt"])
    for f in glob.glob(f"{B}_meta/stats/*.jsonl"):
        for l in open(f):
            r = json.loads(l)
            if r.get("prompt") == COST_VIDEO_PROMPT and r.get("ok", True) is not False:
                c = r.get("cache")
                c = ast.literal_eval(c) if isinstance(c, str) else (c or {})
                return dict(latency=float(r["gen_s"]), nfe=c.get("nfe", r.get("nfe")), prompt=r["prompt"])
    return {}


out["baselines"] = {"flux": {k: baseline("flux", v) for k, v in COST_BASELINES["flux"].items()}}
for key, model in (("hunyuan", "hv"), ("wan", "wan")):
    out["baselines"][key] = {b: {k: baseline(model, v) for k, v in COST_BASELINES[key][b].items()} for b in ("hi", "lo")}
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "data", "cost.json"), "w"), indent=1)
for k, v in out.items():
    if k == "baselines":
        print(json.dumps({m: {b: {kk: (round(vv.get("latency", -1), 2), vv.get("nfe")) for kk, vv in x.items()}
                              if b in ("hi", "lo") else (round(x.get("latency", -1), 2), x.get("nfe"))
                              for b, x in d.items()} for m, d in v.items()}, indent=0))
        continue
    for e, r in v.items():
        print(f"{k:8s} {e:13s} nfe={r.get('nfe')} lat={r.get('latency', float('nan')):.2f}s "
              f"tflops={r.get('tflops', float('nan')):.1f} attn={r.get('tflops_attn', float('nan')):.1f}")
