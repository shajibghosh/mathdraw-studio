from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .models import CubicBezier


@dataclass(slots=True)
class CoordinateTransform:
    width: int
    height: int
    mode: str = "normalized_cartesian"

    def point(self, p: tuple[float, float]) -> tuple[float, float]:
        x, y = p
        if self.mode == "pixel_top_left":
            return float(x), float(y)
        if self.mode == "normalized_0_1":
            return x / max(1, self.width - 1), 1.0 - y / max(1, self.height - 1)
        # Preserve aspect ratio in centered Cartesian coordinates.
        scale = max(self.width, self.height) / 2.0
        return (x - self.width / 2.0) / scale, (self.height / 2.0 - y) / scale

    def scale_x(self, value: float) -> float:
        if self.mode == "pixel_top_left":
            return value
        if self.mode == "normalized_0_1":
            return value / max(1, self.width - 1)
        return value / (max(self.width, self.height) / 2.0)

    def scale_y(self, value: float) -> float:
        if self.mode == "pixel_top_left":
            return value
        if self.mode == "normalized_0_1":
            return -value / max(1, self.height - 1)
        return -value / (max(self.width, self.height) / 2.0)

    def radius(self, r: float) -> float:
        # Backward-compatible isotropic scale, appropriate for centered Cartesian mode.
        return abs(self.scale_x(r))


def resample_polyline(points: np.ndarray, count: int, closed: bool = True) -> np.ndarray:
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    if len(points) < 2:
        return points
    work = np.vstack([points, points[0]]) if closed and not np.allclose(points[0], points[-1]) else points
    seg = np.linalg.norm(np.diff(work, axis=0), axis=1)
    cumulative = np.concatenate([[0.0], np.cumsum(seg)])
    total = cumulative[-1]
    if total <= 1e-9:
        return np.repeat(work[:1], count, axis=0)
    samples = np.linspace(0.0, total, count, endpoint=not closed)
    x = np.interp(samples, cumulative, work[:, 0])
    y = np.interp(samples, cumulative, work[:, 1])
    return np.column_stack([x, y])


def smooth_closed_curve(points: np.ndarray, passes: int = 1) -> np.ndarray:
    result = np.asarray(points, dtype=float)
    if len(result) < 5:
        return result
    for _ in range(max(0, passes)):
        result = (
            np.roll(result, 2, axis=0)
            + 4 * np.roll(result, 1, axis=0)
            + 6 * result
            + 4 * np.roll(result, -1, axis=0)
            + np.roll(result, -2, axis=0)
        ) / 16.0
    return result


def catmull_rom_to_beziers(points: np.ndarray, closed: bool = True, tension: float = 1.0) -> list[CubicBezier]:
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    n = len(pts)
    if n < 2:
        return []
    segments: list[CubicBezier] = []
    count = n if closed else n - 1
    for i in range(count):
        p0 = pts[(i - 1) % n] if closed else pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
        c1 = p1 + (p2 - p0) * (tension / 6.0)
        c2 = p2 - (p3 - p1) * (tension / 6.0)
        segments.append(
            CubicBezier(tuple(p1), tuple(c1), tuple(c2), tuple(p2))
        )
    return segments


def sample_cubic(segment: CubicBezier, count: int = 24) -> np.ndarray:
    p0, p1, p2, p3 = [np.asarray(p, dtype=float) for p in (segment.p0, segment.p1, segment.p2, segment.p3)]
    t = np.linspace(0.0, 1.0, count)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def line_angle(p0: tuple[float, float], p1: tuple[float, float]) -> float:
    return math.atan2(p1[1] - p0[1], p1[0] - p0[0])
