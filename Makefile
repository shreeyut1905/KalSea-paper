# Paper build (thin wrapper around build.sh) + figure helpers.
#   make                 build main.pdf and supp.pdf, render pages to render/page-XX.png and render/supp-page-XX.png,
#                        run checks on both
#   make main            main paper only (no supplement)
#   make supp            same as make (the supplement needs the main paper's build/main.aux)
#   make nopng           build + checks, no PNGs
#   make render          re-render main.pdf and supp.pdf (DPI=150 by default; e.g. make render DPI=220)
#   make strict          build and fail on submission blockers of either PDF (see build.sh --help)
#   make check           checks only, on the existing main.pdf and supp.pdf
#   make kit-test        compile the pristine official kit example (review mode) -> render/kit-test-01.png
#   make fig F=figures/src/foo.tex   compile a standalone LaTeX/TikZ figure -> figures/foo.pdf, 300-dpi PNG in
#                                    render/fig-foo-01.png, size + font check
#   make figcheck P=figures/foo.pdf  300-dpi PNG + size/font check of an existing figure PDF (e.g. matplotlib)
#   make clean           remove build/ and render/
SHELL  := /bin/bash
TL_BIN ?= $(HOME)/texlive/2026/bin/x86_64-linux
PY     ?= $(HOME)/.local/share/paper-tools/venv/bin/python
DPI    ?= 150
export PATH := $(TL_BIN):$(PATH)

.PHONY: all pdf main supp nopng render strict check kit-test fig figcheck clean

all pdf supp:
	DPI=$(DPI) ./build.sh

main:
	DPI=$(DPI) ./build.sh --no-supp

nopng:
	./build.sh --no-render

render:
	DPI=$(DPI) ./build.sh --render-only

strict:
	DPI=$(DPI) ./build.sh --strict

check:
	$(PY) -I tools/pdfcheck.py main.pdf --aux build/main.aux --log build/main.log
	$(PY) -I tools/pdfcheck.py supp.pdf --supp --aux build/supp_main.aux --log build/supp_main.log

kit-test:
	rm -rf build/kit-test && mkdir -p build render && cp -a kit/CVPR2026-v1-latex build/kit-test
	cd build/kit-test && latexmk -norc -pdf -interaction=nonstopmode -halt-on-error main.tex > latexmk.out 2>&1 \
	  || { tail -n 20 latexmk.out; exit 1; }
	$(PY) -I tools/render_pages.py build/kit-test/main.pdf render --pages 1 --dpi $(DPI) --prefix kit-test
	@grep -q 'CONFIDENTIAL REVIEW COPY' <($(PY) -I -c "import pymupdf,sys; print(pymupdf.open(sys.argv[1])[0].get_text())" build/kit-test/main.pdf) \
	  && echo "kit-test OK: official example compiles in review mode (build/kit-test/main.pdf)"

fig:
	@test -n "$(F)" || { echo "usage: make fig F=figures/src/<name>.tex"; exit 2; }
	@mkdir -p build/fig render
	latexmk -norc -pdf -cd -interaction=nonstopmode -halt-on-error -outdir=$(CURDIR)/build/fig $(F) > build/fig/latexmk.out 2>&1 \
	  || { tail -n 20 build/fig/latexmk.out; exit 1; }
	cp build/fig/$(basename $(notdir $(F))).pdf figures/$(basename $(notdir $(F))).pdf
	$(PY) -I tools/render_pages.py figures/$(basename $(notdir $(F))).pdf render --dpi 300 --prefix fig-$(basename $(notdir $(F)))
	$(PY) -I tools/pdfcheck.py figures/$(basename $(notdir $(F))).pdf --figure

figcheck:
	@test -n "$(P)" || { echo "usage: make figcheck P=figures/<name>.pdf"; exit 2; }
	@mkdir -p render
	$(PY) -I tools/render_pages.py $(P) render --dpi 300 --prefix fig-$(basename $(notdir $(P)))
	$(PY) -I tools/pdfcheck.py $(P) --figure

clean:
	rm -rf build render
