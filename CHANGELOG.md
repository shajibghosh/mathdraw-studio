# Changelog

## 0.2.1

- Fixed Hybrid Vector processing with OpenCV builds that return `HoughLinesP` data as `(N, 4)` instead of `(N, 1, 4)`.
- Added robust normalization for single-line, flat-line, and standard Hough line outputs.
- Added the same shape normalization for `HoughCircles` output.
- Added regression tests for the reported `TypeError: 'numpy.int32' object is not iterable` failure.

## 0.2.0

- Added complete Markdown and LaTeX equation reports.
- Added editable DOCX generation through Pandoc.
- Added PDF generation through Tectonic, XeLaTeX, or pdfLaTeX.
- Added exact full-coefficient DCT export at the selected equation resolution.
