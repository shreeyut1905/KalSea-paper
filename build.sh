#!/usr/bin/env bash
# Build the paper and the supplementary material with pdfLaTeX (latexmk, TeX Live 2026), render pages, run the checks.
#   ./build.sh                build -> main.pdf and supp.pdf; pages -> render/page-XX.png, render/supp-page-XX.png
#   ./build.sh --no-render    build + checks, no PNGs
#   ./build.sh --render-only  re-render the existing main.pdf / supp.pdf + checks
#   ./build.sh --strict       exit non-zero on submission blockers (page limit, fonts, undefined refs,
#                             TODO/TBD markers, missing files, anonymity leaks, modified kit files), main or supplement
#   ./build.sh --no-supp      main paper only (supp_main.tex -> supp.pdf is skipped)
#   ./build.sh --clean        delete build/ and render/*page-*.png first
#   DPI=200 ./build.sh        page render resolution (default 150)
# The supplement imports the labels of build/main.aux (references into the main paper), so main.tex is built first.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

TL_BIN="${TL_BIN:-$HOME/texlive/2026/bin/x86_64-linux}"
PY="${PY:-$HOME/.local/share/paper-tools/venv/bin/python}"   # venv with PyMuPDF (render + checks)
export PATH="$TL_BIN:$PATH"
DPI="${DPI:-150}"
BUILD=1; RENDER=1; STRICT=""; CLEAN=0; SUPP=1
for arg in "$@"; do
  case "$arg" in
    --no-render)   RENDER=0 ;;
    --render-only) BUILD=0 ;;
    --strict)      STRICT="--strict" ;;
    --clean)       CLEAN=1 ;;
    --no-supp)     SUPP=0 ;;
    -h|--help)     sed -n '2,11p' "$0"; exit 0 ;;
    *)             echo "unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

command -v latexmk >/dev/null || { echo "latexmk not found; expected TeX Live in $TL_BIN" >&2; exit 1; }
[ -x "$PY" ] || { echo "Python with PyMuPDF not found at $PY" >&2; exit 1; }

if [ "$CLEAN" = 1 ]; then rm -rf build; rm -f render/page-*.png render/supp-page-*.png; fi
mkdir -p build render
echo "[kit]    CVPR2026-v1(latex) -- TODO: switch to the CVPR 2027 kit when released (kit/KIT_SOURCE.txt)"

if [ "$BUILD" = 1 ]; then
  echo "[build]  latexmk -pdf main.tex  ($(pdflatex --version | head -n1))"
  run_latexmk() {   # run_latexmk <jobname> [latexmk options]
    local job="$1"; shift
    if ! latexmk -norc -pdf -outdir=build -interaction=nonstopmode -halt-on-error -file-line-error "$@" "$job.tex" \
         > "build/latexmk_$job.out" 2>&1; then
      echo "[build]  FAILED. First errors (build/$job.log):" >&2
      { grep -nE '^(\./)?[^ :]+\.(tex|sty|cls|bbl):[0-9]+: |^! ' "build/$job.log" 2>/dev/null | head -n 20; } >&2 || true
      echo "[build]  latexmk output tail (build/latexmk_$job.out):" >&2
      tail -n 15 "build/latexmk_$job.out" >&2
      exit 1
    fi
  }
  build_one() {     # build_one <jobname> <output pdf>
    run_latexmk "$1"
    # latexmk can consider a stale state up to date (e.g. after a failed BibTeX run). If the log still asks for a
    # rerun or has undefined citations/references, force one full pass; whatever remains is reported by the check.
    if grep -qE 'Rerun to get|Label\(s\) may have changed|There were undefined (references|citations)' "build/$1.log"; then
      echo "[build]  $1: unresolved references or rerun request -> forcing one full latexmk pass (-g)"
      run_latexmk "$1" -g
    fi
    cp "build/$1.pdf" "$2"
    echo "[build]  $HERE/$2"
  }
  build_one main main.pdf
  if [ "$SUPP" = 1 ]; then
    echo "[build]  latexmk -pdf supp_main.tex  (supplementary material; reads build/main.aux)"
    build_one supp_main supp.pdf
  fi
fi

[ -f main.pdf ] || { echo "main.pdf not found; build first" >&2; exit 1; }
if [ "$SUPP" = 1 ] && [ ! -f supp.pdf ]; then echo "supp.pdf not found; build first (or use --no-supp)" >&2; exit 1; fi
if [ "$RENDER" = 1 ]; then
  n=$("$PY" -I tools/render_pages.py main.pdf render --dpi "$DPI" --clean | wc -l)
  echo "[render] $n pages at $DPI dpi -> $HERE/render/page-01.png ... page-$(printf %02d "$n").png"
  if [ "$SUPP" = 1 ]; then
    n=$("$PY" -I tools/render_pages.py supp.pdf render --dpi "$DPI" --prefix supp-page --clean | wc -l)
    echo "[render] supplement: $n pages -> $HERE/render/supp-page-01.png ... supp-page-$(printf %02d "$n").png"
  fi
fi
echo "[check]  main paper"
status=0
"$PY" -I tools/pdfcheck.py main.pdf --aux build/main.aux --log build/main.log $STRICT || status=1
if [ "$SUPP" = 1 ]; then
  echo "[check]  supplementary material"
  "$PY" -I tools/pdfcheck.py supp.pdf --supp --aux build/supp_main.aux --log build/supp_main.log $STRICT || status=1
fi
exit $status
