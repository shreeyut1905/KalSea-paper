#!/usr/bin/env python3
"""Supplementary figure: budget sweep on video (20 prompts per model, same SEA gate for SeaCache and Ours).

(a, c) PSNR w.r.t. the 50-step reference vs. NFE for our same-setup SeaCache re-run and Ours (mean over the 20 videos,
shaded band = 95% bootstrap CI of the mean); (b, d) paired PSNR gain of Ours over SeaCache with 95% bootstrap CIs.
Gray bands: the two budgets of the main paper's video table. Reads data/video_supp.json and data/video_stats.json
(run video_stats.py first); style: figstyle.py (same colors and markers as the FLUX trade-off figure).

    python fig_video_sweep.py      -> figures/fig_video_sweep.{pdf,png}   (one column, 2 x 2 panels)
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import figstyle as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.dirname(HERE)
LABEL = {**S.LABEL, "seacache": "SeaCache (re-run)"}
MODELS = (("hunyuan", "HunyuanVideo"), ("wan", "Wan2.1"))


def load():
    VS = json.load(open(os.path.join(HERE, "data", "video_supp.json")))
    V = json.load(open(os.path.join(HERE, "data", "video_stats.json")))
    out = {}
    for m, _ in MODELS:
        sw = sorted(VS["ablations"]["models"][m]["sweep"], key=lambda s: s["nfe_ours"])
        main = [float(V[m][b]["delta"]) for b in ("hi", "lo")]
        out[m] = dict(sweep=sw, main_nfe=[s["nfe_ours"] for s in sw if any(abs(s["delta"] - d) < 1e-9 for d in main)])
        assert len(out[m]["main_nfe"]) == 2, (m, main)
    return out


def bands(ax, xs):
    for x in xs:
        ax.axvspan(x - 0.55, x + 0.55, color=S.BAND, zorder=0, lw=0)


def ticks(ax, sw):
    xs = [s["nfe_ours"] for s in sw]
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{x:.0f}" if abs(x - round(x)) < 0.1 else f"{x:.1f}" for x in xs])
    ax.set_xlim(8.3, 30.8)
    ax.grid(axis="x", visible=False)


def psnr_panel(ax, d):
    sw = d["sweep"]
    for m in ("seacache", "ours"):
        x = [s["nfe_seacache" if m == "seacache" else "nfe_ours"] for s in sw]
        y = [s[m]["psnr"] for s in sw]
        lo = [s[m]["psnr_ci95"][0] for s in sw]
        hi = [s[m]["psnr_ci95"][1] for s in sw]
        ax.fill_between(x, lo, hi, color=S.C[m], alpha=0.12, lw=0, zorder=S.ZORDER[m] - 2)
        ax.plot(x, y, color=S.C[m], lw=1.6 if m == "ours" else 1.2, zorder=S.ZORDER[m], marker=S.MARKER[m],
                ms=S.MSIZE[m], mfc=S.C[m], mec="white", mew=0.6)
    bands(ax, d["main_nfe"])
    ticks(ax, sw)
    ax.set_ylabel(r"PSNR (dB) $\uparrow$", labelpad=2)


def gain_panel(ax, d):
    sw = d["sweep"]
    ax.axhline(0, color=S.AXIS, lw=0.6, zorder=1)
    x = [s["nfe_ours"] for s in sw]
    y = [s["ours_minus_seacache"]["psnr"]["mean"] for s in sw]
    yerr = [[s["ours_minus_seacache"]["psnr"]["mean"] - s["ours_minus_seacache"]["psnr"]["ci95"][0] for s in sw],
            [s["ours_minus_seacache"]["psnr"]["ci95"][1] - s["ours_minus_seacache"]["psnr"]["mean"] for s in sw]]
    b = "seacache"   # the gain is drawn in the color and marker of the baseline it is measured against
    ax.plot(x, y, color=S.C[b], lw=1.2, zorder=S.ZORDER[b], marker=S.MARKER[b], ms=S.MSIZE[b], mfc=S.C[b],
            mec="white", mew=0.6)
    ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor=S.C[b], elinewidth=0.8, capsize=1.6, capthick=0.8,
                zorder=S.ZORDER[b] - 1)
    for s, xx, yy in zip(sw, x, y):   # direct labels only at the two budgets of the main table
        if any(abs(xx - mx) < 1e-9 for mx in d["main_nfe"]):
            top = s["ours_minus_seacache"]["psnr"]["ci95"][1]
            ax.annotate(f"{yy:+.2f}".replace("-", "$-$"), (xx, top), xytext=(0, 2.5), textcoords="offset points",
                        ha="center", va="bottom", fontsize=6.5, color=S.INK)
    bands(ax, d["main_nfe"])
    ticks(ax, sw)
    ax.set_ylabel(r"$\Delta$PSNR (dB)", labelpad=2)


def main():
    S.apply()
    data = load()
    # one column, 2 x 2: rows = models, columns = PSNR and paired gain (panels as wide as in a 4-panel full-width row)
    fig, axes = plt.subplots(2, 2, figsize=(S.COL_W, 3.30), gridspec_kw=dict(wspace=0.46, hspace=0.62))
    fig.subplots_adjust(left=0.125, right=0.985, bottom=0.095, top=0.885)
    for i, (m, name) in enumerate(MODELS):
        psnr_panel(axes[i, 0], data[m])
        gain_panel(axes[i, 1], data[m])
        axes[i, 0].set_title(rf"({'ac'[i]}) {name}: PSNR", loc="left", fontsize=7.5, pad=4, color=S.INK)
        axes[i, 1].set_title(rf"({'bd'[i]}) {name}: gain", loc="left", fontsize=7.5, pad=4, color=S.INK)
    # same y-range for the two PSNR panels and for the two gain panels (comparable across models); headroom for the
    # direct labels above the confidence intervals
    lo = min(a.get_ylim()[0] for a in axes[:, 0]); hi = max(a.get_ylim()[1] for a in axes[:, 0])
    for a in axes[:, 0]:
        a.set_ylim(lo, hi)
    ci = [s["ours_minus_seacache"]["psnr"]["ci95"] for m, _ in MODELS for s in data[m]["sweep"]]
    glo, ghi = min(c[0] for c in ci) - 0.3, max(c[1] for c in ci) + 1.0
    for a in axes[:, 1]:
        a.set_ylim(glo, ghi)
    for a in axes.ravel():
        a.set_xlabel("NFE (of 50)", labelpad=1.5)
    handles = [Line2D([], [], color=S.C[k], lw=1.6 if k == "ours" else 1.2, marker=S.MARKER[k], ms=S.MSIZE[k] + 0.4,
                      mfc=S.C[k], mec="white", mew=0.6, label=LABEL[k]) for k in ("seacache", "ours")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=2, columnspacing=1.6,
               handlelength=2.0, borderaxespad=0.0)
    S.save(fig, os.path.join(FIG_DIR, "fig_video_sweep"))
    plt.close(fig)
    print("wrote", os.path.join(FIG_DIR, "fig_video_sweep.pdf"))


if __name__ == "__main__":
    main()
