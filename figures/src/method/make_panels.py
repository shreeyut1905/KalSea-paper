#!/usr/bin/env python3
"""Panels (b) and (c) of the method figure from the processed real trace in data/.

Provenance: research_v2/ablations/method_figure_trace/collect_trace.py (one instrumented FLUX.1-dev generation per
method, GPU) -> p154/ raw trace -> process_trace.py -> data/method_trace_steps.csv + data/method_trace_summary.json.

Output: panel_b.pgf, panel_c.pgf (matplotlib PGF backend; text is typeset by LaTeX when method.tex is compiled,
so fonts are exactly the paper's: Times text, Computer Modern math).  Colors / markers: figures/src/figstyle.py.

Data (all real, FLUX.1-dev, one DrawBench prompt, delta = 0.6, see data/method_trace_summary.json):
  (b) residual projected on a fixed random unit direction in the lowest DCT band of the Kalman filter (the band that
      carries most of the residual energy):  observations at computed steps, the Kalman extrapolation (prior mean
      m_i^-) with its +-1 sd band sqrt(P_00^- p), the RTS-smoothed values m_i^s, and, for reference only, the residual
      that full computation from x_{a+1} would have produced (shadow evaluation, not available to the sampler).
      Below: the smoother gains g_i of that band.
  (c) relative deviation of the latent from full computation started at the same x_{a+1}: path integrated with the
      extrapolated residuals (what the sampler did before the correction) vs. the path re-integrated with the
      smoothed residuals and the output layers only (PCGS); the sampler continues from x_b'.
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np
import matplotlib

matplotlib.use("pgf")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import figstyle  # noqa: E402  (shared palette)

os.environ["PATH"] = "/home/ubuntu/texlive/2026/bin/x86_64-linux:" + os.environ.get("PATH", "")
CM = 1 / 2.54
C = figstyle.C
INK, INK2, MUTED, GRID = figstyle.INK, figstyle.INK2, figstyle.MUTED, figstyle.GRID
GAPFILL = "#f3f2ef"          # very light neutral wash marking skipped steps
TRUE_C = "#7a7974"           # shadow full-computation residual (context, not a method)

matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    "pgf.rcfonts": False,
    "pgf.preamble": "\n".join([r"\usepackage{times}", r"\usepackage{amsmath,amssymb,bm}",
                               r"\input{%s}" % os.path.join(HERE, "method_macros.tex").replace("\\", "/")]),
    "text.usetex": False,
    "font.family": "serif",
    "font.size": 7,
    "axes.labelsize": 7,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.5,
    "axes.edgecolor": figstyle.AXIS,
    "axes.labelcolor": INK,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelcolor": INK, "ytick.labelcolor": INK,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2.0, "ytick.major.size": 2.0,
    "xtick.major.pad": 1.5, "ytick.major.pad": 1.5,
    "axes.labelpad": 2.0,
    "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round",
    "lines.dash_capstyle": "butt",
    "legend.frameon": False,
})

LW = 1.0          # data lines (pt)
LW_THIN = 0.6


def load():
    rows = list(csv.DictReader(open(os.path.join(HERE, "data", "method_trace_steps.csv"))))

    def col(k):
        return np.array([float(r[k]) if r[k] not in ("", None) else np.nan for r in rows])

    D = {k: col(k) for k in rows[0].keys()}
    S = json.load(open(os.path.join(HERE, "data", "method_trace_summary.json")))
    return D, S


def gap_spans(S, lo, hi):
    return [(g["i_a"], g["i_b"]) for g in S["gaps"] if g["i_a"] >= lo and g["i_b"] <= hi]


def shade_gaps(ax, spans):
    for a, b in spans:
        ax.axvspan(a + 0.5, b - 0.5, color=GAPFILL, lw=0, zorder=0)


def style_steps(ax, lo, hi, label=True):
    ax.set_xlim(lo - 0.55, hi + 0.55)
    ax.set_xticks(np.arange(lo, hi + 1, 4))
    ax.set_xticks(np.arange(lo, hi + 1, 1), minor=True)
    ax.tick_params(axis="x", which="minor", length=1.2, width=0.4, color=figstyle.AXIS)
    if label:
        ax.set_xlabel(r"sampler step $i$", labelpad=1.5)


def panel_b(D, S, lo, hi, path, W, H):
    i = D["i"]
    sel = (i >= lo) & (i <= hi)
    spans = gap_spans(S, lo, hi)
    fig = plt.figure(figsize=(W, H))
    l, r = 0.072, 0.992
    axr = fig.add_axes([l, 0.425, r - l, 0.565])
    axg = fig.add_axes([l, 0.178, r - l, 0.180], sharex=axr)
    # ---------------------------------------------------------------- residual
    obs_m = sel & (D["computed"] == 1)
    for a, b in spans:
        g = (i > a) & (i < b)
        ia, ib = int(a) - 1, int(b) - 1
        xs = np.r_[a, i[g], b]
        fc = np.r_[D["post"][ia], D["prior"][g], D["prior"][ib]]
        sd = np.r_[D["post_sd"][ia], D["prior_sd"][g], D["prior_sd"][ib]]
        axr.fill_between(xs, fc - sd, fc + sd, color=C["kalsea"], alpha=0.10, lw=0, zorder=1)
        axr.plot(xs, fc, color=C["kalsea"], lw=LW, dashes=(3.2, 1.6), zorder=3)
        tr = np.r_[D["obs"][ia], D["oracle"][g], D["obs"][ib]]
        axr.plot(xs, tr, color=TRUE_C, lw=LW_THIN, zorder=2)
        axr.plot(i[g], D["oracle"][g], ls="none", marker="o", ms=2.6, mfc="white", mec=TRUE_C, mew=0.6, zorder=2)
        sm = np.r_[D["obs"][ia], D["smoothed"][g], D["obs"][ib]]
        axr.plot(xs, sm, color=C["ours"], lw=LW, zorder=4)
        axr.plot(i[g], D["smoothed"][g], ls="none", marker="o", ms=2.6, mfc=C["ours"], mec="white", mew=0.4, zorder=4)
        # innovation at b: from the extrapolated value to the observation
        y0, y1 = D["prior"][ib], D["obs"][ib]
        xa = b - 0.22
        axr.add_patch(FancyArrowPatch((xa, y0), (xa, y1), arrowstyle="-|>,head_length=2.2,head_width=1.1",
                                      lw=0.5, color=INK, shrinkA=0, shrinkB=2.0, zorder=6))
        axr.plot([xa - 0.12, xa + 0.12], [y0, y0], color=INK, lw=0.5, zorder=6)
        axr.text(xa - 0.12, 0.5 * (y0 + y1), r"$e_b$", ha="right", va="center", fontsize=7, color=INK, zorder=6)
    axr.plot(i[obs_m], D["obs"][obs_m], ls="none", marker="o", ms=3.8, mfc=INK, mec="white", mew=0.5, zorder=7)
    # z_a, z_b of the first gap
    a0, b0 = spans[0]
    axr.annotate(r"$z_a$", (a0, D["obs"][int(a0) - 1]), xytext=(-1.5, 5.5), textcoords="offset points", ha="left",
                 va="bottom", fontsize=7, color=INK)
    axr.annotate(r"$z_b$", (b0, D["obs"][int(b0) - 1]), xytext=(-2.0, 5.0), textcoords="offset points", ha="center",
                 va="bottom", fontsize=7, color=INK)
    # curve labels tying (b) to the PCGS formula in (a)
    g0 = (i > a0) & (i < b0)
    xm = a0 + 0.55 * (b0 - a0)
    ym = np.interp(xm, np.r_[a0, i[g0], b0], np.r_[D["post"][int(a0) - 1], D["prior"][g0], D["prior"][int(b0) - 1]])
    axr.annotate(r"$\prior{m}_i$", (xm, ym), xytext=(0, -4.5), textcoords="offset points", ha="center", va="top",
                 fontsize=7, color=INK)
    a1, b1 = spans[1]
    g1 = (i > a1) & (i < b1)
    xm = a1 + 0.45 * (b1 - a1)
    ym = np.interp(xm, np.r_[a1, i[g1], b1], np.r_[D["obs"][int(a1) - 1], D["smoothed"][g1], D["obs"][int(b1) - 1]])
    axr.annotate(r"$\smooth{m}_i$", (xm, ym), xytext=(1.0, -5.0), textcoords="offset points", ha="center", va="top",
                 fontsize=7, color=INK)
    axr.set_ylabel(r"residual $\langle\res_i,\mathbf{u}\rangle$", labelpad=2)
    axr.set_yticks([])
    plt.setp(axr.get_xticklabels(), visible=False)
    axr.tick_params(axis="x", which="both", length=0)
    vals = np.concatenate([D["obs"][obs_m], D["oracle"][sel & (D["computed"] == 0)],
                           D["smoothed"][sel & (D["computed"] == 0)], D["prior"][sel & (D["computed"] == 0)]])
    vmin, vmax = np.nanmin(vals), np.nanmax(vals)
    pad = 0.22 * (vmax - vmin)
    axr.set_ylim(vmin - pad, vmax + pad)
    # ---------------------------------------------------------------- gains
    gm = sel & np.isfinite(D["gain"])
    axg.vlines(i[gm], 0, D["gain"][gm], color=C["ours"], lw=LW)
    axg.plot(i[gm], D["gain"][gm], ls="none", marker="o", ms=2.6, mfc=C["ours"], mec="white", mew=0.4)
    axg.set_ylim(0, 1.08)
    axg.set_yticks([0, 1])
    axg.set_ylabel(r"$g_i$", rotation=0, ha="right", va="center", labelpad=2)
    style_steps(axr, lo, hi, label=False)
    style_steps(axg, lo, hi)
    fig.savefig(path)
    plt.close(fig)
    return fig


def panel_c(D, S, lo, hi, path, W, H):
    i = D["i"]
    spans = gap_spans(S, lo, hi)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.125, 0.178, 0.865, 0.812])
    ax.axhline(0, color=TRUE_C, lw=LW_THIN, zorder=2)
    for a, b in spans:
        g = (i > a) & (i <= b)
        xs = i[g]
        dr = 100 * D["dev_drift_o"][g]
        co = 100 * D["dev_corr_o"][g]
        ax.plot(xs, dr, color=C["kalsea"], lw=LW, dashes=(3.2, 1.6), zorder=3)
        ax.plot(xs, dr, ls="none", marker=figstyle.MARKER["kalsea"], ms=2.5, mfc=C["kalsea"], mec="white", mew=0.4,
                zorder=3)
        ax.plot(xs, co, color=C["ours"], lw=LW, zorder=4)
        ax.plot(xs, co, ls="none", marker="o", ms=2.6, mfc=C["ours"], mec="white", mew=0.4, zorder=4)
        ax.add_patch(FancyArrowPatch((b + 0.25, dr[-1]), (b + 0.25, co[-1]),
                                     arrowstyle="-|>,head_length=2.4,head_width=1.2", lw=0.6, color=INK,
                                     shrinkA=0.5, shrinkB=0.5, zorder=6))
        if (a, b) == spans[0]:
            ax.text(b + 0.38, 0.5 * (dr[-1] + co[-1]), r"$\lat_b\!\to\!\lat_b'$", ha="left", va="center",
                    fontsize=7, color=INK)
    ax.set_ylabel(r"$\|\lat_i-\lat_i^{\mathrm{full}}\|\,/\,\|\lat_i^{\mathrm{full}}\|$ (\%)", labelpad=2)
    style_steps(ax, lo, hi)
    ax.set_xlim(lo - 0.55, hi + 0.75)
    ax.text(lo - 0.2, 0.97 * ax.get_ylim()[1], "gap re-integrated with $\\Emb,\\Out$ only:\n0 extra transformer evaluations",
            ha="left", va="top", fontsize=7, color=INK, linespacing=1.25)
    ax.text(lo + 0.75, -0.42, "full computation from $\\lat_{a+1}$", ha="left", va="top", fontsize=7, color=INK2)
    ax.set_ylim(-1.35, None)
    ax.set_yticks([0, 2, 4, 6, 8])
    fig.savefig(path)
    plt.close(fig)


def main():
    D, S = load()
    lo, hi = 26, 42
    panel_b(D, S, lo, hi, os.path.join(HERE, "panel_b.pgf"), 10.0 * CM, 3.75 * CM)
    panel_c(D, S, lo, hi, os.path.join(HERE, "panel_c.pgf"), 7.2 * CM, 3.75 * CM)
    print("panels written; window", lo, hi, "band", S["band"])


if __name__ == "__main__":
    main()
