from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass(slots=True)
class PreprocessConfig:
    blur_sigma: float = 1.0
    canny_low: int = 40
    canny_high: int = 130
    use_threshold_edges: bool = True
    close_gaps: bool = True


def pil_to_rgb(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"), dtype=np.uint8)


def grayscale(image: Image.Image | np.ndarray) -> np.ndarray:
    rgb = pil_to_rgb(image) if isinstance(image, Image.Image) else image
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)


def make_edge_map(image: Image.Image, config: PreprocessConfig) -> np.ndarray:
    gray = grayscale(image)
    if config.blur_sigma > 0:
        k = max(3, int(round(config.blur_sigma * 4)) | 1)
        gray_blur = cv2.GaussianBlur(gray, (k, k), config.blur_sigma)
    else:
        gray_blur = gray
    edges = cv2.Canny(gray_blur, config.canny_low, config.canny_high, L2gradient=True)
    if config.use_threshold_edges:
        _, binary = cv2.threshold(gray_blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        gradient = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
        edges = cv2.bitwise_or(edges, gradient)
    if config.close_gaps:
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    return edges


def image_characteristics(image: Image.Image) -> dict[str, float]:
    rgb = pil_to_rgb(image.resize((128, 128), Image.Resampling.BILINEAR))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    white_fraction = float(np.mean(gray > 235))
    dark_fraction = float(np.mean(gray < 80))
    edge_density = float(np.mean(edges > 0))
    saturation = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[:, :, 1]
    mean_saturation = float(np.mean(saturation) / 255.0)
    hist = np.histogram(gray, bins=32, range=(0, 256), density=True)[0]
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist + 1e-12)))
    return {
        "white_fraction": white_fraction,
        "dark_fraction": dark_fraction,
        "edge_density": edge_density,
        "mean_saturation": mean_saturation,
        "gray_entropy": entropy,
    }


def choose_auto_mode(image: Image.Image) -> str:
    c = image_characteristics(image)
    if c["white_fraction"] > 0.35 and c["mean_saturation"] < 0.18 and c["edge_density"] < 0.30:
        return "hybrid_vector"
    return "dct_image"


def make_foreground_mask(image: Image.Image, blur_sigma: float = 0.6) -> np.ndarray:
    """Return a binary mask with foreground strokes/regions equal to 255."""
    gray = grayscale(image)
    if blur_sigma > 0:
        k = max(3, int(round(blur_sigma * 4)) | 1)
        gray = cv2.GaussianBlur(gray, (k, k), blur_sigma)
    # Choose polarity from border brightness, which is usually background for drawings.
    border = np.concatenate([gray[0, :], gray[-1, :], gray[:, 0], gray[:, -1]])
    background_is_light = float(np.median(border)) >= 127.0
    otsu_value, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if background_is_light:
        threshold_value = min(250.0, max(float(otsu_value), 225.0))
        mask = (gray < threshold_value).astype(np.uint8) * 255
    else:
        threshold_value = max(5.0, min(float(otsu_value), 30.0))
        mask = (gray > threshold_value).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    return mask
