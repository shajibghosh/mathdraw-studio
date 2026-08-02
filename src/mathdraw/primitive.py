from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np
from PIL import Image

from .models import CirclePrimitive, LinePrimitive
from .preprocess import grayscale


@dataclass(slots=True)
class PrimitiveConfig:
    detect_lines: bool = True
    detect_circles: bool = False
    min_line_length: int = 30
    line_gap: int = 10
    hough_threshold: int = 25
    max_lines: int = 100
    max_circles: int = 40


def morphological_skeleton(mask: np.ndarray) -> np.ndarray:
    image = (mask > 0).astype(np.uint8) * 255
    skeleton = np.zeros_like(image)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while cv2.countNonZero(image) > 0:
        eroded = cv2.erode(image, element)
        opened = cv2.dilate(eroded, element)
        residue = cv2.subtract(image, opened)
        skeleton = cv2.bitwise_or(skeleton, residue)
        image = eroded
    return skeleton


def estimate_stroke_width(mask: np.ndarray, skeleton: np.ndarray) -> float:
    distance = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    values = distance[skeleton > 0]
    if values.size == 0:
        return 2.0
    return float(np.clip(2.0 * np.median(values), 1.0, 16.0))


def _angle_delta(a: float, b: float) -> float:
    d = abs(a - b) % math.pi
    return min(d, math.pi - d)


def _normalize_hough_lines(raw: np.ndarray | None) -> list[tuple[int, int, int, int]]:
    """Normalize OpenCV HoughLinesP output across binding/version shape variants.

    OpenCV commonly returns ``(N, 1, 4)``, but some builds return ``(N, 4)``
    and a single detection may be represented as ``(4,)``.  Reshaping by the
    four segment coordinates prevents code from accidentally iterating over a
    scalar ``numpy.int32`` value. Malformed or non-finite records are ignored.
    """
    if raw is None:
        return []

    values = np.asarray(raw)
    if values.size == 0 or values.size % 4 != 0:
        return []

    segments = values.reshape(-1, 4)
    output: list[tuple[int, int, int, int]] = []
    for row in segments:
        row = np.asarray(row, dtype=float)
        if not np.all(np.isfinite(row)):
            continue
        output.append(tuple(int(round(value)) for value in row))
    return output


def _normalize_hough_circles(raw: np.ndarray | None) -> list[tuple[int, int, int]]:
    """Normalize OpenCV HoughCircles output to integer ``(x, y, r)`` tuples."""
    if raw is None:
        return []

    values = np.asarray(raw)
    if values.size == 0 or values.size % 3 != 0:
        return []

    circles = values.reshape(-1, 3)
    output: list[tuple[int, int, int]] = []
    for row in circles:
        row = np.asarray(row, dtype=float)
        if not np.all(np.isfinite(row)):
            continue
        x, y, radius = (int(round(value)) for value in row)
        if radius > 0:
            output.append((x, y, radius))
    return output


def _line_support(mask: np.ndarray, line: tuple[float, float, float, float], radius: int = 2) -> float:
    x1, y1, x2, y2 = line
    samples = max(2, int(round(math.hypot(x2 - x1, y2 - y1))))
    xs = np.linspace(x1, x2, samples)
    ys = np.linspace(y1, y2, samples)
    h, w = mask.shape
    supported = 0
    for x, y in zip(xs, ys):
        xi, yi = int(round(x)), int(round(y))
        x0, x3 = max(0, xi - radius), min(w, xi + radius + 1)
        y0, y3 = max(0, yi - radius), min(h, yi + radius + 1)
        if x0 < x3 and y0 < y3 and np.any(mask[y0:y3, x0:x3] > 0):
            supported += 1
    return supported / samples


def _merge_hough_lines(raw_lines: list[tuple[int, int, int, int]], angle_tol_deg: float, rho_tol: float, gap_tol: float) -> list[tuple[float, float, float, float]]:
    records = []
    for x1, y1, x2, y2 in raw_lines:
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < 1e-6:
            continue
        angle = math.atan2(dy, dx) % math.pi
        d = np.array([math.cos(angle), math.sin(angle)])
        n = np.array([-d[1], d[0]])
        p1, p2 = np.array([x1, y1], float), np.array([x2, y2], float)
        rho = float(np.dot((p1 + p2) / 2.0, n))
        t0, t1 = sorted([float(np.dot(p1, d)), float(np.dot(p2, d))])
        records.append((angle, rho, t0, t1, length))
    records.sort(key=lambda r: r[4], reverse=True)

    clusters: list[dict] = []
    for angle, rho, t0, t1, _length in records:
        target = None
        for cluster in clusters:
            if _angle_delta(angle, cluster["angle"]) <= math.radians(angle_tol_deg) and abs(rho - cluster["rho"]) <= rho_tol:
                target = cluster
                break
        if target is None:
            clusters.append({"angle": angle, "rho": rho, "items": [(t0, t1, rho, angle)]})
        else:
            target["items"].append((t0, t1, rho, angle))
            target["rho"] = float(np.mean([x[2] for x in target["items"]]))
            target["angle"] = float(np.mean([x[3] for x in target["items"]]))

    output: list[tuple[float, float, float, float]] = []
    for cluster in clusters:
        angle = cluster["angle"]
        d = np.array([math.cos(angle), math.sin(angle)])
        n = np.array([-d[1], d[0]])
        rho = cluster["rho"]
        intervals = sorted((item[0], item[1]) for item in cluster["items"])
        merged: list[list[float]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1] + gap_tol:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        for start, end in merged:
            p0 = n * rho + d * start
            p1 = n * rho + d * end
            output.append((float(p0[0]), float(p0[1]), float(p1[0]), float(p1[1])))
    return output


def detect_primitives(
    image: Image.Image,
    edge_map: np.ndarray,
    config: PrimitiveConfig,
    foreground_mask: np.ndarray | None = None,
) -> tuple[list[LinePrimitive], list[CirclePrimitive], np.ndarray]:
    lines: list[LinePrimitive] = []
    circles: list[CirclePrimitive] = []
    primitive_mask = np.zeros_like(edge_map)
    stroke_width = 2.0

    if config.detect_lines:
        base = foreground_mask if foreground_mask is not None else edge_map
        if float(np.mean(base > 0)) > 0.28:
            skeleton = edge_map
        else:
            skeleton = morphological_skeleton(base)
        stroke_width = estimate_stroke_width(base, skeleton)
        adaptive_min_length = max(config.min_line_length, int(0.12 * min(image.size)))
        raw = cv2.HoughLinesP(
            skeleton,
            rho=1,
            theta=np.pi / 360,
            threshold=config.hough_threshold,
            minLineLength=adaptive_min_length,
            maxLineGap=config.line_gap,
        )
        if raw is not None:
            candidates = _normalize_hough_lines(raw)
            candidates = [line for line in candidates if _line_support(skeleton, line, radius=2) >= 0.93]
            merged = _merge_hough_lines(candidates, angle_tol_deg=3.0, rho_tol=max(2.0, stroke_width), gap_tol=config.line_gap * 1.5)
            merged.sort(key=lambda l: math.hypot(l[2] - l[0], l[3] - l[1]), reverse=True)
            accepted = 0
            for x1, y1, x2, y2 in merged:
                if accepted >= config.max_lines:
                    break
                if math.hypot(x2 - x1, y2 - y1) < adaptive_min_length:
                    continue
                if _line_support(skeleton, (x1, y1, x2, y2), radius=2) < 0.90:
                    continue
                width = max(1.0, stroke_width)
                lines.append(LinePrimitive((x1, y1), (x2, y2), width=width))
                accepted += 1
                cv2.line(
                    primitive_mask,
                    (round(x1), round(y1)),
                    (round(x2), round(y2)),
                    255,
                    max(2, round(width * 1.8)),
                    cv2.LINE_AA,
                )

    if config.detect_circles:
        gray = cv2.medianBlur(grayscale(image), 5)
        min_dist = max(10, min(image.size) // 25)
        detected = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min_dist,
            param1=120,
            param2=28,
            minRadius=3,
            maxRadius=max(5, min(image.size) // 3),
        )
        if detected is not None:
            for x, y, r in _normalize_hough_circles(detected)[: config.max_circles]:
                width = max(1.0, stroke_width)
                circles.append(CirclePrimitive((float(x), float(y)), float(r), width=width))
                cv2.circle(primitive_mask, (x, y), r, 255, max(2, round(width * 1.8)), cv2.LINE_AA)

    return lines, circles, primitive_mask
