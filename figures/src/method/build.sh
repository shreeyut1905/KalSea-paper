#!/usr/bin/env bash
# Build the method figure: (1) panels (b),(c) from the processed trace in data/ (make_panels.py, matplotlib PGF backend;
#     the trace itself is produced by research_v2/ablations/method_figure_trace/{collect_trace,process_trace}.py),
# (2) method.tex -> ../../method.pdf (pdfLaTeX, TeX Live 2026), (3) 300-dpi PNG preview ../../method.png.
#   ./build.sh            full build
#   ./build.sh --tex-only skip the matplotlib step
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FIG="$(cd "$HERE/../.." && pwd)"
export PATH=/home/ubuntu/texlive/2026/bin/x86_64-linux:$PATH
PY=${PY:-/home/ubuntu/spectrum_env/rv/bin/python}
RENDER_PY=${RENDER_PY:-$HOME/.local/share/paper-tools/venv/bin/python}   # any python with PyMuPDF (same venv as the paper build), only for the PNG preview
cd "$HERE"
if [[ "${1:-}" != "--tex-only" && -f make_panels.py ]]; then
  "$PY" make_panels.py
fi
mkdir -p build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory build method.tex > build/method.stdout 2>&1 || {
  grep -n -A3 '^!' build/method.log | head -40; exit 1; }
cp build/method.pdf "$FIG/method.pdf"
if [[ -x "$RENDER_PY" ]]; then
  "$RENDER_PY" - "$FIG/method.pdf" "$FIG/method.png" <<'EOF'
import sys, pymupdf
doc = pymupdf.open(sys.argv[1]); page = doc[0]
page.get_pixmap(dpi=300, alpha=False).save(sys.argv[2])
fonts = page.get_fonts()
bad = [f for f in fonts if f[2] not in ("Type1", "Type1C", "TrueType", "CIDFontType0", "CIDFontType2")]
print("page %.3f x %.3f in; fonts: %s%s" % (page.rect.width / 72, page.rect.height / 72,
      ", ".join(sorted({f[3].split('+')[-1] + "/" + f[2] for f in fonts})), ("  NON-EMBEDDABLE: %s" % bad) if bad else ""))
EOF
fi
grep -E "Overfull|Underfull|Warning" build/method.log | grep -v "Font shape" | head -5 || true
