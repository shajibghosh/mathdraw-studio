from __future__ import annotations

import math

from .geometry import CoordinateTransform
from .models import DrawingModel


def _f(value: float, precision: int = 6) -> str:
    if abs(value) < 0.5 * 10 ** (-precision):
        value = 0.0
    return f"{value:.{precision}f}".rstrip("0").rstrip(".") or "0"


def _bezier_component(a: float, b: float, c: float, d: float) -> str:
    return f"(1-t)^3({_f(a)})+3(1-t)^2t({_f(b)})+3(1-t)t^2({_f(c)})+t^3({_f(d)})"


def equations_for_model(model: DrawingModel, coordinate_mode: str = "normalized_cartesian") -> str:
    width, height = model.canvas_size
    transform = CoordinateTransform(width, height, coordinate_mode)
    lines: list[str] = []
    lines.append("MathDraw Studio equation export")
    lines.append(f"mode = {model.mode}")
    lines.append(f"canvas = {width} x {height}")
    lines.append(f"coordinates = {coordinate_mode}")
    lines.append("")

    for i, line in enumerate(model.lines, 1):
        p0, p1 = transform.point(line.p0), transform.point(line.p1)
        lines.extend([
            f"[line_{i}]  0 <= t <= 1",
            f"x(t) = {_f(p0[0])} + ({_f(p1[0]-p0[0])}) t",
            f"y(t) = {_f(p0[1])} + ({_f(p1[1]-p0[1])}) t",
            "",
        ])

    for i, circle in enumerate(model.circles, 1):
        center = transform.point(circle.center)
        rx = transform.scale_x(circle.radius)
        ry = transform.scale_y(circle.radius)
        lines.extend([
            f"[circle_{i}]  0 <= t < 2*pi",
            f"x(t) = {_f(center[0])} + ({_f(rx)}) cos(t)",
            f"y(t) = {_f(center[1])} + ({_f(ry)}) sin(t)",
            "",
        ])

    for i, ellipse in enumerate(model.ellipses, 1):
        center = transform.point(ellipse.center)
        rx, ry = ellipse.radii
        theta = math.radians(ellipse.angle_deg)
        x_cos = transform.scale_x(rx * math.cos(theta))
        x_sin = transform.scale_x(-ry * math.sin(theta))
        y_cos = transform.scale_y(rx * math.sin(theta))
        y_sin = transform.scale_y(ry * math.cos(theta))
        lines.extend([
            f"[ellipse_{i}]  0 <= t < 2*pi",
            f"x(t) = {_f(center[0])} + ({_f(x_cos)}) cos(t) + ({_f(x_sin)}) sin(t)",
            f"y(t) = {_f(center[1])} + ({_f(y_cos)}) cos(t) + ({_f(y_sin)}) sin(t)",
            "",
        ])

    for p_index, path in enumerate(model.beziers, 1):
        fill_note = f", fill={path.fill}, use nonzero winding/interior rule" if path.fill != "none" else ""
        lines.append(f"[bezier_path_{p_index}: {path.label}{fill_note}]")
        for s_index, segment in enumerate(path.segments, 1):
            p0, p1, p2, p3 = [transform.point(p) for p in (segment.p0, segment.p1, segment.p2, segment.p3)]
            lines.append(f"segment {s_index}, 0 <= t <= 1")
            lines.append(f"x(t) = {_bezier_component(p0[0], p1[0], p2[0], p3[0])}")
            lines.append(f"y(t) = {_bezier_component(p0[1], p1[1], p2[1], p3[1])}")
        lines.append("")

    for p_index, path in enumerate(model.fourier_paths, 1):
        lines.append(f"[fourier_path_{p_index}: {path.label}]  0 <= t < 1")
        x_terms: list[str] = []
        y_terms: list[str] = []
        # z(t)=sum (a_k+i b_k)(cos wt+i sin wt)
        for c in path.coefficients:
            center = transform.point((c.real, c.imag)) if c.harmonic == 0 else None
            k = c.harmonic
            if k == 0 and center is not None:
                x_terms.append(_f(center[0]))
                y_terms.append(_f(center[1]))
                continue
            # Apply the affine coordinate transform to the pixel-space Fourier terms.
            ax = transform.scale_x(c.real)
            bx = transform.scale_x(c.imag)
            ay = transform.scale_y(c.real)
            by = transform.scale_y(c.imag)
            angle = f"2*pi*({k})*t"
            x_terms.append(f"({_f(ax)})cos({angle})-({_f(bx)})sin({angle})")
            y_terms.append(f"({_f(ay)})sin({angle})+({_f(by)})cos({angle})")
        lines.append("x(t) = " + " + ".join(x_terms))
        lines.append("y(t) = " + " + ".join(y_terms))
        lines.append("")

    if model.dct is not None:
        dct = model.dct
        lines.append("[2D orthonormal DCT image equation]")
        lines.append("For integer pixel coordinates x=0..W-1 and y=0..H-1:")
        lines.append("I_c(x,y) = sum_(u,v) C[c,v,u] alpha(u,W) alpha(v,H)")
        lines.append("             * cos(pi(2x+1)u/(2W)) cos(pi(2y+1)v/(2H))")
        lines.append("alpha(0,N)=1/sqrt(N); alpha(k,N)=sqrt(2/N) for k>0")
        lines.append(f"W={dct.width}, H={dct.height}, channels={dct.channels}")
        lines.append("")
        for c in dct.coefficients:
            lines.append(f"C[{c.channel},{c.v},{c.u}] = {_f(c.value, 10)}")

    return "\n".join(lines)
