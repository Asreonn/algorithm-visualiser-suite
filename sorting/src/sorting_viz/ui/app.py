"""Tkinter-based sorting visualiser showing every algorithm in parallel."""
from __future__ import annotations

import random
import tkinter as tk
from dataclasses import dataclass, field
from time import perf_counter
from tkinter import ttk
from typing import Dict, List, Optional, Sequence, Set

from sorting_viz.core import (
    AlgorithmDefinition,
    Step,
    StepGenerator,
    StepRole,
    StepType,
    algorithm_names,
    get_algorithm,
)
from sorting_viz.config import APP_CONFIG, THEME


def _blank_metrics() -> Dict[str, float]:
    return {
        "steps": 0,
        "comparisons": 0,
        "swaps": 0,
        "writes": 0,
        "duration": 0.0,
    }


@dataclass
class AlgorithmPanel:
    definition: AlgorithmDefinition
    frame: ttk.Frame
    canvas: tk.Canvas
    status_label: ttk.Label
    metrics_label: ttk.Label
    message_label: ttk.Label
    array: List[int] = field(default_factory=list)
    bars: List[int] = field(default_factory=list)
    generator: Optional[StepGenerator] = None
    metrics: Dict[str, float] = field(default_factory=_blank_metrics)
    sorted_indices: Set[int] = field(default_factory=set)
    active_highlights: Set[int] = field(default_factory=set)
    persistent_highlights: Dict[str, Set[int]] = field(default_factory=dict)
    persistent_indices: Set[int] = field(default_factory=set)
    max_value: int = 1
    start_time: float = 0.0
    finished: bool = False
    canvas_width: int = 0
    canvas_height: int = 0


class ScrollableFrame(ttk.Frame):
    """Vertical scroll container for algorithm panels."""

    def __init__(self, parent: tk.Widget, *, style: str) -> None:
        super().__init__(parent)
        self.canvas = tk.Canvas(
            self,
            background=THEME.background,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner = ttk.Frame(self.canvas, style=style)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _on_frame_configure(self, _: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfigure(self.window_id, width=self.canvas.winfo_width())

    def _on_canvas_configure(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _: tk.Event) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.canvas.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def _unbind_mousewheel(self, _: tk.Event) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        num = getattr(event, "num", 0)
        delta = getattr(event, "delta", 0)
        if num == 4 or delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif num == 5 or delta < 0:
            self.canvas.yview_scroll(1, "units")
class SortingVisualizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sorting Algorithm Visualizer")
        self.root.configure(background=THEME.background)
        self.root.minsize(1180, 900)

        self.random = random.Random()
        self.dataset: List[int] = []
        self.panels: List[AlgorithmPanel] = []

        self.is_sorting = False
        self.is_paused = False
        self.after_id: Optional[str] = None

        self.message_var = tk.StringVar(value="Ready.")

        self.scroll_container: Optional[ScrollableFrame] = None
        self.panels_frame: Optional[ttk.Frame] = None
        self._layout_job: Optional[str] = None
        self._configured_columns = 0
        self._configured_rows = 0
        self._current_column_count = 0

        self.root.bind("<Configure>", self._on_root_configure)

        self._build_style()
        self._build_layout()
        self.generate_dataset()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Main.TFrame", background=THEME.background)
        style.configure("Controls.TFrame", background=THEME.background)
        style.configure("Panel.TFrame", background=THEME.surface, relief="flat")
        style.configure("Title.TLabel", background=THEME.surface, foreground=THEME.text_primary, font=("Segoe UI", 12, "bold"))
        style.configure("Status.TLabel", background=THEME.surface, foreground=THEME.text_secondary, font=("Segoe UI", 10))
        style.configure("Meta.TLabel", background=THEME.surface, foreground=THEME.text_secondary, font=("Segoe UI", 9))
        style.configure("Message.TLabel", background=THEME.surface, foreground=THEME.text_primary, font=("Segoe UI", 9))
        style.configure("Legend.TLabel", background=THEME.background, foreground=THEME.text_secondary, font=("Segoe UI", 9))
        style.configure("GlobalMessage.TLabel", background=THEME.background, foreground=THEME.text_secondary, font=("Segoe UI", 10))

        style.configure(
            "Flat.TButton",
            background=THEME.surface_alt,
            foreground=THEME.text_primary,
            padding=(14, 8),
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.map(
            "Flat.TButton",
            background=[("active", THEME.surface_alt), ("pressed", THEME.surface_alt)],
            foreground=[("disabled", THEME.text_secondary)],
        )

        style.configure(
            "Accent.TButton",
            background=THEME.accent,
            foreground=THEME.background,
            padding=(16, 8),
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Accent.TButton",
            background=[("active", THEME.accent), ("pressed", THEME.accent)],
            foreground=[("disabled", THEME.text_secondary)],
        )

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, style="Main.TFrame", padding=(24, 24))
        container.pack(fill="both", expand=True)

        controls = ttk.Frame(container, style="Controls.TFrame")
        controls.pack(fill="x", pady=(0, 16))

        self.generate_button = ttk.Button(controls, text="Generate", style="Flat.TButton", command=self.generate_dataset)
        self.generate_button.pack(side="left", padx=(0, 12))

        self.start_button = ttk.Button(controls, text="Start", style="Accent.TButton", command=self.start_sort)
        self.start_button.pack(side="left", padx=(0, 12))

        self.pause_button = ttk.Button(controls, text="Pause", style="Flat.TButton", command=self.toggle_pause, state="disabled")
        self.pause_button.pack(side="left", padx=(0, 12))

        self.step_button = ttk.Button(controls, text="Step", style="Flat.TButton", command=self.step_once, state="disabled")
        self.step_button.pack(side="left", padx=(0, 12))

        self.stop_button = ttk.Button(controls, text="Stop", style="Flat.TButton", command=self.stop_sort, state="disabled")
        self.stop_button.pack(side="left", padx=(0, 12))

        ttk.Label(controls, textvariable=self.message_var, style="GlobalMessage.TLabel").pack(side="right")

        self._build_legend(container)

        scroll_container = ScrollableFrame(container, style="Main.TFrame")
        scroll_container.pack(fill="both", expand=True)
        self.scroll_container = scroll_container

        panels_frame = scroll_container.inner
        self.panels_frame = panels_frame

        width, height = APP_CONFIG.panel_canvas_size
        for name in algorithm_names():
            definition = get_algorithm(name)
            panel_frame = ttk.Frame(panels_frame, style="Panel.TFrame", padding=16)
            panel_frame.columnconfigure(0, weight=1)
            panel_frame.rowconfigure(1, weight=1)

            header = ttk.Frame(panel_frame, style="Panel.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            ttk.Label(header, text=definition.name, style="Title.TLabel").pack(anchor="w")
            status_label = ttk.Label(header, text="Ready", style="Status.TLabel")
            status_label.pack(anchor="w", pady=(4, 0))

            canvas = tk.Canvas(
                panel_frame,
                width=width,
                height=height,
                background=THEME.canvas_background,
                highlightthickness=0,
                bd=0,
            )
            canvas.grid(row=1, column=0, sticky="nsew", pady=(12, 8))

            metrics_label = ttk.Label(panel_frame, text="0 steps | 0 comparisons | 0 swaps | 0.00 s", style="Meta.TLabel")
            metrics_label.grid(row=2, column=0, sticky="w")

            message_label = ttk.Label(panel_frame, text="Ready.", style="Message.TLabel", wraplength=width, justify="left")
            message_label.grid(row=3, column=0, sticky="w", pady=(8, 0))

            panel = AlgorithmPanel(
                definition=definition,
                frame=panel_frame,
                canvas=canvas,
                status_label=status_label,
                metrics_label=metrics_label,
                message_label=message_label,
                canvas_width=width,
                canvas_height=height,
            )
            self.panels.append(panel)

        self._schedule_layout_update()

    def _build_legend(self, container: ttk.Frame) -> None:
        legend = ttk.Frame(container, style="Controls.TFrame")
        legend.pack(fill="x", pady=(0, 16))

        items = [
            ("Compare", [THEME.compare_primary, THEME.compare_secondary]),
            ("Swap", [THEME.swap_primary, THEME.swap_secondary]),
            ("Write", [THEME.overwrite_primary]),
            ("Pivot", [THEME.pivot]),
            ("Locked", [THEME.sorted]),
        ]
        for text, colors in items:
            item = ttk.Frame(legend, style="Controls.TFrame")
            item.pack(side="left", padx=12)
            for color in colors:
                swatch = tk.Label(item, background=color, width=2, height=1, bd=0)
                swatch.pack(side="left", padx=1)
            ttk.Label(item, text=text, style="Legend.TLabel").pack(side="left", padx=(6, 0))

    # ------------------------------------------------------------------
    # Responsive layout helpers
    # ------------------------------------------------------------------
    def _on_root_configure(self, event: tk.Event) -> None:
        if event.widget is self.root:
            self._schedule_layout_update()

    def _schedule_layout_update(self) -> None:
        if self._layout_job is not None:
            self.root.after_cancel(self._layout_job)
        self._layout_job = self.root.after(120, self._layout_panels)

    def _layout_panels(self) -> None:
        self._layout_job = None
        if not self.panels or not self.panels_frame:
            return

        self.root.update_idletasks()
        available_width = self.panels_frame.winfo_width()
        if available_width <= 0 and self.scroll_container:
            available_width = self.scroll_container.canvas.winfo_width()
        if available_width <= 0:
            available_width = self.root.winfo_width() - 96
        if available_width <= 0:
            return

        gutter = 24
        min_panel_width = 320
        max_columns = min(len(self.panels), 4)
        if max_columns == 0:
            return

        column_count = max_columns
        while column_count > 1:
            required = column_count * min_panel_width + (column_count - 1) * gutter
            if required <= available_width:
                break
            column_count -= 1
        if column_count < 1:
            column_count = 1

        panel_width = (available_width - (column_count - 1) * gutter) / column_count
        panel_width = max(panel_width, min_panel_width)
        canvas_width = int(max(240, panel_width - 32))
        canvas_height = int(max(110, min(canvas_width * 0.45, 220)))
        total_rows = max(1, (len(self.panels) + column_count - 1) // column_count)

        for col in range(self._configured_columns):
            self.panels_frame.columnconfigure(col, weight=0)
        for row in range(self._configured_rows):
            self.panels_frame.rowconfigure(row, weight=0)

        for panel in self.panels:
            panel.frame.grid_forget()

        for col in range(column_count):
            self.panels_frame.columnconfigure(col, weight=1, uniform="panel")
        for row in range(total_rows):
            self.panels_frame.rowconfigure(row, weight=1)

        self._configured_columns = column_count
        self._configured_rows = total_rows
        self._current_column_count = column_count

        for index, panel in enumerate(self.panels):
            row = index // column_count
            column = index % column_count
            panel.frame.grid(row=row, column=column, sticky="nsew", padx=12, pady=12)
            panel.frame.configure(width=int(panel_width))
            panel.canvas_width = canvas_width
            panel.canvas_height = canvas_height
            panel.canvas.configure(width=canvas_width, height=canvas_height)
            self._reposition_panel_bars(panel)
            panel.message_label.configure(wraplength=canvas_width)

        if self.scroll_container:
            region = self.scroll_container.canvas.bbox("all")
            if region:
                self.scroll_container.canvas.configure(scrollregion=region)

    def _reposition_panel_bars(self, panel: AlgorithmPanel) -> None:
        count = len(panel.array)
        if count == 0 or not panel.bars:
            return

        width = panel.canvas_width or APP_CONFIG.panel_canvas_size[0]
        height = panel.canvas_height or APP_CONFIG.panel_canvas_size[1]
        bar_width = width / count
        padding = max(1.0, bar_width * 0.08)
        effective_height = height - 16

        for index, item in enumerate(panel.bars):
            if index >= count:
                continue
            value = panel.array[index]
            normalized = value / panel.max_value if panel.max_value else 0
            bar_height = normalized * effective_height
            x0 = index * bar_width + padding
            x1 = (index + 1) * bar_width - padding
            y0 = height - bar_height
            y1 = height
            panel.canvas.coords(item, x0, y0, x1, y1)

    # ------------------------------------------------------------------
    # Dataset & control flow
    # ------------------------------------------------------------------
    def generate_dataset(self) -> None:
        was_running = self.is_sorting
        self._stop_tick()
        self.is_sorting = False
        self.is_paused = False
        self._set_controls_idle()

        length = APP_CONFIG.dataset_length
        min_value = APP_CONFIG.dataset_min_value
        max_value = APP_CONFIG.dataset_max_value
        self.dataset = [self.random.randint(min_value, max_value) for _ in range(length)]
        for panel in self.panels:
            self._prepare_panel(panel, self.dataset)
        self._schedule_layout_update()
        self.message_var.set("New dataset ready.")
        if was_running:
            self.pause_button.configure(text="Pause")

    def start_sort(self) -> None:
        if self.is_sorting:
            self.message_var.set("Run already in progress.")
            return
        if not self.dataset:
            self.generate_dataset()
        for panel in self.panels:
            self._prepare_panel(panel, self.dataset)
            panel.generator = panel.definition.generator(panel.array)
            panel.start_time = perf_counter()
            panel.status_label.configure(text="Running…")
        self.is_sorting = True
        self.is_paused = False
        self._set_controls_running()
        self.message_var.set("All algorithms started.")
        self._tick()

    def toggle_pause(self) -> None:
        if not self.is_sorting:
            return
        if self.is_paused:
            self.is_paused = False
            self.pause_button.configure(text="Pause")
            self.step_button.configure(state="disabled")
            for panel in self._active_panels():
                panel.status_label.configure(text="Running…")
            self.message_var.set("Sorting resumed.")
            self._schedule_tick()
        else:
            self.is_paused = True
            self._stop_tick()
            self.pause_button.configure(text="Resume")
            self.step_button.configure(state="normal")
            for panel in self._active_panels():
                panel.status_label.configure(text="Paused")
            self.message_var.set("Paused.")

    def step_once(self) -> None:
        if not (self.is_sorting and self.is_paused):
            return
        self._tick(force=True)

    def stop_sort(self) -> None:
        self._stop_tick()
        if not self.dataset:
            self.message_var.set("Generate a dataset first.")
            return
        for panel in self.panels:
            self._prepare_panel(panel, self.dataset)
            panel.status_label.configure(text="Ready")
        self.is_sorting = False
        self.is_paused = False
        self.pause_button.configure(text="Pause")
        self.step_button.configure(state="disabled")
        self._set_controls_idle()
        self.message_var.set("Stopped.")

    # ------------------------------------------------------------------
    # Sorting tick loop
    # ------------------------------------------------------------------
    def _active_panels(self) -> List[AlgorithmPanel]:
        return [panel for panel in self.panels if panel.generator is not None and not panel.finished]

    def _tick(self, *, force: bool = False) -> None:
        if not self.is_sorting:
            return
        if self.is_paused and not force:
            return

        active_found = False
        for panel in self.panels:
            if panel.generator is None or panel.finished:
                continue
            active_found = True
            try:
                step = next(panel.generator)
            except StopIteration:
                self._complete_panel(panel)
                continue
            self._apply_step(panel, step)
        if not active_found:
            self._finish_sort()
            return
        if not force:
            self._schedule_tick()

    def _schedule_tick(self) -> None:
        delay_ms = max(1, int(1000 / max(APP_CONFIG.steps_per_second, 1)))
        self.after_id = self.root.after(delay_ms, self._tick)

    def _stop_tick(self) -> None:
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _complete_panel(self, panel: AlgorithmPanel) -> None:
        panel.finished = True
        panel.generator = None
        panel.metrics["duration"] = perf_counter() - panel.start_time
        panel.sorted_indices = set(range(len(panel.array)))
        self._draw_panel_bars(panel, final_pass=True)
        panel.status_label.configure(text="Completed")
        self._update_panel_metrics_label(panel)
        panel.message_label.configure(text="Sorting completed.")

    def _finish_sort(self) -> None:
        self._stop_tick()
        for panel in self.panels:
            if not panel.finished:
                self._complete_panel(panel)
        self.is_sorting = False
        self.is_paused = False
        self._set_controls_idle()
        self.pause_button.configure(text="Pause")
        self.step_button.configure(state="disabled")
        self.message_var.set("All algorithms completed.")

    # ------------------------------------------------------------------
    # Panel helpers
    # ------------------------------------------------------------------
    def _prepare_panel(self, panel: AlgorithmPanel, source: Sequence[int]) -> None:
        panel.array = list(source)
        panel.max_value = max(1, max(panel.array, default=1))
        panel.metrics = _blank_metrics()
        panel.sorted_indices.clear()
        panel.active_highlights.clear()
        panel.persistent_highlights.clear()
        panel.persistent_indices.clear()
        panel.bars.clear()
        panel.generator = None
        panel.start_time = 0.0
        panel.finished = False
        self._draw_panel_bars(panel)
        panel.status_label.configure(text="Ready")
        self._update_panel_metrics_label(panel)
        panel.message_label.configure(text="Ready.")

    def _draw_panel_bars(self, panel: AlgorithmPanel, final_pass: bool = False) -> None:
        canvas = panel.canvas
        canvas.delete("all")
        count = len(panel.array)
        if count == 0:
            return
        width = panel.canvas_width or APP_CONFIG.panel_canvas_size[0]
        height = panel.canvas_height or APP_CONFIG.panel_canvas_size[1]
        canvas.configure(width=width, height=height)
        bar_width = width / count
        padding = max(1.0, bar_width * 0.08)
        effective_height = height - 16
        panel.bars = []
        for index, value in enumerate(panel.array):
            x0 = index * bar_width + padding
            x1 = (index + 1) * bar_width - padding
            bar_height = (value / panel.max_value) * effective_height
            y0 = height - bar_height
            y1 = height
            color = self._base_bar_color(panel, index, final_pass)
            item = canvas.create_rectangle(x0, y0, x1, y1, fill=color, width=0)
            panel.bars.append(item)

    def _base_bar_color(self, panel: AlgorithmPanel, index: int, final_pass: bool = False) -> str:
        if final_pass or index in panel.sorted_indices:
            return THEME.sorted
        if index in panel.persistent_indices:
            return THEME.pivot
        return THEME.bar_dim

    def _update_bar(self, panel: AlgorithmPanel, index: int, value: Optional[int] = None, color: Optional[str] = None) -> None:
        width = panel.canvas_width or APP_CONFIG.panel_canvas_size[0]
        height = panel.canvas_height or APP_CONFIG.panel_canvas_size[1]
        canvas = panel.canvas
        count = len(panel.array)
        if count == 0:
            return
        bar_width = width / count
        padding = max(1.0, bar_width * 0.08)
        effective_height = height - 16
        if value is not None:
            panel.array[index] = value
        value_to_draw = panel.array[index]
        bar_height = (value_to_draw / panel.max_value) * effective_height
        y0 = height - bar_height
        y1 = height
        x0 = index * bar_width + padding
        x1 = (index + 1) * bar_width - padding
        try:
            item = panel.bars[index]
        except IndexError:
            item = canvas.create_rectangle(x0, y0, x1, y1, fill=color or THEME.bar_dim, width=0)
            if index >= len(panel.bars):
                panel.bars.append(item)
            else:
                panel.bars[index] = item
            return
        canvas.coords(item, x0, y0, x1, y1)
        if color:
            canvas.itemconfigure(item, fill=color)

    def _apply_step(self, panel: AlgorithmPanel, step: Step) -> None:
        self._clear_active_highlights(panel)
        panel.metrics["steps"] += 1
        color_map = self._color_map_for_step(step)

        if step.action == StepType.COMPARE:
            panel.metrics["comparisons"] += 1
            self._apply_color_map(panel, step, color_map)
            self._register_active_highlights(panel, color_map.keys())
        elif step.action == StepType.SWAP:
            panel.metrics["swaps"] += 1
            panel.metrics["writes"] += len(step.indices)
            for idx, value in zip(step.indices, step.values):
                color = color_map.get(idx, THEME.swap_primary)
                self._update_bar(panel, idx, value, color)
            self._register_active_highlights(panel, color_map.keys())
        elif step.action == StepType.OVERWRITE:
            panel.metrics["writes"] += len(step.indices)
            for idx, value in zip(step.indices, step.values):
                color = color_map.get(idx, THEME.overwrite_primary)
                self._update_bar(panel, idx, value, color)
            self._register_active_highlights(panel, color_map.keys())
        elif step.action == StepType.HIGHLIGHT:
            if step.label and step.label in APP_CONFIG.persistent_highlight_labels:
                self._set_persistent_highlight(panel, step.label, step.indices)
            else:
                self._apply_color_map(panel, step, color_map)
                self._register_active_highlights(panel, color_map.keys())
        elif step.action == StepType.MARK_RANGE:
            self._apply_color_map(panel, step, color_map)
            self._register_active_highlights(panel, color_map.keys())
        elif step.action == StepType.MARK_FINAL:
            for idx in step.indices:
                panel.sorted_indices.add(idx)
                self._remove_persistent_index(panel, idx)
                self._update_bar(panel, idx, None, THEME.sorted)
        panel.metrics["duration"] = perf_counter() - panel.start_time
        self._update_panel_metrics_label(panel)
        panel.message_label.configure(text=self._step_message(step))

    def _color_map_for_step(self, step: Step) -> Dict[int, str]:
        if step.action == StepType.HIGHLIGHT and step.label and step.label in APP_CONFIG.persistent_highlight_labels:
            return {}
        mapping: Dict[int, str] = {}
        role_map = step.role_map()
        for index, role in role_map.items():
            mapping[index] = self._role_color(step.action, role)
        if not mapping:
            default_color = self._role_color(step.action, StepRole.PRIMARY)
            for index in step.indices:
                mapping[index] = default_color
        return mapping

    def _role_color(self, action: StepType, role: StepRole) -> str:
        if action == StepType.COMPARE:
            if role == StepRole.SECONDARY:
                return THEME.compare_secondary
            if role == StepRole.AUXILIARY:
                return THEME.compare_aux
            return THEME.compare_primary
        if action == StepType.SWAP:
            return THEME.swap_secondary if role == StepRole.SECONDARY else THEME.swap_primary
        if action == StepType.OVERWRITE:
            return THEME.overwrite_secondary if role == StepRole.AUXILIARY else THEME.overwrite_primary
        if action == StepType.MARK_RANGE:
            return THEME.range_end if role == StepRole.RANGE_END else THEME.range_start
        if action == StepType.HIGHLIGHT:
            if role == StepRole.SECONDARY:
                return THEME.compare_secondary
            if role == StepRole.AUXILIARY:
                return THEME.compare_aux
            return THEME.highlight
        return THEME.bar

    def _apply_color_map(self, panel: AlgorithmPanel, step: Step, color_map: Dict[int, str]) -> None:
        for index, color in color_map.items():
            if index in panel.sorted_indices:
                continue
            if index in panel.persistent_indices and step.action != StepType.HIGHLIGHT:
                continue
            self._update_bar(panel, index, None, color)

    def _register_active_highlights(self, panel: AlgorithmPanel, indices: Sequence[int]) -> None:
        for index in indices:
            if index in panel.sorted_indices or index in panel.persistent_indices:
                continue
            panel.active_highlights.add(index)

    def _clear_active_highlights(self, panel: AlgorithmPanel) -> None:
        if not panel.active_highlights:
            return
        for index in list(panel.active_highlights):
            if index in panel.sorted_indices or index in panel.persistent_indices:
                continue
            self._update_bar(panel, index, None, THEME.bar_dim)
        panel.active_highlights.clear()

    def _set_persistent_highlight(self, panel: AlgorithmPanel, label: str, indices: Sequence[int]) -> None:
        existing = panel.persistent_highlights.pop(label, set())
        for index in existing:
            if index in panel.sorted_indices:
                continue
            self._update_bar(panel, index, None, THEME.bar_dim)
            panel.persistent_indices.discard(index)
        new_indices = set(indices)
        panel.persistent_highlights[label] = new_indices
        for index in new_indices:
            if index in panel.sorted_indices:
                continue
            panel.persistent_indices.add(index)
            self._update_bar(panel, index, None, THEME.pivot)

    def _remove_persistent_index(self, panel: AlgorithmPanel, index: int) -> None:
        for label, indices in list(panel.persistent_highlights.items()):
            if index in indices:
                indices.discard(index)
                panel.persistent_indices.discard(index)
            if not indices:
                panel.persistent_highlights.pop(label, None)

    def _update_panel_metrics_label(self, panel: AlgorithmPanel) -> None:
        panel.metrics_label.configure(
            text=(
                f"{panel.metrics['steps']} steps | "
                f"{panel.metrics['comparisons']} comparisons | "
                f"{panel.metrics['swaps']} swaps | "
                f"{panel.metrics['duration']:.2f} s"
            )
        )

    def _step_message(self, step: Step) -> str:
        if step.message:
            return step.message
        fallback = {
            StepType.COMPARE: "Comparing elements.",
            StepType.SWAP: "Swapping elements.",
            StepType.OVERWRITE: "Writing new value.",
            StepType.HIGHLIGHT: "Highlighting pivots.",
            StepType.MARK_RANGE: "Processing subrange.",
            StepType.MARK_FINAL: "Element locked in place.",
        }
        return fallback.get(step.action, "Step executed.")

    # ------------------------------------------------------------------
    # Control state helpers
    # ------------------------------------------------------------------
    def _set_controls_idle(self) -> None:
        self.generate_button.configure(state="normal")
        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled", text="Pause")
        self.step_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")

    def _set_controls_running(self) -> None:
        self.generate_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal", text="Pause")
        self.step_button.configure(state="disabled")
        self.stop_button.configure(state="normal")


def launch() -> None:
    root = tk.Tk()
    SortingVisualizerApp(root)
    root.mainloop()


__all__ = ["SortingVisualizerApp", "launch"]
