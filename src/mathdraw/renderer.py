from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from .dct_image import reconstruct_dct
from .fourier import evaluate_fourier_path
from .geometry import sample_cubic
from .models import DrawingModel


def render_model(model: DrawingModel, scale: int = 1, background: int = 255) -> Image.Image:
    if model.dct is not None:
        image = reconstruct_dct(model.dct)
        if scale != 1:
            image = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        return image.convert("RGB")

    width, height = model.canvas_size
    canvas = np.full((height * scale, width * scale, 3), background, dtype=np.uint8)

    def pt(p: tuple[float, float]) -> tuple[int, int]:
        return int(round(p[0] * scale)), int(round(p[1] * scale))

    for line in model.lines:
        cv2.line(canvas, pt(line.p0), pt(line.p1), (0, 0, 0), max(1, round(line.width * scale)), cv2.LINE_AA)
    for circle in model.circles:
        cv2.circle(canvas, pt(circle.center), max(1, round(circle.radius * scale)), (0, 0, 0), max(1, round(circle.width * scale)), cv2.LINE_AA)
    for ellipse in model.ellipses:
        cv2.ellipse(
            canvas,
            pt(ellipse.center),
            (max(1, round(ellipse.radii[0] * scale)), max(1, round(ellipse.radii[1] * scale))),
            ellipse.angle_deg,
            0,
            360,
            (0, 0, 0),
            max(1, round(ellipse.width * scale)),
            cv2.LINE_AA,
        )
    for path in model.beziers:
        sampled = [sample_cubic(segment, 8) for segment in path.segments]
        if sampled:
            points = np.vstack(sampled)
            points = np.rint(points * scale).astype(np.int32).reshape(-1, 1, 2)
            if path.fill in {"black", "white"}:
                fill_color = (0, 0, 0) if path.fill == "black" else (255, 255, 255)
                cv2.fillPoly(canvas, [points], fill_color, cv2.LINE_AA)
            if path.width > 0:
                cv2.polylines(canvas, [points], path.closed, (0, 0, 0), max(1, round(path.width * scale)), cv2.LINE_AA)
    for path in model.fourier_paths:
        points = evaluate_fourier_path(path, 600)
        points = np.rint(points * scale).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(canvas, [points], True, (0, 0, 0), max(1, round(path.width * scale)), cv2.LINE_AA)
    return Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
