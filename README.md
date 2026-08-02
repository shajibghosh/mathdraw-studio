# MathDraw Studio

MathDraw Studio is a Python desktop application and command-line tool that converts an input image into a **finite mathematical representation** and renders that representation back into an image.

It is designed for:

- line drawings and diagrams;
- objects, animals, foods, logos, and silhouettes;
- repeating patterns and decorative art;
- text and disconnected strokes, represented as glyph contours;
- photographs and dense textures, represented by a finite 2D cosine series.

> Important: no small, universal closed-form equation can exactly describe every arbitrary photograph. MathDraw therefore selects an appropriate finite representation. Increasing the number of paths, harmonics, or cosine coefficients increases fidelity and equation size.

## What the program produces

For every processed image, the GUI can export:

- `equations.txt`: complete plain-text equations;
- `equations_full.md`: complete equations in Markdown with LaTeX notation;
- `equations_full.tex`: complete, compilable LaTeX source;
- `equations_full.docx`: editable Microsoft Word equations stored as native Office Math objects;
- `equations_full.pdf`: typeset equation report;
- `drawing_model.json`: machine-readable primitives and coefficients;
- `reconstruction.svg`: scalable vector output for vector modes, or an embedded reconstruction for DCT mode;
- `reconstruction.png`: rendered preview of the equations.

The GUI equation tab may truncate extremely large reports for responsiveness, but the exported files are not truncated.

## Mathematical modes

### 1. Hybrid vector

Best for a drawing like the supplied cat-in-a-box example.

- Straight structures become parametric line equations:

  \[
  x(t)=x_0+(x_1-x_0)t,\qquad
  y(t)=y_0+(y_1-y_0)t,\qquad 0\le t\le1.
  \]

- Circular structures become:

  \[
  x(t)=c_x+r\cos t,\qquad y(t)=c_y+r\sin t.
  \]

- Irregular outlines, text glyphs, animal silhouettes, and curved details become piecewise cubic Bézier equations:

  \[
  B(t)=(1-t)^3P_0+3(1-t)^2tP_1+3(1-t)t^2P_2+t^3P_3.
  \]

### 2. Fourier contours

Each closed contour is resampled and represented as a truncated complex Fourier series:

\[
z(t)=x(t)+iy(t)=\sum_{k=-K}^{K}c_k e^{i2\pi kt},\qquad 0\le t<1.
\]

This is useful for smooth silhouettes and organic contours.

### 3. 2D cosine-series image

Photographs and textured images are resized to a configurable equation grid. Each color channel is represented using an orthonormal 2D DCT basis:

\[
I_c(x,y)=\sum_{u,v}C_{cvu}\alpha_u\alpha_v
\cos\left(\frac{\pi(2x+1)u}{2W}\right)
\cos\left(\frac{\pi(2y+1)v}{2H}\right).
\]

Retaining all coefficients reconstructs the represented sample grid exactly up to floating-point and final pixel rounding. Retaining fewer coefficients produces a compressed approximation. In the GUI, enable **Retain every DCT coefficient (exact at selected resolution)** to request the full coefficient set.

A crucial distinction is that an exact DCT equation is exact for the equation grid. If a 2000 × 1100 image is first resized to 128 × 128, the full DCT is exact for that 128 × 128 representation, not for the original raster. Set the equation width and height to the original dimensions only when you truly need original-resolution exactness; this can produce millions of coefficients and extremely large Word/PDF files.

## Windows installation using Anaconda Prompt

From the extracted project directory:

```bat
scripts\setup_windows.bat
scripts\run_windows.bat
```

Manual equivalent:

```bat
conda env create -f environment.yml
conda activate mathdraw-studio
python -m pip install -e .
python run_app.py
```

## Standard pip installation

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
python run_app.py
```

macOS or Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
python run_app.py
```

Optional support for PDF, SVG, HEIC/HEIF/AVIF, and camera RAW:

```bash
pip install -e ".[formats]"
```

For editable Word equation export when Pandoc is not already installed:

```bash
pip install -e ".[documents]"
```

PDF equation export requires one LaTeX engine on `PATH`: Tectonic, XeLaTeX, or pdfLaTeX. The supplied Anaconda environment installs Pandoc and Tectonic automatically.

## GUI workflow

1. Select **Open image**.
2. Leave **Automatic** selected, or select a representation explicitly.
3. For a line drawing like the cat example, choose **Hybrid vector**.
4. Adjust edge thresholds and contour complexity when needed.
5. Select **Process image**.
6. Compare the input and mathematical reconstruction.
7. Inspect the grouped equations and diagnostics.
8. Select **Export equations (TXT, DOCX, PDF)**.

The DOCX report contains native, editable Word equations rather than screenshots. Click an equation in Microsoft Word and use **Equation > Professional** or **Linear** to switch its display format.

## CLI examples

Hybrid vector:

```bash
mathdraw drawing.png --mode hybrid_vector --output output_vector
```

Fourier contours:

```bash
mathdraw silhouette.png --mode fourier_contour --harmonics 30 --output output_fourier
```

Photograph using a compressed DCT approximation:

```bash
mathdraw photo.jpg --mode dct_image --dct-width 160 --dct-height 120 \
  --dct-coefficients 6000 --output output_photo
```

Exact DCT at a selected resolution:

```bash
mathdraw photo.jpg --mode dct_image --dct-width 64 --dct-height 64 \
  --dct-exact --output output_exact_64
```

For RGB at 64 × 64, this writes 12,288 coefficients. At 2000 × 1100, RGB exactness would require 6,600,000 coefficients, so use original-resolution export only when the very large document size is acceptable.

Automatic selection:

```bash
mathdraw input.webp --mode auto --output output_auto
```

## Recommended settings for the supplied cat example

- Mode: `Hybrid vector`
- Vector max side: `800–1200`
- Canny low/high: `30–50 / 100–150`
- Maximum contours: `150–300`
- Maximum Bézier vertices per region: `60–160`
- Detect straight lines: enabled
- Detect circles: disabled initially; enable only when circular details are important
- Coordinates: centered Cartesian

The text is not semantically retyped. Its visible glyph outlines are mathematically traced, which preserves the original lettering style.

## Input format support

Built in through Pillow:

- PNG, JPEG, BMP, TIFF, WebP, GIF first frame, ICO, PPM, and PGM.

Optional:

- PDF first page through PyMuPDF;
- SVG through CairoSVG;
- HEIC, HEIF, and AVIF through `pillow-heif`;
- common camera RAW formats through `rawpy`.

Animated images are currently processed using the first frame. PDF processing currently uses the selected loader page index, with the GUI defaulting to page 1.

## Accuracy and complexity

The controls trade equation size for reconstruction quality:

- More Bézier samples preserve more local curvature but generate more piecewise equations.
- More Fourier harmonics preserve sharper contour features.
- More DCT coefficients preserve more photographic detail.
- A larger DCT equation grid preserves more spatial resolution but can create a very large coefficient list.

The app displays RMSE, MAE, and PSNR as basic reconstruction diagnostics. Vector previews are compared against the original raster image, so white-space and antialiasing can affect these values.

## Project structure

```text
src/mathdraw/
  contour.py       Bézier contour extraction
  dct_image.py     2D cosine-series model
  document_export.py editable DOCX, LaTeX, Markdown, and PDF reports
  equations.py     readable plain-text equation generation
  exporters.py     TXT, DOCX, PDF, LaTeX, Markdown, JSON, SVG, and PNG export
  fourier.py       Fourier descriptors
  geometry.py      resampling and curve mathematics
  gui/             Tkinter desktop application
  io.py            image loading and optional formats
  pipeline.py      automatic and manual mode orchestration
  preprocess.py    edge maps and image classification heuristic
  primitive.py     line and circle detection
  renderer.py      mathematical reconstruction
```

## Tests

```bash
pip install -e . pytest
pytest -q
```

## Known limitations

- “Any image” means common raster formats plus the documented optional formats, not every proprietary binary image format ever created.
- A photograph may need thousands of coefficients; the representation is mathematically valid but not necessarily human-readable coefficient by coefficient.
- Contour extraction traces visible strokes. It does not infer semantic parts such as “ear,” “tail,” or “letter A.”
- Overlapping strokes, very low contrast, compression artifacts, shadows, and textured backgrounds can require threshold adjustment or preprocessing.
- Hough line and circle detection is intentionally conservative. Remaining geometry is preserved as Bézier contours.

## License

MIT.

## Version 0.2.1 processing fix

Version 0.2.1 normalizes the different array shapes returned by OpenCV `HoughLinesP` and `HoughCircles`. This fixes `TypeError: 'numpy.int32' object is not iterable` on OpenCV builds that return line segments as `(N, 4)` rather than `(N, 1, 4)`.


## GitHub release and project governance

- Release procedure: [`GITHUB_RELEASE_GUIDE.md`](GITHUB_RELEASE_GUIDE.md)
- Change history: [`CHANGELOG.md`](CHANGELOG.md)
- Citation metadata: [`CITATION.cff`](CITATION.cff)
- Contributing: [`CONTRIBUTING.md`](CONTRIBUTING.md)
- Security policy: [`SECURITY.md`](SECURITY.md)
- Version 0.2.1 notes: [`RELEASE_NOTES_v0.2.1.md`](RELEASE_NOTES_v0.2.1.md)

MathDraw Studio is released under the MIT License. Copyright © 2026 Shajib Ghosh.
