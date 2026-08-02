# Editable Word and PDF equation export

MathDraw Studio exports the complete equation model in four human-readable forms:

- `equations.txt` for plain text;
- `equations_full.md` for Markdown plus LaTeX;
- `equations_full.tex` for compilable LaTeX;
- `equations_full.docx` for native, editable Microsoft Word equations;
- `equations_full.pdf` for a typeset report.

## GUI workflow

1. Open and process an image.
2. Choose the coordinate system.
3. Select **Export equations (TXT, DOCX, PDF)**.
4. Choose an output folder.
5. Open `equations_full.docx` in Microsoft Word.

The Word equations are Office Math objects, not pasted screenshots. Select an equation in Word and use **Equation > Professional** or **Linear** to change how it is displayed. You may edit coefficients, symbols, limits, fractions, subscripts, and superscripts directly.

## Exactness

An exported report is always complete for the generated model, but the generated model may approximate the original image.

- Hybrid vector mode includes every detected line, circle, ellipse, and Bezier segment. Image-to-contour extraction is normally approximate.
- Fourier mode includes every retained harmonic coefficient. A finite harmonic series approximates the sampled contour.
- DCT mode becomes exact at the selected equation resolution only when **Retain every DCT coefficient** is enabled.

For an RGB image represented at width `W` and height `H`, exact DCT export contains `3WH` coefficients. For example:

- 32 x 32 RGB: 3,072 coefficients;
- 64 x 64 RGB: 12,288 coefficients;
- 128 x 128 RGB: 49,152 coefficients;
- 2000 x 1100 RGB: 6,600,000 coefficients.

The last case can produce a document containing thousands of pages. Exactness at a smaller equation grid is usually more practical.

## Command line

Compressed photographic approximation:

```bash
mathdraw photo.jpg --mode dct_image --dct-width 128 --dct-height 128 \
  --dct-coefficients 6000 --output output_photo
```

Exact at 64 x 64 equation resolution:

```bash
mathdraw photo.jpg --mode dct_image --dct-width 64 --dct-height 64 \
  --dct-exact --output output_exact
```

## Required converters

The Anaconda environment installs Pandoc and Tectonic. Pandoc generates native Word equations. Tectonic generates the PDF.

Using the supplied environment:

```bat
scripts\setup_windows.bat
scripts\run_windows.bat
```

For a pip installation, install Pandoc support:

```bash
pip install -e ".[documents]"
```

Install Tectonic, MiKTeX, or TeX Live separately for automatic PDF generation. The `.tex` source is still exported when a PDF engine is unavailable.
