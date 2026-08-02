from __future__ import annotations

import math
import numpy as np
from PIL import Image


def compare_images(reference: Image.Image, reconstruction: Image.Image) -> dict[str, float]:
    ref = np.asarray(reference.convert("RGB").resize(reconstruction.size, Image.Resampling.LANCZOS), dtype=np.float64)
    out = np.asarray(reconstruction.convert("RGB"), dtype=np.float64)
    mse = float(np.mean((ref - out) ** 2))
    rmse = math.sqrt(mse)
    psnr = float("inf") if mse == 0 else 20 * math.log10(255.0 / rmse)
    mae = float(np.mean(np.abs(ref - out)))
    return {"mse": mse, "rmse": rmse, "mae": mae, "psnr_db": psnr}
