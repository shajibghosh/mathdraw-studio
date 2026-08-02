from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .geometry import CoordinateTransform
from .models import DrawingModel


@dataclass(slots=True)
class EquationEntry:
    title: str
    latex: str
    note: str = ""


@dataclass(slots=True)
class EquationSection:
    title: str
    entries: list[EquationEntry] = field(default_factory=list)
    introduction: str = ""


def _f(value: float, precision: int = 8) -> str:
    if abs(value) < 0.5 * 10 ** (-precision):
        value = 0.0
    return f"{value:.{precision}f}".rstrip("0").rstrip(".") or "0"


def _latex_number(value: float, precision: int = 8) -> str:
    text = _f(value, precision)
    # Avoid LaTeX interpreting a leading minus as a binary operator in compact products.
    return text


def _latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)


def _bezier_component_latex(a: float, b: float, c: float, d: float) -> str:
    return (
        rf"(1-t)^3\left({_latex_number(a)}\right)"
        rf"+3(1-t)^2t\left({_latex_number(b)}\right)"
        rf"+3(1-t)t^2\left({_latex_number(c)}\right)"
        rf"+t^3\left({_latex_number(d)}\right)"
    )


def _join_signed_terms(terms: Iterable[str]) -> str:
    values = [term for term in terms if term]
    return " + ".join(values).replace("+ -", "- ") if values else "0"


def equation_sections_for_model(
    model: DrawingModel,
    coordinate_mode: str = "normalized_cartesian",
) -> list[EquationSection]:
    width, height = model.canvas_size
    transform = CoordinateTransform(width, height, coordinate_mode)
    sections: list[EquationSection] = []

    if model.lines:
        section = EquationSection(
            "Line equations",
            introduction=(
                "Each detected line is represented parametrically. The parameter interval is included "
                "so that the equation draws only the detected segment rather than an infinite line."
            ),
        )
        for i, line in enumerate(model.lines, 1):
            p0, p1 = transform.point(line.p0), transform.point(line.p1)
            section.entries.extend(
                [
                    EquationEntry(
                        f"Line {i}: x-coordinate",
                        rf"x_{{{i}}}(t)={_latex_number(p0[0])}+\left({_latex_number(p1[0]-p0[0])}\right)t,\qquad 0\le t\le 1",
                    ),
                    EquationEntry(
                        f"Line {i}: y-coordinate",
                        rf"y_{{{i}}}(t)={_latex_number(p0[1])}+\left({_latex_number(p1[1]-p0[1])}\right)t,\qquad 0\le t\le 1",
                    ),
                ]
            )
        sections.append(section)

    if model.circles:
        section = EquationSection("Circle equations")
        for i, circle in enumerate(model.circles, 1):
            center = transform.point(circle.center)
            rx = transform.scale_x(circle.radius)
            ry = transform.scale_y(circle.radius)
            section.entries.extend(
                [
                    EquationEntry(
                        f"Circle {i}: x-coordinate",
                        rf"x_{{{i}}}(t)={_latex_number(center[0])}+\left({_latex_number(rx)}\right)\cos t,\qquad 0\le t<2\pi",
                    ),
                    EquationEntry(
                        f"Circle {i}: y-coordinate",
                        rf"y_{{{i}}}(t)={_latex_number(center[1])}+\left({_latex_number(ry)}\right)\sin t,\qquad 0\le t<2\pi",
                    ),
                ]
            )
        sections.append(section)

    if model.ellipses:
        import math

        section = EquationSection("Ellipse equations")
        for i, ellipse in enumerate(model.ellipses, 1):
            center = transform.point(ellipse.center)
            rx, ry = ellipse.radii
            theta = math.radians(ellipse.angle_deg)
            x_cos = transform.scale_x(rx * math.cos(theta))
            x_sin = transform.scale_x(-ry * math.sin(theta))
            y_cos = transform.scale_y(rx * math.sin(theta))
            y_sin = transform.scale_y(ry * math.cos(theta))
            section.entries.extend(
                [
                    EquationEntry(
                        f"Ellipse {i}: x-coordinate",
                        rf"x_{{{i}}}(t)={_latex_number(center[0])}+\left({_latex_number(x_cos)}\right)\cos t"
                        rf"+\left({_latex_number(x_sin)}\right)\sin t,\qquad 0\le t<2\pi",
                    ),
                    EquationEntry(
                        f"Ellipse {i}: y-coordinate",
                        rf"y_{{{i}}}(t)={_latex_number(center[1])}+\left({_latex_number(y_cos)}\right)\cos t"
                        rf"+\left({_latex_number(y_sin)}\right)\sin t,\qquad 0\le t<2\pi",
                    ),
                ]
            )
        sections.append(section)

    if model.beziers:
        section = EquationSection(
            "Piecewise cubic Bezier equations",
            introduction=(
                "Every irregular contour is a sequence of cubic Bezier segments. Taken together with the "
                "listed parameter domains and fill rule, these equations fully specify the exported vector model."
            ),
        )
        for path_index, path in enumerate(model.beziers, 1):
            fill_note = (
                f"Closed={path.closed}; fill={path.fill}; use the nonzero winding rule."
                if path.fill != "none"
                else f"Closed={path.closed}; unfilled contour."
            )
            for segment_index, segment in enumerate(path.segments, 1):
                p0, p1, p2, p3 = [
                    transform.point(p) for p in (segment.p0, segment.p1, segment.p2, segment.p3)
                ]
                x_component = _bezier_component_latex(p0[0], p1[0], p2[0], p3[0])
                y_component = _bezier_component_latex(p0[1], p1[1], p2[1], p3[1])
                base_title = f"Bezier path {path_index}, segment {segment_index}"
                section.entries.extend(
                    [
                        EquationEntry(
                            f"{base_title}: x-coordinate",
                            rf"x_{{{path_index},{segment_index}}}(t)={x_component},\qquad 0\le t\le 1",
                            fill_note if segment_index == 1 else "",
                        ),
                        EquationEntry(
                            f"{base_title}: y-coordinate",
                            rf"y_{{{path_index},{segment_index}}}(t)={y_component},\qquad 0\le t\le 1",
                        ),
                    ]
                )
        sections.append(section)

    if model.fourier_paths:
        formula_section = EquationSection(
            "Fourier contour equations",
            introduction=(
                "For each contour, the finite complex-series formula and every complex coefficient are included. "
                "The coordinate mapping converts the pixel-space complex contour into the selected report coordinates."
            ),
        )
        scale = max(width, height) / 2.0
        for path_index, path in enumerate(model.fourier_paths, 1):
            formula_section.entries.append(
                EquationEntry(
                    f"Fourier path {path_index}: finite contour series",
                    rf"z_{{{path_index}}}(t)=\sum_{{k\in K_{{{path_index}}}}}c_{{{path_index},k}}e^{{i2\pi kt}},\qquad 0\le t<1",
                    f"Label: {path.label}. Coefficients retained: {len(path.coefficients)}.",
                )
            )
            if coordinate_mode == "pixel_top_left":
                formula_section.entries.extend(
                    [
                        EquationEntry(
                            f"Fourier path {path_index}: x-coordinate mapping",
                            rf"x_{{{path_index}}}(t)=\operatorname{{Re}}\!\left(z_{{{path_index}}}(t)\right)",
                        ),
                        EquationEntry(
                            f"Fourier path {path_index}: y-coordinate mapping",
                            rf"y_{{{path_index}}}(t)=\operatorname{{Im}}\!\left(z_{{{path_index}}}(t)\right)",
                        ),
                    ]
                )
            elif coordinate_mode == "normalized_0_1":
                formula_section.entries.extend(
                    [
                        EquationEntry(
                            f"Fourier path {path_index}: x-coordinate mapping",
                            rf"x_{{{path_index}}}(t)=\frac{{\operatorname{{Re}}\!\left(z_{{{path_index}}}(t)\right)}}{{{max(1, width-1)}}}",
                        ),
                        EquationEntry(
                            f"Fourier path {path_index}: y-coordinate mapping",
                            rf"y_{{{path_index}}}(t)=1-\frac{{\operatorname{{Im}}\!\left(z_{{{path_index}}}(t)\right)}}{{{max(1, height-1)}}}",
                        ),
                    ]
                )
            else:
                formula_section.entries.extend(
                    [
                        EquationEntry(
                            f"Fourier path {path_index}: x-coordinate mapping",
                            rf"x_{{{path_index}}}(t)=\frac{{\operatorname{{Re}}\!\left(z_{{{path_index}}}(t)\right)-{_latex_number(width/2.0)}}}{{{_latex_number(scale)}}}",
                        ),
                        EquationEntry(
                            f"Fourier path {path_index}: y-coordinate mapping",
                            rf"y_{{{path_index}}}(t)=\frac{{{_latex_number(height/2.0)}-\operatorname{{Im}}\!\left(z_{{{path_index}}}(t)\right)}}{{{_latex_number(scale)}}}",
                        ),
                    ]
                )
            for coefficient in path.coefficients:
                k = coefficient.harmonic
                formula_section.entries.append(
                    EquationEntry(
                        f"Path {path_index}, coefficient k={k}",
                        rf"c_{{{path_index},{k}}}={_latex_number(coefficient.real)}"
                        rf"+i\left({_latex_number(coefficient.imag)}\right)",
                    )
                )
        sections.append(formula_section)

    if model.dct is not None:
        dct = model.dct
        full_count = dct.width * dct.height * dct.channels
        retained = len(dct.coefficients)
        exact = retained == full_count
        section = EquationSection(
            "Two-dimensional orthonormal DCT image equation",
            introduction=(
                f"The represented raster has W={dct.width}, H={dct.height}, and {dct.channels} channel(s). "
                f"It retains {retained} of {full_count} coefficients. "
                + (
                    "Because every coefficient is retained, the inverse DCT is exact at this represented resolution, "
                    "apart from floating-point and final integer rounding."
                    if exact
                    else "Because coefficients were truncated, this is a finite approximation rather than an exact raster identity."
                )
            ),
        )
        section.entries.extend(
            [
                EquationEntry(
                    "DCT reconstruction formula",
                    r"I_c(x,y)=\sum_{v=0}^{H-1}\sum_{u=0}^{W-1}C_{c,v,u}\,\alpha(u,W)\alpha(v,H)"
                    r"\cos\!\left(\frac{\pi(2x+1)u}{2W}\right)"
                    r"\cos\!\left(\frac{\pi(2y+1)v}{2H}\right)",
                    r"Integer domains: $0\le x<W$, $0\le y<H$, and $0\le c<C$.",
                ),
                EquationEntry("DCT normalization at zero", r"\alpha(0,N)=\frac{1}{\sqrt{N}}"),
                EquationEntry(
                    "DCT normalization above zero",
                    r"\alpha(k,N)=\sqrt{\frac{2}{N}},\qquad k>0",
                ),
            ]
        )
        for coefficient in dct.coefficients:
            section.entries.append(
                EquationEntry(
                    f"Coefficient c={coefficient.channel}, v={coefficient.v}, u={coefficient.u}",
                    rf"C_{{{coefficient.channel},{coefficient.v},{coefficient.u}}}="
                    rf"{_latex_number(coefficient.value, 12)}",
                )
            )
        sections.append(section)

    return sections


def _exactness_text(model: DrawingModel) -> str:
    if model.dct is not None:
        dct = model.dct
        complete = len(dct.coefficients) == dct.width * dct.height * dct.channels
        if complete:
            return (
                "Exactness: all DCT coefficients are present, so this representation reconstructs the represented "
                "raster resolution exactly up to floating-point and final pixel rounding. If the image was resized before "
                "conversion, it is exact for the resized raster, not for the original larger raster."
            )
        return (
            "Exactness: the DCT coefficient set is truncated. The document contains the complete exported equation, "
            "but that equation is an approximation of the input image. Enable the exact/full-coefficient option to retain "
            "all coefficients at the selected equation resolution."
        )
    if model.mode == "fourier_contour":
        return (
            "Exactness: the document contains the complete finite Fourier equation exported by the program. It is a "
            "harmonic approximation of sampled image contours; increasing the harmonic count improves fidelity."
        )
    return (
        "Exactness: the document contains every line, circle, ellipse, and Bezier segment in the exported vector model. "
        "The model itself is an approximation obtained from image processing unless the source already consists of exactly "
        "those mathematical primitives."
    )


def markdown_report_for_model(
    model: DrawingModel,
    coordinate_mode: str = "normalized_cartesian",
) -> str:
    width, height = model.canvas_size
    lines = [
        "# Complete Mathematical Equation Report",
        "",
        f"**Representation mode:** `{model.mode}`  ",
        f"**Source image size:** {model.source_size[0]} × {model.source_size[1]} pixels  ",
        f"**Equation canvas:** {width} × {height}  ",
        f"**Coordinate system:** `{coordinate_mode}`",
        "",
        _exactness_text(model),
        "",
        "The equations below are not a shortened GUI preview. Every equation component and every retained coefficient in the exported model is included.",
        "",
    ]
    for section in equation_sections_for_model(model, coordinate_mode):
        lines.extend([f"## {section.title}", ""])
        if section.introduction:
            lines.extend([section.introduction, ""])
        for entry in section.entries:
            lines.extend([f"### {entry.title}", ""])
            if entry.note:
                lines.extend([entry.note, ""])
            lines.extend(["$$", entry.latex, "$$", ""])
    return "\n".join(lines)


def latex_report_for_model(
    model: DrawingModel,
    coordinate_mode: str = "normalized_cartesian",
) -> str:
    width, height = model.canvas_size
    body: list[str] = [
        r"\documentclass[10pt]{article}",
        r"\usepackage[margin=0.65in]{geometry}",
        r"\usepackage{amsmath,amssymb}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{lmodern}",
        r"\usepackage{microtype}",
        r"\usepackage{hyperref}",
        r"\allowdisplaybreaks",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\parskip}{5pt}",
        r"\begin{document}",
        r"\begin{center}",
        r"{\LARGE\bfseries Complete Mathematical Equation Report}\par",
        r"\vspace{3pt}",
        r"{\large MathDraw Studio}\par",
        r"\end{center}",
        rf"\textbf{{Representation mode:}} \texttt{{{_latex_escape(model.mode)}}}\\",
        rf"\textbf{{Source image size:}} {model.source_size[0]} $\times$ {model.source_size[1]} pixels\\",
        rf"\textbf{{Equation canvas:}} {width} $\times$ {height}\\",
        rf"\textbf{{Coordinate system:}} \texttt{{{_latex_escape(coordinate_mode)}}}",
        "",
        _latex_escape(_exactness_text(model)),
        "",
        _latex_escape(
            "The equations below are not a shortened GUI preview. Every equation component and every retained coefficient in the exported model is included."
        ),
    ]
    for section in equation_sections_for_model(model, coordinate_mode):
        body.append(rf"\section{{{_latex_escape(section.title)}}}")
        if section.introduction:
            body.append(_latex_escape(section.introduction))
        for entry in section.entries:
            body.append(rf"\subsection*{{{_latex_escape(entry.title)}}}")
            if entry.note:
                body.append(_latex_escape(entry.note))
            body.extend([r"\begin{equation*}", r"\small", entry.latex, r"\end{equation*}"])
    body.append(r"\end{document}")
    return "\n".join(body)


def _run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n{completed.stdout[-6000:]}"
        )


def _find_pandoc() -> str | None:
    command = shutil.which("pandoc")
    if command:
        return command
    try:
        import pypandoc  # type: ignore

        path = pypandoc.get_pandoc_path()
        return path if path and Path(path).exists() else None
    except Exception:
        return None


def export_equation_documents(
    model: DrawingModel,
    directory: str | Path,
    coordinate_mode: str = "normalized_cartesian",
    *,
    require_docx: bool = False,
    require_pdf: bool = False,
) -> dict[str, Path]:
    """Export complete equations as Markdown, LaTeX, editable DOCX, and typeset PDF.

    DOCX generation uses Pandoc, which converts LaTeX math to native Office Math (OMML), so equations
    are editable in Microsoft Word. PDF generation prefers XeLaTeX and falls back to pdfLaTeX.
    Source .md and .tex files are always produced even if document converters are unavailable.
    """

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    markdown_path = directory / "equations_full.md"
    latex_path = directory / "equations_full.tex"
    docx_path = directory / "equations_full.docx"
    pdf_path = directory / "equations_full.pdf"

    markdown_path.write_text(markdown_report_for_model(model, coordinate_mode), encoding="utf-8")
    latex_path.write_text(latex_report_for_model(model, coordinate_mode), encoding="utf-8")
    result: dict[str, Path] = {"equations_markdown": markdown_path, "equations_latex": latex_path}

    pandoc = _find_pandoc()
    if pandoc:
        try:
            _run(
                [
                    pandoc,
                    str(markdown_path.name),
                    "--from=markdown+tex_math_dollars",
                    "--to=docx",
                    "--standalone",
                    f"--output={docx_path.name}",
                ],
                directory,
            )
            result["equations_docx"] = docx_path
        except Exception:
            if require_docx:
                raise
    elif require_docx:
        raise RuntimeError(
            "Pandoc is required for editable Word equations. Install it with `conda install -c conda-forge pandoc` "
            "or `pip install pypandoc-binary`."
        )

    latex_engine = shutil.which("xelatex") or shutil.which("pdflatex") or shutil.which("tectonic")
    if latex_engine:
        try:
            engine_name = Path(latex_engine).name.lower()
            if "tectonic" in engine_name:
                _run([latex_engine, latex_path.name, "--outdir", str(directory)], directory)
            else:
                _run(
                    [latex_engine, "-interaction=nonstopmode", "-halt-on-error", latex_path.name],
                    directory,
                )
            generated = directory / "equations_full.pdf"
            if generated.exists():
                result["equations_pdf"] = generated
            # A second pass resolves PDF metadata/bookmarks consistently for conventional LaTeX engines.
            if generated.exists() and "tectonic" not in engine_name:
                _run(
                    [latex_engine, "-interaction=nonstopmode", "-halt-on-error", latex_path.name],
                    directory,
                )
            for suffix in (".aux", ".log", ".out", ".toc"):
                extra = directory / f"equations_full{suffix}"
                if extra.exists():
                    extra.unlink()
        except Exception:
            if require_pdf:
                raise
    elif require_pdf:
        raise RuntimeError(
            "A LaTeX PDF engine is required. Install Tectonic, MiKTeX, or TeX Live and ensure `tectonic`, "
            "`xelatex`, or `pdflatex` is on PATH."
        )

    return result
