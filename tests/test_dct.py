import numpy as np
from PIL import Image

from mathdraw.dct_image import DCTConfig, build_dct_model, reconstruct_dct


def test_full_dct_reconstructs_small_grayscale_image():
    array = np.arange(64, dtype=np.uint8).reshape(8, 8) * 4
    image = Image.fromarray(array, mode="L")
    model = build_dct_model(image, DCTConfig(max_width=8, max_height=8, coefficient_count=64, grayscale=True))
    reconstructed = np.asarray(reconstruct_dct(model))
    assert reconstructed.shape == array.shape
    assert np.max(np.abs(reconstructed.astype(int) - array.astype(int))) <= 1
