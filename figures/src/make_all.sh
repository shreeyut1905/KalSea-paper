#!/usr/bin/env bash
# Rebuild every data figure, table and caption from the evaluation outputs (see data_sources.py).
#   PY      python with numpy, matplotlib>=3.8 and Pillow                (default: ~/spectrum_env/rv/bin/python)
#   PYPDF   python with PyMuPDF or pypdfium2, for the PNG previews       (default: ~/.local/share/paper-tools/venv/bin/python)
#   LATEX_ENGINE  pdflatex used for the qualitative figures             (default: ~/texlive/2026/bin/x86_64-linux/pdflatex)
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "${BASH_SOURCE[0]}")"
PY="${PY:-$HOME/spectrum_env/rv/bin/python}"
PYPDF="${PYPDF:-$HOME/.local/share/paper-tools/venv/bin/python}"

"$PY" flux_stats.py                                   # data/flux_drawbench_stats.json
"$PY" fig_tradeoff.py                                 # ../fig_tradeoff.{pdf,png}
"$PY" fig_tradeoff.py --onecol                        # ../fig_tradeoff_1col.{pdf,png}
"$PY" qual_select.py --delta 0.6 --quantiles 50 75 --k 2 --tag nfe13
"$PY" qual_select.py --delta 0.6 --quantiles 50 75 --k 1 --tag nfe13_teaser
"$PY" qual_select.py --delta 0.6 --quantiles 25 50 75 --k 2 --tag nfe13_supp
"$PY" qual_select.py --delta 0.3 --quantiles 25 50 75 --k 2 --tag nfe21_supp
"$PY" fig_qualitative.py --tag nfe13 --name fig_qualitative
"$PY" fig_qualitative.py --tag nfe13_teaser --name fig_qualitative_teaser
"$PY" fig_qualitative.py --tag nfe13_supp --name fig_qualitative_supp_nfe13
"$PY" fig_qualitative.py --tag nfe21_supp --name fig_qualitative_supp_nfe21
"$PYPDF" render_previews.py ../fig_qualitative.pdf ../fig_qualitative_teaser.pdf ../fig_qualitative_supp_nfe13.pdf \
    ../fig_qualitative_supp_nfe21.pdf
"$PY" make_tables.py                                  # ../../tables/tab_*.tex
"$PY" make_captions.py                                # ../fig_*_caption.tex
"$PY" make_supp_tables.py                             # ../../tables/supp_*.tex (supplementary material; needs torch)
