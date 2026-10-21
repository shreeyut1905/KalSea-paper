#!/usr/bin/env bash
# Build the paper with pdfLaTeX (latexmk, TeX Live 2026), render pages to PNG, and run the checks.
#   ./build.sh                build -> main.pdf; pages -> render/page-XX.png; print checks
#   ./build.sh --no-render    build + checks, no PNGs
#   ./build.sh --render-only  re-render the existing main.pdf + checks
#   ./build.sh --strict       exit non-zero on submission blockers (page limit, fonts, undefined refs,
#                             TODO/TBD markers, missing files, anonymity leaks, modified kit files)
#   ./build.sh --clean        delete build/ and render/page-*.png first
#   DPI=200 ./build.sh        page render resolution (default 150)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

TL_BIN="${TL_BIN:-$HOME/texlive/2026/bin/x86_64-linux}"
PY="${PY:-$HOME/.local/share/paper-tools/venv/bin/python}"   # venv with PyMuPDF (render + checks)
export PATH="$TL_BIN:$PATH"
DPI="${DPI:-150}"
BUILD=1; RENDER=1; STRICT=""; CLEAN=0
for arg in "$@"; do
  case "$arg" in
    --no-render)   RENDER=0 ;;
    --render-only) BUILD=0 ;;
    --strict)      STRICT="--strict" ;;
    --clean)       CLEAN=1 ;;
    -h|--help)     sed -n '2,9p' "$0"; exit 0 ;;
    *)             echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

command -v latexmk >/dev/null || { echo "latexmk not found; expected TeX Live in $TL_BIN" >&2; exit 1; }
[ -x "$PY" ] || { echo "Python with PyMuPDF not found at $PY" >&2; exit 1; }

if [ "$CLEAN" = 1 ]; then rm -rf build; rm -f render/page-*.png; fi
mkdir -p build render
echo "[kit]    CVPR2026-v1(latex) -- TODO: switch to the CVPR 2027 kit when released (kit/KIT_SOURCE.txt)"

if [ "$BUILD" = 1 ]; then
  echo "[build]  latexmk -pdf main.tex  ($(pdflatex --version | head -n1))"
  run_latexmk() {
    if ! latexmk -norc -pdf -outdir=build -interaction=nonstopmode -halt-on-error -file-line-error "$@" main.tex \
         > build/latexmk.out 2>&1; then
      echo "[build]  FAILED. First errors (build/main.log):" >&2
      { grep -nE '^(\./)?[^ :]+\.(tex|sty|cls|bbl):[0-9]+: |^! ' build/main.log 2>/dev/null | head -n 20; } >&2 || true
      echo "[build]  latexmk output tail (build/latexmk.out):" >&2
      tail -n 15 build/latexmk.out >&2
      exit 1
    fi
  }
  run_latexmk
  # latexmk can consider a stale state up to date (e.g. after a failed BibTeX run). If the log still asks for a
  # rerun or has undefined citations/references, force one full pass; whatever remains is reported by the check.
  if grep -qE 'Rerun to get|Label\(s\) may have changed|There were undefined (references|citations)' build/main.log; then
    echo "[build]  unresolved references or rerun request -> forcing one full latexmk pass (-g)"
    run_latexmk -g
  fi
  cp build/main.pdf main.pdf
  echo "[build]  $HERE/main.pdf"
fi

[ -f main.pdf ] || { echo "main.pdf not found; build first" >&2; exit 1; }
if [ "$RENDER" = 1 ]; then
  n=$("$PY" -I tools/render_pages.py main.pdf render --dpi "$DPI" --clean | wc -l)
  echo "[render] $n pages at $DPI dpi -> $HERE/render/page-01.png ... page-$(printf %02d "$n").png"
fi
echo "[check]"
"$PY" -I tools/pdfcheck.py main.pdf --aux build/main.aux --log build/main.log $STRICT
