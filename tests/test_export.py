from mathdraw.exporters import export_bundle
from mathdraw.models import DrawingModel, LinePrimitive


def test_export_bundle(tmp_path):
    model = DrawingModel(
        mode="hybrid_vector",
        source_size=(100, 100),
        canvas_size=(100, 100),
        lines=[LinePrimitive((10, 10), (90, 90))],
    )
    paths = export_bundle(model, tmp_path)
    assert all(path.exists() for path in paths.values())
    assert "x(t)" in paths["equations"].read_text(encoding="utf-8")
