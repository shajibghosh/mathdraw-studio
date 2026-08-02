from __future__ import annotations

import argparse
from pathlib import Path

from .contour import ContourConfig
from .dct_image import DCTConfig
from .exporters import export_bundle
from .fourier import FourierConfig
from .io import load_image, resize_to_limit
from .pipeline import PipelineConfig, process_image
from .preprocess import PreprocessConfig
from .primitive import PrimitiveConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert an image into mathematical drawing equations.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--output", type=Path, default=Path("mathdraw_output"))
    parser.add_argument("--mode", choices=["auto", "hybrid_vector", "fourier_contour", "dct_image"], default="auto")
    parser.add_argument("--coordinates", choices=["normalized_cartesian", "normalized_0_1", "pixel_top_left"], default="normalized_cartesian")
    parser.add_argument("--max-side", type=int, default=1000)
    parser.add_argument("--max-contours", type=int, default=220)
    parser.add_argument("--bezier-samples", type=int, default=80)
    parser.add_argument("--harmonics", type=int, default=18)
    parser.add_argument("--dct-width", type=int, default=128)
    parser.add_argument("--dct-height", type=int, default=128)
    parser.add_argument("--dct-coefficients", type=int, default=2400)
    parser.add_argument("--grayscale", action="store_true")
    parser.add_argument(
        "--dct-exact",
        action="store_true",
        help="Retain every DCT coefficient, giving exact reconstruction at the selected DCT resolution.",
    )
    parser.add_argument("--no-lines", action="store_true")
    parser.add_argument("--circles", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    image = load_image(args.image)
    if args.mode != "dct_image":
        image = resize_to_limit(image, args.max_side)
    config = PipelineConfig(
        mode=args.mode,
        preprocess=PreprocessConfig(),
        contour=ContourConfig(max_contours=args.max_contours, samples_per_contour=args.bezier_samples),
        primitives=PrimitiveConfig(detect_lines=not args.no_lines, detect_circles=args.circles),
        fourier=FourierConfig(max_contours=args.max_contours, harmonics=args.harmonics),
        dct=DCTConfig(args.dct_width, args.dct_height, args.dct_coefficients, args.grayscale, args.dct_exact),
    )
    model = process_image(image, config)
    paths = export_bundle(model, args.output, args.coordinates)
    print(f"Selected mode: {model.mode}")
    for name, path in paths.items():
        print(f"{name:10s} {path.resolve()}")


if __name__ == "__main__":
    main()
