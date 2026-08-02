from __future__ import annotations

from zipfile import ZipFile

from mathdraw.document_export import export_equation_documents, markdown_report_for_model
from mathdraw.models import DrawingModel, LinePrimitive


def test_document_sources_include_complete_equation(tmp_path):
    model = DrawingModel(
        mode="hybrid_vector",
        source_size=(100, 100),
        canvas_size=(100, 100),
        lines=[LinePrimitive((10, 10), (90, 90))],
    )
    report = markdown_report_for_model(model)
    assert "Line 1: x-coordinate" in report
    assert "x_{1}(t)" in report
    paths = export_equation_documents(model, tmp_path)
    assert paths["equations_markdown"].exists()
    assert paths["equations_latex"].exists()
    if "equations_docx" in paths:
        with ZipFile(paths["equations_docx"]) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
        assert "<m:oMath" in xml
