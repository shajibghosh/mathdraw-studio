from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image
from scipy.fft import dctn, idctn

from .models import DCTCoefficient, DCTImageModel


@dataclass(slots=True)
class DCTConfig:
    max_width: int = 128
    max_height: int = 128
    coefficient_count: int = 1800
    grayscale: bool = False
    exact: bool = False


def build_dct_model(image: Image.Image, config: DCTConfig) -> DCTImageModel:
    work = image.convert("L" if config.grayscale else "RGB")
    work.thumbnail((config.max_width, config.max_height), Image.Resampling.LANCZOS)
    array = np.asarray(work, dtype=np.float64)
    if array.ndim == 2:
        array = array[:, :, None]
    h, w, channels = array.shape
    all_coefficients: list[DCTCoefficient] = []
    per_channel = max(1, config.coefficient_count // channels)
    for channel in range(channels):
        coeff = dctn(array[:, :, channel], norm="ortho")
        if config.exact:
            # Row-major order avoids an unnecessary full sort and makes exact coefficient reports stable.
            for v in range(coeff.shape[0]):
                for u in range(coeff.shape[1]):
                    all_coefficients.append(DCTCoefficient(channel, v, u, float(coeff[v, u])))
        else:
            count = min(per_channel, coeff.size)
            flat_idx = np.argpartition(np.abs(coeff).ravel(), -count)[-count:]
            flat_idx = flat_idx[np.argsort(np.abs(coeff).ravel()[flat_idx])[::-1]]
            for idx in flat_idx:
                v, u = np.unravel_index(int(idx), coeff.shape)
                all_coefficients.append(DCTCoefficient(channel, int(v), int(u), float(coeff[v, u])))
    return DCTImageModel(width=w, height=h, channels=channels, coefficients=all_coefficients, color_mode=work.mode)


def reconstruct_dct(model: DCTImageModel) -> Image.Image:
    coeff = np.zeros((model.height, model.width, model.channels), dtype=np.float64)
    for c in model.coefficients:
        coeff[c.v, c.u, c.channel] = c.value
    channels = [idctn(coeff[:, :, i], norm="ortho") for i in range(model.channels)]
    array = np.stack(channels, axis=-1)
    array = np.clip(np.rint(array), 0, 255).astype(np.uint8)
    if model.channels == 1:
        return Image.fromarray(array[:, :, 0], mode="L")
    return Image.fromarray(array, mode=model.color_mode)
