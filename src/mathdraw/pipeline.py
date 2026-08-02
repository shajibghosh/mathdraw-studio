from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

import cv2

from .contour import ContourConfig, extract_bezier_paths
from .dct_image import DCTConfig, build_dct_model
from .fourier import FourierConfig, extract_fourier_paths
from .models import DrawingModel
from .preprocess import PreprocessConfig, choose_auto_mode, image_characteristics, make_edge_map, make_foreground_mask
from .primitive import PrimitiveConfig, detect_primitives


@dataclass(slots=True)
class PipelineConfig:
    mode: str = "auto"
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    contour: ContourConfig = field(default_factory=ContourConfig)
    primitives: PrimitiveConfig = field(default_factory=PrimitiveConfig)
    fourier: FourierConfig = field(default_factory=FourierConfig)
    dct: DCTConfig = field(default_factory=DCTConfig)


def process_image(image: Image.Image, config: PipelineConfig) -> DrawingModel:
    image = image.convert("RGB")
    selected_mode = choose_auto_mode(image) if config.mode == "auto" else config.mode
    metadata = {"requested_mode": config.mode, "selected_mode": selected_mode, **image_characteristics(image)}

    if selected_mode == "dct_image":
        dct = build_dct_model(image, config.dct)
        metadata.update({
            "dct_coefficients": len(dct.coefficients),
            "dct_full_coefficient_count": dct.width * dct.height * dct.channels,
            "dct_exact_at_equation_resolution": len(dct.coefficients) == dct.width * dct.height * dct.channels,
        })
        return DrawingModel(
            mode=selected_mode,
            source_size=image.size,
            canvas_size=(dct.width, dct.height),
            dct=dct,
            metadata=metadata,
        )

    edge_map = make_edge_map(image, config.preprocess)
    if selected_mode == "fourier_contour":
        fourier_paths = extract_fourier_paths(edge_map, config.fourier)
        metadata.update({"edge_pixels": int((edge_map > 0).sum()), "fourier_paths": len(fourier_paths)})
        return DrawingModel(
            mode=selected_mode,
            source_size=image.size,
            canvas_size=image.size,
            fourier_paths=fourier_paths,
            metadata=metadata,
        )

    foreground = make_foreground_mask(image)
    lines, circles, primitive_mask = detect_primitives(
        image, edge_map, config.primitives, foreground_mask=foreground
    )
    residual = cv2.bitwise_and(foreground, cv2.bitwise_not(primitive_mask))
    beziers = extract_bezier_paths(residual, config.contour, filled=True)
    metadata.update(
        {
            "edge_pixels": int((edge_map > 0).sum()),
            "line_count": len(lines),
            "circle_count": len(circles),
            "bezier_path_count": len(beziers),
        }
    )
    return DrawingModel(
        mode="hybrid_vector",
        source_size=image.size,
        canvas_size=image.size,
        lines=lines,
        circles=circles,
        beziers=beziers,
        metadata=metadata,
    )
