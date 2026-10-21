# latexmk configuration (read when latexmk runs in this directory).  Prefer ./build.sh, which also renders
# PNG pages and runs the checks.  Engine: pdfLaTeX from TeX Live 2026 (~/texlive/2026).
$pdf_mode = 1;
$out_dir = 'build';
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error -file-line-error %O %S';
@default_files = ('main.tex');
