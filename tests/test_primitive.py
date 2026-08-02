from __future__ import annotations

import numpy as np

from mathdraw.primitive import _normalize_hough_circles, _normalize_hough_lines


def test_normalize_hough_lines_accepts_standard_n_1_4_shape():
    raw = np.array([[[10, 20, 100, 20]], [[4, 8, 4, 90]]], dtype=np.int32)
    assert _normalize_hough_lines(raw) == [(10, 20, 100, 20), (4, 8, 4, 90)]


def test_normalize_hough_lines_accepts_flat_n_4_shape_that_caused_numpy_int32_error():
    raw = np.array([[10, 20, 100, 20], [4, 8, 4, 90]], dtype=np.int32)
    assert _normalize_hough_lines(raw) == [(10, 20, 100, 20), (4, 8, 4, 90)]


def test_normalize_hough_lines_accepts_single_flat_segment():
    raw = np.array([10, 20, 100, 20], dtype=np.int32)
    assert _normalize_hough_lines(raw) == [(10, 20, 100, 20)]


def test_normalize_hough_lines_ignores_malformed_and_nonfinite_values():
    assert _normalize_hough_lines(np.array([1, 2, 3], dtype=np.int32)) == []
    raw = np.array([[1.0, 2.0, np.nan, 4.0], [5.2, 6.2, 7.8, 8.8]])
    assert _normalize_hough_lines(raw) == [(5, 6, 8, 9)]


def test_normalize_hough_circles_accepts_common_shape_variants():
    standard = np.array([[[12.2, 15.8, 5.1], [30.0, 31.0, 0.0]]], dtype=np.float32)
    flat = np.array([[12.2, 15.8, 5.1]], dtype=np.float32)
    assert _normalize_hough_circles(standard) == [(12, 16, 5)]
    assert _normalize_hough_circles(flat) == [(12, 16, 5)]


def test_detect_primitives_handles_flat_hough_output(monkeypatch):
    import cv2
    from PIL import Image

    from mathdraw.primitive import PrimitiveConfig, detect_primitives

    edge_map = np.zeros((128, 128), dtype=np.uint8)
    cv2.line(edge_map, (10, 64), (110, 64), 255, 1)
    image = Image.new("RGB", (128, 128), "white")

    monkeypatch.setattr(
        cv2,
        "HoughLinesP",
        lambda *args, **kwargs: np.array([[10, 64, 110, 64]], dtype=np.int32),
    )

    lines, circles, _mask = detect_primitives(
        image,
        edge_map,
        PrimitiveConfig(detect_lines=True, detect_circles=False, min_line_length=20),
        foreground_mask=edge_map,
    )

    assert len(lines) == 1
    assert circles == []
