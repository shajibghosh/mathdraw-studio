from __future__ import annotations

import json
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from ..contour import ContourConfig
from ..dct_image import DCTConfig
from ..equations import equations_for_model
from ..exporters import export_bundle
from ..fourier import FourierConfig
from ..io import load_image, resize_to_limit
from ..metrics import compare_images
from ..pipeline import PipelineConfig, process_image
from ..preprocess import PreprocessConfig
from ..primitive import PrimitiveConfig
from ..renderer import render_model


MODE_LABELS = {
    "Automatic": "auto",
    "Hybrid vector (lines, circles, Bézier)": "hybrid_vector",
    "Fourier contour equations": "fourier_contour",
    "2D cosine-series image": "dct_image",
}
COORDINATE_LABELS = {
    "Centered Cartesian [-1, 1]": "normalized_cartesian",
    "Normalized Cartesian [0, 1]": "normalized_0_1",
    "Pixel coordinates (top-left origin)": "pixel_top_left",
}


class MathDrawApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MathDraw Studio — Image to Mathematical Equations")
        self.geometry("1500x920")
        self.minsize(1050, 700)

        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mathdraw")
        self.source_path: Path | None = None
        self.source_image: Image.Image | None = None
        self.model = None
        self.reconstruction: Image.Image | None = None
        self.full_equations = ""
        self._source_photo = None
        self._result_photo = None

        self._build_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Heading.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=8)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=(12, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="MathDraw Studio", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(
            header,
            text="Convert line art, objects, animals, patterns, food, and photographs into finite mathematical representations.",
        ).pack(side=tk.LEFT, padx=18)

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        controls = ttk.Frame(main, padding=10, width=300)
        workspace = ttk.Panedwindow(main, orient=tk.VERTICAL)
        main.add(controls, weight=0)
        main.add(workspace, weight=1)

        self._build_controls(controls)
        self._build_workspace(workspace)

        status_frame = ttk.Frame(self, padding=(10, 5))
        status_frame.pack(fill=tk.X)
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=180)
        self.progress.pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Open an image to begin.")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=10)

    def _build_controls(self, parent: ttk.Frame) -> None:
        ttk.Button(parent, text="Open image…", command=self.open_image, style="Accent.TButton").pack(fill=tk.X)
        ttk.Button(parent, text="Process image", command=self.process, style="Accent.TButton").pack(fill=tk.X, pady=(8, 0))
        ttk.Button(parent, text="Export equations (TXT, DOCX, PDF)…", command=self.export, style="Accent.TButton").pack(fill=tk.X, pady=(8, 16))

        settings = ttk.LabelFrame(parent, text="Representation", padding=10)
        settings.pack(fill=tk.X)

        self.mode_var = tk.StringVar(value="Automatic")
        ttk.Label(settings, text="Mode").pack(anchor=tk.W)
        ttk.Combobox(settings, textvariable=self.mode_var, values=list(MODE_LABELS), state="readonly", width=32).pack(fill=tk.X, pady=(2, 8))

        self.coord_var = tk.StringVar(value="Centered Cartesian [-1, 1]")
        ttk.Label(settings, text="Equation coordinates").pack(anchor=tk.W)
        coord = ttk.Combobox(settings, textvariable=self.coord_var, values=list(COORDINATE_LABELS), state="readonly", width=32)
        coord.pack(fill=tk.X, pady=(2, 8))
        coord.bind("<<ComboboxSelected>>", lambda _event: self.refresh_equations())

        self.max_side_var = tk.IntVar(value=1000)
        self._spin(settings, "Vector processing max side", self.max_side_var, 200, 2400, 50)

        edge_box = ttk.LabelFrame(parent, text="Vector and contour settings", padding=10)
        edge_box.pack(fill=tk.X, pady=(12, 0))
        self.canny_low_var = tk.IntVar(value=40)
        self.canny_high_var = tk.IntVar(value=130)
        self.max_contours_var = tk.IntVar(value=220)
        self.samples_var = tk.IntVar(value=80)
        self.harmonics_var = tk.IntVar(value=18)
        self.detect_lines_var = tk.BooleanVar(value=True)
        self.detect_circles_var = tk.BooleanVar(value=False)
        self._spin(edge_box, "Canny low", self.canny_low_var, 0, 255, 5)
        self._spin(edge_box, "Canny high", self.canny_high_var, 1, 255, 5)
        self._spin(edge_box, "Maximum contours", self.max_contours_var, 1, 1000, 10)
        self._spin(edge_box, "Max Bézier vertices/region", self.samples_var, 8, 400, 8)
        self._spin(edge_box, "Fourier harmonics", self.harmonics_var, 2, 100, 1)
        ttk.Checkbutton(edge_box, text="Detect straight lines", variable=self.detect_lines_var).pack(anchor=tk.W, pady=(4, 0))
        ttk.Checkbutton(edge_box, text="Detect circles", variable=self.detect_circles_var).pack(anchor=tk.W)

        dct_box = ttk.LabelFrame(parent, text="Photo / texture settings", padding=10)
        dct_box.pack(fill=tk.X, pady=(12, 0))
        self.dct_width_var = tk.IntVar(value=128)
        self.dct_height_var = tk.IntVar(value=128)
        self.dct_coeff_var = tk.IntVar(value=2400)
        self.dct_gray_var = tk.BooleanVar(value=False)
        self.dct_exact_var = tk.BooleanVar(value=False)
        self._spin(dct_box, "Equation image width", self.dct_width_var, 16, 4096, 8)
        self._spin(dct_box, "Equation image height", self.dct_height_var, 16, 4096, 8)
        self._spin(dct_box, "Retained DCT coefficients", self.dct_coeff_var, 16, 200000, 100)
        ttk.Checkbutton(dct_box, text="Grayscale equation", variable=self.dct_gray_var).pack(anchor=tk.W, pady=(4, 0))
        ttk.Checkbutton(
            dct_box,
            text="Retain every DCT coefficient (exact at selected resolution)",
            variable=self.dct_exact_var,
        ).pack(anchor=tk.W, pady=(4, 0))

        note = (
            "Tip: use Hybrid Vector for drawings like the supplied cat example. "
            "Use Fourier Contours for smooth silhouettes and DCT for photographs or dense textures."
        )
        ttk.Label(parent, text=note, wraplength=285, justify=tk.LEFT).pack(fill=tk.X, pady=14)

    @staticmethod
    def _spin(parent: ttk.Frame, label: str, variable: tk.Variable, minimum: int, maximum: int, increment: int) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label).pack(side=tk.LEFT)
        ttk.Spinbox(row, textvariable=variable, from_=minimum, to=maximum, increment=increment, width=9).pack(side=tk.RIGHT)

    def _build_workspace(self, parent: ttk.Panedwindow) -> None:
        previews = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        tabs = ttk.Notebook(parent)
        parent.add(previews, weight=3)
        parent.add(tabs, weight=2)

        source_frame = ttk.LabelFrame(previews, text="Input image", padding=6)
        result_frame = ttk.LabelFrame(previews, text="Mathematical reconstruction", padding=6)
        previews.add(source_frame, weight=1)
        previews.add(result_frame, weight=1)
        self.source_label = ttk.Label(source_frame, anchor=tk.CENTER, text="No image loaded")
        self.result_label = ttk.Label(result_frame, anchor=tk.CENTER, text="Process an image to preview the reconstruction")
        self.source_label.pack(fill=tk.BOTH, expand=True)
        self.result_label.pack(fill=tk.BOTH, expand=True)
        source_frame.bind("<Configure>", lambda _e: self._update_previews())
        result_frame.bind("<Configure>", lambda _e: self._update_previews())

        eq_frame = ttk.Frame(tabs, padding=6)
        diag_frame = ttk.Frame(tabs, padding=6)
        tabs.add(eq_frame, text="Equations")
        tabs.add(diag_frame, text="Diagnostics")

        eq_scroll = ttk.Scrollbar(eq_frame)
        eq_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.equation_text = tk.Text(eq_frame, wrap=tk.NONE, font=("Consolas", 10), yscrollcommand=eq_scroll.set)
        self.equation_text.pack(fill=tk.BOTH, expand=True)
        eq_scroll.config(command=self.equation_text.yview)

        diag_scroll = ttk.Scrollbar(diag_frame)
        diag_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.diagnostic_text = tk.Text(diag_frame, wrap=tk.WORD, font=("Consolas", 10), yscrollcommand=diag_scroll.set)
        self.diagnostic_text.pack(fill=tk.BOTH, expand=True)
        diag_scroll.config(command=self.diagnostic_text.yview)

    def open_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Open image",
            filetypes=[
                ("Supported images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp *.gif *.ico *.heic *.heif *.avif *.svg *.pdf *.dng *.cr2 *.nef *.arw"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            image = load_image(path)
        except Exception as exc:
            messagebox.showerror("Could not open image", str(exc))
            return
        self.source_path = Path(path)
        self.source_image = image
        self.model = None
        self.reconstruction = None
        self.full_equations = ""
        self.equation_text.delete("1.0", tk.END)
        self.diagnostic_text.delete("1.0", tk.END)
        self.status_var.set(f"Loaded {self.source_path.name}: {image.width} × {image.height} pixels.")
        self._update_previews()

    def _config(self) -> PipelineConfig:
        return PipelineConfig(
            mode=MODE_LABELS[self.mode_var.get()],
            preprocess=PreprocessConfig(
                canny_low=int(self.canny_low_var.get()),
                canny_high=int(self.canny_high_var.get()),
                blur_sigma=1.0,
                use_threshold_edges=True,
                close_gaps=True,
            ),
            contour=ContourConfig(
                max_contours=int(self.max_contours_var.get()),
                samples_per_contour=int(self.samples_var.get()),
                smoothing_passes=1,
            ),
            primitives=PrimitiveConfig(
                detect_lines=bool(self.detect_lines_var.get()),
                detect_circles=bool(self.detect_circles_var.get()),
            ),
            fourier=FourierConfig(
                max_contours=int(self.max_contours_var.get()),
                harmonics=int(self.harmonics_var.get()),
            ),
            dct=DCTConfig(
                max_width=int(self.dct_width_var.get()),
                max_height=int(self.dct_height_var.get()),
                coefficient_count=int(self.dct_coeff_var.get()),
                grayscale=bool(self.dct_gray_var.get()),
                exact=bool(self.dct_exact_var.get()),
            ),
        )

    def process(self) -> None:
        if self.source_image is None:
            messagebox.showinfo("No image", "Open an image first.")
            return
        config = self._config()
        if config.mode == "dct_image" and config.dct.exact:
            source_w, source_h = self.source_image.size
            ratio = min(config.dct.max_width / source_w, config.dct.max_height / source_h, 1.0)
            represented_w = max(1, int(round(source_w * ratio)))
            represented_h = max(1, int(round(source_h * ratio)))
            channels = 1 if config.dct.grayscale else 3
            estimated = represented_w * represented_h * channels
            if estimated > 100_000:
                proceed = messagebox.askyesno(
                    "Very large exact equation",
                    f"Exact DCT at approximately {represented_w} × {represented_h} will create "
                    f"{estimated:,} coefficients. Processing and document export may require substantial memory, "
                    "time, and disk space. Continue?",
                )
                if not proceed:
                    return
        self.progress.start(12)
        self.status_var.set("Generating mathematical representation…")
        source = self.source_image.copy()
        if config.mode != "dct_image":
            source = resize_to_limit(source, int(self.max_side_var.get()))
        future = self.executor.submit(self._process_worker, source, config)
        future.add_done_callback(lambda f: self.after(0, self._process_complete, f))

    @staticmethod
    def _process_worker(source: Image.Image, config: PipelineConfig):
        model = process_image(source, config)
        reconstruction = render_model(model, scale=1)
        equations = equations_for_model(model, "normalized_cartesian")
        metrics = compare_images(source, reconstruction)
        return model, reconstruction, equations, metrics

    def _process_complete(self, future) -> None:
        self.progress.stop()
        try:
            self.model, self.reconstruction, self.full_equations, metrics = future.result()
        except Exception as exc:
            self.status_var.set("Processing failed.")
            messagebox.showerror("Processing failed", f"{exc}\n\n{traceback.format_exc()}")
            return
        self.refresh_equations()
        diagnostics = {"model": self.model.metadata, "image_similarity": metrics}
        self.diagnostic_text.delete("1.0", tk.END)
        self.diagnostic_text.insert("1.0", json.dumps(diagnostics, indent=2))
        count = (
            len(self.model.lines)
            + len(self.model.circles)
            + len(self.model.beziers)
            + len(self.model.fourier_paths)
            + (len(self.model.dct.coefficients) if self.model.dct else 0)
        )
        self.status_var.set(f"Done. Mode: {self.model.mode}; equation components: {count:,}.")
        self._update_previews()

    def refresh_equations(self) -> None:
        if self.model is None:
            return
        self.full_equations = equations_for_model(self.model, COORDINATE_LABELS[self.coord_var.get()])
        preview_limit = 400_000
        visible = self.full_equations
        if len(visible) > preview_limit:
            visible = visible[:preview_limit] + "\n\n[GUI preview truncated. Export writes the complete equation file.]"
        self.equation_text.delete("1.0", tk.END)
        self.equation_text.insert("1.0", visible)

    def export(self) -> None:
        if self.model is None:
            messagebox.showinfo("Nothing to export", "Process an image first.")
            return
        directory = filedialog.askdirectory(title="Select output directory")
        if not directory:
            return
        if self.model.dct is not None and bool(self.dct_exact_var.get()):
            full_count = self.model.dct.width * self.model.dct.height * self.model.dct.channels
            if full_count > 100_000:
                proceed = messagebox.askyesno(
                    "Large equation document",
                    f"This exact raster representation contains {full_count:,} coefficients. "
                    "The Word/PDF reports may contain thousands of pages and take a long time to create. Continue?",
                )
                if not proceed:
                    return
        try:
            paths = export_bundle(self.model, directory, COORDINATE_LABELS[self.coord_var.get()])
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Exported {len(paths)} files to {directory}")
        messagebox.showinfo("Export complete", "Created:\n" + "\n".join(str(p) for p in paths.values()))

    @staticmethod
    def _fit_photo(image: Image.Image, width: int, height: int):
        if width < 50 or height < 50:
            return None
        display = image.copy()
        display.thumbnail((max(50, width - 12), max(50, height - 12)), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(display)

    def _update_previews(self) -> None:
        if self.source_image is not None:
            self._source_photo = self._fit_photo(self.source_image, self.source_label.winfo_width(), self.source_label.winfo_height())
            if self._source_photo:
                self.source_label.configure(image=self._source_photo, text="")
        if self.reconstruction is not None:
            self._result_photo = self._fit_photo(self.reconstruction, self.result_label.winfo_width(), self.result_label.winfo_height())
            if self._result_photo:
                self.result_label.configure(image=self._result_photo, text="")

    def _on_close(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()


def run() -> None:
    app = MathDrawApp()
    app.mainloop()
