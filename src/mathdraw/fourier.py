from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .geometry import resample_polyline
from .models import FourierCoefficient, FourierPath


@dataclass(slots=True)
class FourierConfig:
    min_length: float = 20.0
    max_contours: int = 120
    contour_samples: int = 128
    harmonics: int = 18


def extract_fourier_paths(edge_map: np.ndarray, config: FourierConfig) -> list[FourierPath]:
    contours, _ = cv2.findContours(edge_map, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    contours = [c for c in contours if cv2.arcLength(c, True) >= config.min_length]
    contours.sort(key=lambda c: cv2.arcLength(c, True), reverse=True)
    paths: list[FourierPath] = []
    for i, contour in enumerate(contours[: config.max_contours]):
        pts = resample_polyline(contour.reshape(-1, 2), config.contour_samples, closed=True)
        z = pts[:, 0] + 1j * pts[:, 1]
        coeff = np.fft.fft(z) / len(z)
        freq = np.fft.fftfreq(len(z), d=1.0 / len(z)).astype(int)
        keep = np.argsort(np.abs(freq))[: 2 * config.harmonics + 1]
        coefficients = [
            FourierCoefficient(int(freq[j]), float(coeff[j].real), float(coeff[j].imag))
            for j in sorted(keep, key=lambda idx: int(freq[idx]))
        ]
        paths.append(FourierPath(coefficients=coefficients, width=1.2, label=f"fourier_contour_{i+1}"))
    return paths


def evaluate_fourier_path(path: FourierPath, samples: int = 500) -> np.ndarray:
    t = np.linspace(0.0, 1.0, samples, endpoint=False)
    z = np.zeros(samples, dtype=complex)
    for c in path.coefficients:
        z += complex(c.real, c.imag) * np.exp(2j * np.pi * c.harmonic * t)
    return np.column_stack([z.real, z.imag])
