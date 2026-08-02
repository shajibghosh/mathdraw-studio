from PIL import Image, ImageDraw

from mathdraw.pipeline import PipelineConfig, process_image
from mathdraw.preprocess import PreprocessConfig
from mathdraw.contour import ContourConfig
from mathdraw.primitive import PrimitiveConfig


def test_hybrid_pipeline_returns_components():
    image = Image.new("RGB", (240, 180), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((40, 30, 180, 140), outline="black", width=4)
    draw.ellipse((80, 55, 140, 115), outline="black", width=4)
    config = PipelineConfig(
        mode="hybrid_vector",
        preprocess=PreprocessConfig(canny_low=20, canny_high=80),
        contour=ContourConfig(max_contours=50, samples_per_contour=12),
        primitives=PrimitiveConfig(detect_lines=True, detect_circles=False, min_line_length=25),
    )
    model = process_image(image, config)
    assert model.mode == "hybrid_vector"
    assert len(model.lines) + len(model.beziers) > 0
