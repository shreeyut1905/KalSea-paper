#!/usr/bin/env python3
"""Fig. (quality-compute trade-off on FLUX.1-dev, DrawBench-200).

(a) PSNR and (b) LPIPS w.r.t. the 50-step reference vs. NFE for SeaCache and Ours over the delta sweep (mean over 200
prompts, shaded band = 95% bootstrap CI of the mean), plus the other baselines of Tab. 1 as gray markers (two budgets
each, bars = 95% bootstrap CI); (c) paired PSNR gain of Ours over SeaCache with 95% bootstrap CIs.
Reads figures/src/data/flux_drawbench_stats.json (run flux_stats.py first) and data/flux_baselines.json
(collect_flux_baselines.py).

    python fig_tradeoff.py            # full width (\\textwidth), 3 panels  -> figures/fig_tradeoff.{pdf,png}
    python fig_tradeoff.py --onecol   # one column, 2x2 grid variant         -> figures/fig_tradeoff_1col.{pdf,png}
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

import figstyle as S  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.dirname(HERE)
METHODS = ("seacache", "ours")   # main comparison: KalSea vs SeaCache (the predictor-only ablation is in Tab. 3 / supplement)
# SeaCache curve = our same-setup re-run of its released gate + reuse (the main table cites its published numbers)
LABEL = dict(S.LABEL)
# other baselines of Tab. 1 (data/flux_baselines.json): neutral gray, one marker shape each, identified in the legend
BASELINES = (("spectrum", "Spectrum", "^"), ("sada", "SADA", "v"), ("teacache", "TeaCache", "P"),
             ("taylorseer", "TaylorSeer", "X"), ("vanilla", "Fewer steps", "p"))
BASE_C = S.INK2
MAIN_BUDGETS = {"0.37": r"$\delta\!=\!0.37$", "0.6": r"$\delta\!=\!0.6$"}   # budgets of the main table (18.1 / 13 NFE)


def load():
    st = json.load(open(os.path.join(HERE, "data", "flux_drawbench_stats.json")))
    deltas = st["deltas"]
    series = {}
    for m in METHODS:
        rows = [(d, st["summary"][d][m]["nfe"], st["summary"][d][m]["psnr"], st["summary"][d][m]["lpips"]) for d in deltas]
        rows.sort(key=lambda t: t[1])
        series[m] = rows
    gains = {}
    for key, base in (("ours-seacache", "seacache"),):
        rows = []
        for d in deltas:
            p = st["paired"][d][key]["psnr"]
            rows.append((d, st["summary"][d]["ours"]["nfe"], p["mean"], p["ci95"]))
        rows.sort(key=lambda t: t[1])
        gains[base] = rows
    budget_nfe = {d: st["summary"][d]["ours"]["nfe"] for d in deltas}
    return series, gains, budget_nfe


def load_baselines():
    return json.load(open(os.path.join(HERE, "data", "flux_baselines.json")))["methods"]


def baseline_points(ax, key):
    for m, _, mk in BASELINES:
        pts = sorted(BL[m], key=lambda p: p["nfe"])
        x = [p["nfe"] for p in pts]
        y = [p[key]["mean"] for p in pts]
        yerr = [[p[key]["mean"] - p[key]["ci95"][0] for p in pts], [p[key]["ci95"][1] - p[key]["mean"] for p in pts]]
        ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor=BASE_C, elinewidth=0.5, capsize=0, zorder=2, alpha=0.7)
        ax.plot(x, y, color=BASE_C, lw=0.6, ls=":", zorder=2.5, marker=mk, ms=4.4, mfc=BASE_C, mec=BASE_C, mew=0)


def budget_marks(ax, budget_nfe, label=True, y=0.985):
    """Light vertical band at SeaCache's two main budgets (delta = 0.3 and 0.6), label inside the top of the axes."""
    for d, txt in MAIN_BUDGETS.items():
        x = budget_nfe[d]
        ax.axvspan(x - 0.45, x + 0.45, color=S.BAND, zorder=0, lw=0)
        if label:
            ax.text(x, y, txt, transform=ax.get_xaxis_transform(), ha="center", va="top",
                    fontsize=6.5, color=S.INK2, zorder=1)


def metric_panel(ax, series, budget_nfe, key, ylabel, direct_labels=False, label_budgets=True):
    for m in METHODS:
        rows = series[m]
        x = [r[1] for r in rows]
        y = [r[2 if key == "psnr" else 3]["mean"] for r in rows]
        lo = [r[2 if key == "psnr" else 3]["ci95"][0] for r in rows]
        hi = [r[2 if key == "psnr" else 3]["ci95"][1] for r in rows]
        ax.fill_between(x, lo, hi, color=S.C[m], alpha=0.12, lw=0, zorder=S.ZORDER[m] - 2)
        ax.plot(x, y, color=S.C[m], lw=1.6 if m == "ours" else 1.2, zorder=S.ZORDER[m],
                marker=S.MARKER[m], ms=S.MSIZE[m], mfc=S.C[m], mec="white", mew=0.6)
        if direct_labels:
            ax.annotate(LABEL[m], (x[-1], y[-1]), xytext=(4, 0), textcoords="offset points",
                        ha="left", va="center", fontsize=7, color=S.INK)
    baseline_points(ax, key)
    budget_marks(ax, budget_nfe, label=label_budgets)
    ax.set_ylabel(ylabel, labelpad=2)
    nfe_ticks(ax, budget_nfe)


def zoom_inset(ax, series, budget_nfe):
    """Enlarged view of the 18-NFE budget in the PSNR panel, where SeaCache and Spectrum lie 0.15 dB apart."""
    x0 = budget_nfe["0.37"]
    ins = ax.inset_axes([0.035, 0.55, 0.36, 0.33])
    for m in METHODS:
        rows = series[m]
        x = [r[1] for r in rows]
        y = [r[2]["mean"] for r in rows]
        ins.fill_between(x, [r[2]["ci95"][0] for r in rows], [r[2]["ci95"][1] for r in rows], color=S.C[m], alpha=0.12,
                         lw=0, zorder=S.ZORDER[m] - 2)
        ins.plot(x, y, color=S.C[m], lw=1.6 if m == "ours" else 1.2, zorder=S.ZORDER[m], marker=S.MARKER[m],
                 ms=S.MSIZE[m] + 0.6, mfc=S.C[m], mec="white", mew=0.6)
    baseline_points(ins, "psnr")
    ins.set_xlim(x0 - 0.45, x0 + 0.35)
    ins.set_ylim(24.6, 28.5)
    ins.set_xticks([])
    ins.set_yticks([25, 27])
    ins.yaxis.tick_right()
    ins.tick_params(labelsize=5.5, length=1.5, pad=1)
    ins.text(0.04, 0.95, f"{x0:.0f} NFE", transform=ins.transAxes, ha="left", va="top", fontsize=5.5, color=S.INK2)
    ins.grid(axis="x", visible=False)
    ins.set_facecolor("white")
    for sp in ins.spines.values():
        sp.set_visible(True)
        sp.set_color(S.AXIS)
        sp.set_linewidth(0.5)
    ax.indicate_inset_zoom(ins, edgecolor=S.AXIS, lw=0.5, alpha=1.0)


def nfe_ticks(ax, budget_nfe):
    xs = sorted(budget_nfe.values())
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{x:.0f}" if abs(x - round(x)) < 0.05 else f"{x:.1f}" for x in xs])
    ax.set_xlim(8.2, 28.0)
    ax.grid(axis="x", visible=False)


def gain_panel(ax, gains, budget_nfe, label_budgets=True, annotate=True):
    ax.axhline(0, color=S.AXIS, lw=0.6, zorder=1)
    off = {"seacache": 0.0}
    for base in ("seacache",):
        rows = gains[base]
        x = [r[1] + off[base] for r in rows]
        y = [r[2] for r in rows]
        yerr = [[r[2] - r[3][0] for r in rows], [r[3][1] - r[2] for r in rows]]
        ax.plot(x, y, color=S.C[base], lw=1.2, zorder=S.ZORDER[base], marker=S.MARKER[base], ms=S.MSIZE[base],
                mfc=S.C[base], mec="white", mew=0.6)
        ax.errorbar(x, y, yerr=yerr, fmt="none", ecolor=S.C[base], elinewidth=0.8, capsize=1.6, capthick=0.8,
                    zorder=S.ZORDER[base] - 1)
        if annotate and base == "seacache":
            for r, xx in zip(rows, x):
                if r[0] in MAIN_BUDGETS:
                    ax.annotate(f"{r[2]:+.2f}", (xx, r[3][1]), xytext=(0, 2.5), textcoords="offset points",
                                ha="center", va="bottom", fontsize=6.5, color=S.INK)
    budget_marks(ax, budget_nfe, label=label_budgets)
    ax.set_ylabel(r"$\Delta$PSNR of KalSea (dB)", labelpad=2)
    nfe_ticks(ax, budget_nfe)
    # same color + marker as the baseline the gain is measured against
    handles = [Line2D([], [], color=S.C[b], lw=1.2, marker=S.MARKER[b], ms=S.MSIZE[b], mfc=S.C[b], mec="white", mew=0.6,
                      label=f"vs. {LABEL[b]}") for b in ("seacache",)]
    ax.legend(handles=handles, loc="upper left", borderaxespad=0.3, handlelength=1.8, labelspacing=0.35)


def method_legend(fig, y, x=0.5, ncol=3):
    handles = [Line2D([], [], color=S.C[m], lw=1.6 if m == "ours" else 1.2, marker=S.MARKER[m], ms=S.MSIZE[m] + 0.4,
                      mfc=S.C[m], mec="white", mew=0.6, label=LABEL[m]) for m in METHODS]
    handles += [Line2D([], [], color=BASE_C, lw=0.6, ls=":", marker=mk, ms=4.4, mfc=BASE_C, mec=BASE_C, mew=0,
                       label=lab) for _, lab, mk in BASELINES]  # noqa: E501
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(x, y), ncol=ncol, columnspacing=1.6,
               handlelength=2.0, borderaxespad=0.0)


def full_width():
    series, gains, budget_nfe = load()
    fig, axes = plt.subplots(1, 3, figsize=(S.TEXT_W, 2.30), gridspec_kw=dict(wspace=0.30))
    fig.subplots_adjust(left=0.055, right=0.99, bottom=0.15, top=0.84)
    metric_panel(axes[0], series, budget_nfe, "psnr", r"PSNR (dB) $\uparrow$", direct_labels=False)
    zoom_inset(axes[0], series, budget_nfe)
    metric_panel(axes[1], series, budget_nfe, "lpips", r"LPIPS $\downarrow$", label_budgets=False)
    gain_panel(axes[2], gains, budget_nfe, label_budgets=False)
    axes[0].set_ylim(14.5, 38.5)
    axes[1].set_ylim(0, 0.44)
    axes[2].set_ylim(-0.3, 4.6)
    titles = ["(a) PSNR w.r.t. the 50-step reference", "(b) LPIPS w.r.t. the 50-step reference",
              r"(c) Paired PSNR gain of KalSea (95\% CI)"]
    for ax, t in zip(axes, titles):
        ax.set_title(t, loc="left", fontsize=7.5, pad=4, color=S.INK)
        ax.set_xlabel("NFE (of 50)", labelpad=1.5)
    axes[2].set_ylabel(r"$\Delta$PSNR (dB)", labelpad=2)
    method_legend(fig, y=1.0, x=0.5, ncol=len(METHODS) + len(BASELINES))
    S.save(fig, os.path.join(FIG_DIR, "fig_tradeoff"))
    plt.close(fig)


def one_col():
    series, gains, budget_nfe = load()
    fig = plt.figure(figsize=(S.COL_W, 3.30))
    gs = fig.add_gridspec(2, 2, hspace=0.55, wspace=0.40, height_ratios=[1, 1])
    ax_p = fig.add_subplot(gs[0, 0])
    ax_l = fig.add_subplot(gs[0, 1])
    ax_g = fig.add_subplot(gs[1, :])
    fig.subplots_adjust(left=0.115, right=0.985, bottom=0.095, top=0.895)
    metric_panel(ax_p, series, budget_nfe, "psnr", r"PSNR (dB) $\uparrow$")
    metric_panel(ax_l, series, budget_nfe, "lpips", r"LPIPS $\downarrow$", label_budgets=False)
    gain_panel(ax_g, gains, budget_nfe, label_budgets=False)
    for ax in (ax_p, ax_l):   # narrow panels: label the extremes and the two main budgets only
        major = [budget_nfe[d] for d in ("1.0", "0.6", "0.3", "0.2")]
        ax.set_xticks(major)
        ax.set_xticklabels([f"{x:.0f}" if abs(x - round(x)) < 0.05 else f"{x:.1f}" for x in major])
        ax.set_xticks([budget_nfe[d] for d in ("0.8", "0.5", "0.37")], minor=True)
        ax.tick_params(axis="x", which="minor", length=1.8, width=0.5, color=S.INK2)
    ax_p.set_ylim(14.5, 36.5)
    ax_l.set_ylim(0, 0.44)
    ax_g.set_ylim(-0.3, 4.6)
    ax_g.set_ylabel(r"$\Delta$PSNR (dB)", labelpad=2)
    for ax, t in zip((ax_p, ax_l, ax_g), ("(a) PSNR w.r.t. reference", "(b) LPIPS w.r.t. reference",
                                          r"(c) Paired PSNR gain of KalSea (95\% CI)")):
        ax.set_title(t, loc="left", fontsize=7.5, pad=4, color=S.INK)
        ax.set_xlabel("NFE (of 50)", labelpad=1.5)
    method_legend(fig, y=1.0, ncol=4)
    S.save(fig, os.path.join(FIG_DIR, "fig_tradeoff_1col"))
    plt.close(fig)


BL = load_baselines()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--onecol", action="store_true")
    a = ap.parse_args()
    S.apply()
    one_col() if a.onecol else full_width()
