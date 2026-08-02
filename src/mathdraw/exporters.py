from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from .document_export import export_equation_documents
from .equations import equations_for_model
from .fourier import evaluate_fourier_path
from .models import DrawingModel
from .renderer import render_model


def _path_d(path) -> str:
    if not path.segments:
        return ""
    first = path.segments[0].p0
    parts = [f"M {first[0]:.4f},{first[1]:.4f}"]
    for s in path.segments:
        parts.append(
            f"C {s.p1[0]:.4f},{s.p1[1]:.4f} {s.p2[0]:.4f},{s.p2[1]:.4f} {s.p3[0]:.4f},{s.p3[1]:.4f}"
        )
    if path.closed:
        parts.append("Z")
    return " ".join(parts)


def model_to_svg(model: DrawingModel) -> str:
    width, height = model.canvas_size
    elements: list[str] = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>']
    if model.dct is not None:
        import base64
        from io import BytesIO
        image = render_model(model)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        elements.append(f'<image href="data:image/png;base64,{encoded}" x="0" y="0" width="{width}" height="{height}"/>')
    for line in model.lines:
        elements.append(f'<line x1="{line.p0[0]}" y1="{line.p0[1]}" x2="{line.p1[0]}" y2="{line.p1[1]}" stroke="black" stroke-width="{line.width}"/>')
    for circle in model.circles:
        elements.append(f'<circle cx="{circle.center[0]}" cy="{circle.center[1]}" r="{circle.radius}" fill="none" stroke="black" stroke-width="{circle.width}"/>')
    for path in model.beziers:
        fill = path.fill if path.fill in {"black", "white"} else "none"
        stroke = "black" if path.width > 0 else "none"
        elements.append(f'<path d="{escape(_path_d(path))}" fill="{fill}" stroke="{stroke}" stroke-width="{path.width}" stroke-linejoin="round" stroke-linecap="round"/>')
    for path in model.fourier_paths:
        points = evaluate_fourier_path(path, 800)
        value = " ".join(f"{x:.3f},{y:.3f}" for x, y in points)
        elements.append(f'<polyline points="{value}" fill="none" stroke="black" stroke-width="{path.width}"/>')
    elements.append("</svg>")
    return "\n".join(elements)


def export_bundle(model: DrawingModel, directory: str | Path, coordinate_mode: str = "normalized_cartesian") -> dict[str, Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": directory / "drawing_model.json",
        "equations": directory / "equations.txt",
        "preview": directory / "reconstruction.png",
        "svg": directory / "reconstruction.svg",
    }
    paths["json"].write_text(json.dumps(model.to_dict(), indent=2), encoding="utf-8")
    paths["equations"].write_text(equations_for_model(model, coordinate_mode), encoding="utf-8")
    render_model(model, scale=2 if model.dct is None else 1).save(paths["preview"])
    paths["svg"].write_text(model_to_svg(model), encoding="utf-8")
    paths.update(export_equation_documents(model, directory, coordinate_mode))
    return paths
