# Architecture

## Data flow

```text
Image loader
  -> optional resize
  -> mode selection
      -> Hybrid vector
           edge map -> line/circle detection -> residual contours -> Bézier paths
      -> Fourier contour
           edge map -> closed contours -> uniform resampling -> FFT coefficients
      -> DCT image
           resize -> per-channel 2D DCT -> coefficient selection
  -> DrawingModel
  -> equation formatter
  -> renderer
  -> TXT / JSON / SVG / PNG exporters
```

## Why there are multiple mathematical models

A single compact equation is inappropriate for all image classes.

- Geometry-heavy drawings benefit from explicit primitives and parametric curves.
- Smooth closed silhouettes benefit from Fourier descriptors.
- Full-tone images require a spatial basis such as DCT, Fourier, wavelets, or pixel indicator functions.

The shared `DrawingModel` allows the GUI, CLI, renderer, and exporters to work with all representations.

## Threading

The GUI runs image conversion in a single background worker thread. Tkinter updates remain on the main thread through `after()`. This prevents the interface from freezing during contour extraction or large coefficient selection.

## Extension points

Good future additions include:

- semantic object segmentation before contour fitting;
- OCR that replaces glyph outlines with typed text and font metadata;
- differentiable spline fitting;
- superpixel or region equations for flat-color artwork;
- SVG path import without rasterization;
- multi-page PDF and multi-frame animation processing;
- GPU-backed transforms through CuPy;
- export directly to Desmos, GeoGebra, Mathematica, MATLAB, or LaTeX/TikZ.
