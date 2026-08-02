from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

Point = tuple[float, float]


@dataclass(slots=True)
class LinePrimitive:
    p0: Point
    p1: Point
    width: float = 1.5


@dataclass(slots=True)
class CirclePrimitive:
    center: Point
    radius: float
    width: float = 1.5


@dataclass(slots=True)
class EllipsePrimitive:
    center: Point
    radii: Point
    angle_deg: float = 0.0
    width: float = 1.5


@dataclass(slots=True)
class CubicBezier:
    p0: Point
    p1: Point
    p2: Point
    p3: Point


@dataclass(slots=True)
class BezierPath:
    segments: list[CubicBezier]
    closed: bool = False
    width: float = 1.25
    label: str = "contour"
    fill: str = "none"  # one of: none, black, white


@dataclass(slots=True)
class FourierCoefficient:
    harmonic: int
    real: float
    imag: float


@dataclass(slots=True)
class FourierPath:
    coefficients: list[FourierCoefficient]
    width: float = 1.25
    label: str = "contour"


@dataclass(slots=True)
class DCTCoefficient:
    channel: int
    v: int
    u: int
    value: float


@dataclass(slots=True)
class DCTImageModel:
    width: int
    height: int
    channels: int
    coefficients: list[DCTCoefficient]
    color_mode: str = "RGB"


@dataclass(slots=True)
class DrawingModel:
    mode: str
    source_size: tuple[int, int]
    canvas_size: tuple[int, int]
    lines: list[LinePrimitive] = field(default_factory=list)
    circles: list[CirclePrimitive] = field(default_factory=list)
    ellipses: list[EllipsePrimitive] = field(default_factory=list)
    beziers: list[BezierPath] = field(default_factory=list)
    fourier_paths: list[FourierPath] = field(default_factory=list)
    dct: Optional[DCTImageModel] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DrawingModel":
        return cls(
            mode=payload["mode"],
            source_size=tuple(payload["source_size"]),
            canvas_size=tuple(payload["canvas_size"]),
            lines=[
                LinePrimitive(tuple(x["p0"]), tuple(x["p1"]), x.get("width", 1.5))
                for x in payload.get("lines", [])
            ],
            circles=[
                CirclePrimitive(tuple(x["center"]), x["radius"], x.get("width", 1.5))
                for x in payload.get("circles", [])
            ],
            ellipses=[
                EllipsePrimitive(
                    tuple(x["center"]), tuple(x["radii"]), x.get("angle_deg", 0.0), x.get("width", 1.5)
                )
                for x in payload.get("ellipses", [])
            ],
            beziers=[
                BezierPath(
                    segments=[
                        CubicBezier(tuple(s["p0"]), tuple(s["p1"]), tuple(s["p2"]), tuple(s["p3"]))
                        for s in x.get("segments", [])
                    ],
                    closed=x.get("closed", False),
                    width=x.get("width", 1.25),
                    label=x.get("label", "contour"),
                    fill=x.get("fill", "none"),
                )
                for x in payload.get("beziers", [])
            ],
            fourier_paths=[
                FourierPath(
                    coefficients=[
                        FourierCoefficient(c["harmonic"], c["real"], c["imag"])
                        for c in x.get("coefficients", [])
                    ],
                    width=x.get("width", 1.25),
                    label=x.get("label", "contour"),
                )
                for x in payload.get("fourier_paths", [])
            ],
            dct=(
                DCTImageModel(
                    width=payload["dct"]["width"],
                    height=payload["dct"]["height"],
                    channels=payload["dct"]["channels"],
                    coefficients=[DCTCoefficient(**c) for c in payload["dct"].get("coefficients", [])],
                    color_mode=payload["dct"].get("color_mode", "RGB"),
                )
                if payload.get("dct")
                else None
            ),
            metadata=payload.get("metadata", {}),
        )
