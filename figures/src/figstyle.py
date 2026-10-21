"""Shared figure style for the paper (palette, typography, sizes, export).

One fixed color per method, used in every figure (data plots and diagrams):
    Ours      #256abf  (blue step 500)
    KalSea    #199e70  (aqua, dark-surface step)  -- Kalman forecasting, no gap smoothing
    SeaCache  #d95926  (orange, dark-surface step)
    Reference #0b0b0b  (primary ink; 50-step sampler)
All hexes come from the documented dataviz reference palette. The three method colors pass the
dataviz validator on a white surface (validate_palette.js --mode light --pairs all --surface #ffffff):
lightness band, chroma floor, CVD all-pairs dE >= 9.4 (protan/deutan) and 9.6 (tritan),
normal-vision all-pairs dE >= 21.6, contrast >= 3.4:1 on white.  Secondary encoding is
always present (marker shape per method + legend/direct labels), so identity never relies on hue.

Typography matches the CVPR template (Times): STIX (Times-compatible) text and math, 7-8 pt at final size.
CVPR widths: \\columnwidth = 3.28125 in, \\textwidth = 6.875 in.
"""
import matplotlib as mpl

COL_W = 3.28125   # in, CVPR \columnwidth  ((6.875 - 0.3125) / 2)
TEXT_W = 6.875    # in, CVPR \textwidth

C = {
    "ours": "#256abf",
    "kalsea": "#199e70",
    "seacache": "#d95926",
    "reference": "#0b0b0b",
}
LABEL = {"ours": "Ours", "kalsea": "KalSea", "seacache": "SeaCache", "reference": "Reference"}
MARKER = {"ours": "o", "kalsea": "D", "seacache": "s"}
MSIZE = {"ours": 3.6, "kalsea": 3.0, "seacache": 3.2}
ZORDER = {"ours": 5, "kalsea": 4, "seacache": 3}

INK = "#0b0b0b"        # primary ink
INK2 = "#52514e"       # secondary ink (axis labels, annotations)
MUTED = "#898781"      # muted ink
GRID = "#e1e0d9"       # hairline grid
AXIS = "#9a998f"       # axis spines (one step darker than the template's baseline gray, for print)
BAND = "#f0efec"       # neutral highlight band


def apply():
    mpl.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 7.5,
        "axes.titlesize": 7.5,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.labelcolor": INK,
        "ytick.labelcolor": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "xtick.major.pad": 2,
        "ytick.major.pad": 2,
        "lines.linewidth": 1.25,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "pdf.fonttype": 42,   # embed TrueType (Type 42), no Type 3
        "ps.fonttype": 42,
        "savefig.dpi": 300,
        "figure.dpi": 150,
        "text.color": INK,
    })


def save(fig, path_noext, png_dpi=300):
    """Vector PDF (fonts embedded as Type 42) + 300-dpi PNG preview."""
    fig.savefig(path_noext + ".pdf", metadata={"Creator": None, "Producer": None, "CreationDate": None})
    fig.savefig(path_noext + ".png", dpi=png_dpi)
