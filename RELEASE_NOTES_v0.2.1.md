# MathDraw Studio 0.2.1

MathDraw Studio converts images into finite mathematical drawing representations and exports both the reconstructed image and the complete associated equations.

## Principal capabilities

- Hybrid vector extraction using line, circle, ellipse, and piecewise cubic Bézier equations.
- Fourier contour representation for smooth closed silhouettes.
- Two-dimensional orthonormal DCT representation for photographs and dense textures.
- Exact full-coefficient DCT reconstruction at a user-selected equation resolution.
- Desktop GUI and command-line interface.
- Export to plain text, JSON, SVG, PNG, Markdown, LaTeX, editable DOCX, and typeset PDF.
- Reconstruction-quality measurements including MSE, RMSE, MAE, and PSNR.

## Corrections in 0.2.1

- Corrected Hybrid Vector processing for OpenCV builds that return `HoughLinesP` arrays with shape `(N, 4)` rather than `(N, 1, 4)`.
- Added defensive normalization for standard, flat, and single-line Hough output.
- Added equivalent shape normalization for `HoughCircles` output.
- Added regression coverage for `TypeError: 'numpy.int32' object is not iterable`.

## Installation

```bash
python -m pip install mathdraw_studio-0.2.1-py3-none-any.whl
mathdraw-gui
```

For editable DOCX output, install Pandoc or the `documents` optional dependency. PDF output additionally requires Tectonic, XeLaTeX, or pdfLaTeX on `PATH`.

## Validation

The release package is intended to pass the complete included test suite on Python 3.10 through 3.13. Release artifacts include SHA-256 checksums.
