from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .models import BezierPath, CubicBezier


@dataclass(slots=True)
class ContourConfig:
    min_length: float = 12.0
    min_area: float = 1.5
    max_contours: int = 300
    samples_per_contour: int = 80
    smoothing_passes: int = 0
    simplify_epsilon: float = 0.8


def _line_cubic(p0: np.ndarray, p3: np.ndarray) -> CubicBezier:
    delta = (p3 - p0) / 3.0
    return CubicBezier(tuple(p0), tuple(p0 + delta), tuple(p0 + 2.0 * delta), tuple(p3))


def _depth(index: int, hierarchy: np.ndarray) -> int:
    depth = 0
    parent = int(hierarchy[index][3])
    while parent >= 0:
        depth += 1
        parent = int(hierarchy[parent][3])
    return depth


def extract_bezier_paths(mask: np.ndarray, config: ContourConfig, filled: bool = False) -> list[BezierPath]:
    mode = cv2.RETR_TREE if filled else cv2.RETR_LIST
    contours, hierarchy = cv2.findContours(mask, mode, cv2.CHAIN_APPROX_NONE)
    if hierarchy is None:
        return []
    hierarchy = hierarchy[0]
    candidates: list[tuple[int, float, float, np.ndarray]] = []
    for index, contour in enumerate(contours):
        length = cv2.arcLength(contour, True)
        area = abs(cv2.contourArea(contour))
        if length < config.min_length or (area < config.min_area and length < config.min_length * 1.6):
            continue
        candidates.append((index, length, area, contour))

    # Parent regions before holes; within each depth, larger regions first.
    candidates.sort(key=lambda item: (_depth(item[0], hierarchy), -item[2], -item[1]))
    paths: list[BezierPath] = []
    for output_index, (index, length, _area, contour) in enumerate(candidates[: config.max_contours]):
        epsilon = max(0.25, min(config.simplify_epsilon, 0.004 * length))
        simplified = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2).astype(float)
        if len(simplified) < 3:
            continue
        # Limit very large contours while preserving the original polygon order.
        if len(simplified) > config.samples_per_contour:
            positions = np.linspace(0, len(simplified), config.samples_per_contour, endpoint=False).astype(int)
            simplified = simplified[positions]
        segments = [
            _line_cubic(simplified[i], simplified[(i + 1) % len(simplified)])
            for i in range(len(simplified))
        ]
        depth = _depth(index, hierarchy)
        fill = ("black" if depth % 2 == 0 else "white") if filled else "none"
        paths.append(
            BezierPath(
                segments=segments,
                closed=True,
                width=0.8 if not filled else 0.0,
                label=f"{'region' if filled else 'contour'}_{output_index+1}",
                fill=fill,
            )
        )
    return paths
