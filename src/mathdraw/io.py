from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps


COMMON_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif", ".ico", ".ppm", ".pgm"
}


def load_image(path: str | Path, pdf_page: int = 0) -> Image.Image:
    """Load a common raster image, SVG, PDF page, HEIF/HEIC, or camera RAW when optional packages exist."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".heic", ".heif", ".avif"}:
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError as exc:
            raise RuntimeError("Install optional package 'pillow-heif' to open HEIC/HEIF/AVIF files.") from exc

    if suffix == ".pdf":
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("Install optional package 'PyMuPDF' to open PDF files.") from exc
        document = fitz.open(path)
        if not 0 <= pdf_page < len(document):
            raise ValueError(f"PDF page index {pdf_page} is outside 0..{len(document)-1}.")
        page = document[pdf_page]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        document.close()
        return image

    if suffix == ".svg":
        try:
            import cairosvg
        except ImportError as exc:
            raise RuntimeError("Install optional package 'cairosvg' to open SVG files.") from exc
        png_bytes = cairosvg.svg2png(url=str(path), output_width=1600)
        return Image.open(BytesIO(png_bytes)).convert("RGB")

    if suffix in {".dng", ".cr2", ".cr3", ".nef", ".arw", ".rw2", ".orf"}:
        try:
            import rawpy
        except ImportError as exc:
            raise RuntimeError("Install optional package 'rawpy' to open camera RAW files.") from exc
        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess()
        return Image.fromarray(rgb).convert("RGB")

    image = Image.open(path)
    try:
        image.seek(0)
    except EOFError:
        pass
    return ImageOps.exif_transpose(image).convert("RGB")


def resize_to_limit(image: Image.Image, max_side: int) -> Image.Image:
    if max(image.size) <= max_side:
        return image.copy()
    ratio = max_side / max(image.size)
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    return image.resize(size, Image.Resampling.LANCZOS)
