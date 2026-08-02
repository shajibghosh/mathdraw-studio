from __future__ import annotations

import numpy as np
from PIL import Image

from mathdraw.dct_image import DCTConfig, build_dct_model, reconstruct_dct


def test_full_dct_is_exact_at_selected_resolution():
    values = np.arange(8 * 8 * 3, dtype=np.uint8).reshape(8, 8, 3)
    image = Image.fromarray(values, mode="RGB")
    model = build_dct_model(image, DCTConfig(max_width=8, max_height=8, coefficient_count=1, exact=True))
    assert len(model.coefficients) == 8 * 8 * 3
    reconstructed = np.asarray(reconstruct_dct(model))
    assert np.array_equal(reconstructed, values)
