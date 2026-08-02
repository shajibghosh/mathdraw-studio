import numpy as np

from mathdraw.fourier import evaluate_fourier_path
from mathdraw.models import FourierCoefficient, FourierPath


def test_fourier_unit_circle():
    path = FourierPath([FourierCoefficient(1, 10.0, 0.0)])
    points = evaluate_fourier_path(path, 200)
    radii = np.sqrt(points[:, 0] ** 2 + points[:, 1] ** 2)
    assert np.allclose(radii, 10.0, atol=1e-6)
