"""Tkinter application for greedy algorithm visualisation."""
from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import ttk
from typing import Dict, List, Optional, Set, Tuple

from greedy_viz.algorithms import (
    graph_algorithms,
    sequence_algorithms,
)
from greedy_viz.config import APP_CONFIG, GRAPH_CONFIG, SEQUENCE_CONFIG, THEME
from greedy_viz.data import (
    GraphGenerationOptions,
    SequenceGenerationOptions,
    build_activity_dataset,
    build_graph,
    build_knapsack_dataset,
)
from greedy_viz.engine import AnimationEngine
from greedy_viz.state import EdgeId, GraphDataset, GraphStep, NodeId, SequenceDataset, SequenceStep


CANVAS_PADDING = 48
NODE_RADIUS = 22
LEGEND_WIDTH = 180
LEGEND_HEIGHT = 120

LEGEND_ITEMS = (
    ("Visited", THEME.node_visited, "Node already explored"),
    ("Frontier", THEME.node_frontier, "Next candidates"),
    ("Active", THEME.edge_candidate, "Node expanded this step"),
    ("Tree Edge", THEME.edge_selected, "Accepted path"),
    ("Queued Edge", THEME.node_frontier, "In priority queue"),
)

SEQUENCE_LEGEND_ITEMS = (
    ("Seçildi", THEME.node_visited),
    ("Kısmi", THEME.edge_selected),
    ("Elendi", THEME.edge_background),
)


@dataclass
class GraphRenderState:
    dataset: GraphDataset
    start: Optional[NodeId]
    goal: Optional[NodeId]
    step: Optional[GraphStep] = None
    compare_edges: Set[EdgeId] = field(default_factory=set)


class GraphCanvasView(tk.Canvas):
    def __init__(self, parent: tk.Widget, *, width: int, height: int) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            background=THEME.canvas_background,
            highlightthickness=0,
            bd=0,
        )
        self.render_state: Optional[GraphRenderState] = None

    def draw(self, state: GraphRenderState) -> None:
        self.render_state = state
        self.delete("all")
        if not state.dataset.nodes:
            return

        positions = state.dataset.positions
        width = int(self["width"])
        height = int(self["height"])

        def project(node: NodeId) -> Tuple[float, float]:
            x, y = positions.get(node, (0.5, 0.5))
            px = CANVAS_PADDING + x * (width - 2 * CANVAS_PADDING)
            py = CANVAS_PADDING + y * (height - 2 * CANVAS_PADDING)
            return px, py

        # Draw base edges
        for node in state.dataset.nodes:
            for neighbour, weight in state.dataset.neighbours(node):
                if node > neighbour:
                    continue
                x1, y1 = project(node)
                x2, y2 = project(neighbour)
                edge = (node, neighbour)
                normalised = tuple(sorted(edge))
                colour = THEME.edge_background
                width_px = 2
                if state.step:
                    if normalised in state.step.selected_edges:
                        colour = THEME.edge_selected
                        width_px = 4
                    elif normalised == state.step.active_edge:
                        colour = THEME.edge_candidate
                        width_px = 3
                    elif normalised in state.step.candidate_edges:
                        colour = THEME.node_frontier
                self.create_line(x1, y1, x2, y2, fill=colour, width=width_px)
                label_x = (x1 + x2) / 2
                label_y = (y1 + y2) / 2
                self.create_text(
                    label_x,
                    label_y,
                    text=f"{weight:.0f}",
                    fill=THEME.text_secondary,
                    font=("Segoe UI", 9),
                )

        if state.compare_edges:
            for a, b in state.compare_edges:
                x1, y1 = project(a)
                x2, y2 = project(b)
                self.create_line(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=THEME.accent,
                    width=3,
                    dash=(6, 3),
                )

        # Draw nodes
        for node in state.dataset.nodes:
            x, y = project(node)
            colour = THEME.node_default
            outline = THEME.edge_background
            if state.step:
                if node == state.step.active_node:
                    outline = THEME.edge_candidate
                if node in state.step.visited_nodes:
                    colour = THEME.node_visited
                elif node in state.step.frontier_nodes:
                    colour = THEME.node_frontier
            if state.start is not None and node == state.start:
                outline = THEME.accent
            if state.goal is not None and node == state.goal:
                outline = THEME.warning
            self.create_oval(
                x - NODE_RADIUS,
                y - NODE_RADIUS,
                x + NODE_RADIUS,
                y + NODE_RADIUS,
                fill=colour,
                outline=outline,
                width=3,
            )
            self.create_text(
                x,
                y,
                text=str(node),
                fill=THEME.text_primary,
                font=("Segoe UI", 11, "bold"),
            )

        self._draw_legend(width, height)

    def _draw_legend(self, width: int, height: int) -> None:
        x0 = width - LEGEND_WIDTH - 16
        y0 = 16
        x1 = x0 + LEGEND_WIDTH
        y1 = y0 + LEGEND_HEIGHT
        self.create_rectangle(x0, y0, x1, y1, fill=THEME.surface_alt, outline=THEME.edge_background, width=2)
        self.create_text(
            x0 + 12,
            y0 + 14,
            text="Legend",
            fill=THEME.text_primary,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        y = y0 + 32
        for label, colour, description in LEGEND_ITEMS:
            if "Edge" in label:
                self.create_line(x0 + 16, y + 4, x0 + 48, y + 4, fill=colour, width=4, dash=(6, 2) if label == "Queued Edge" else None)
            else:
                self.create_oval(
                    x0 + 12,
                    y,
                    x0 + 36,
                    y + 24,
                    fill=colour,
                    outline=THEME.edge_background,
                    width=2,
                )
            self.create_text(
                x0 + 52,
                y + 12,
                text=label,
                fill=THEME.text_primary,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            )
            if description:
                self.create_text(
                    x0 + 52,
                    y + 26,
                    text=description,
                    fill=THEME.text_secondary,
                    font=("Segoe UI", 8),
                    anchor="w",
                )
                y += 28
            else:
                y += 26


class QueueListbox(ttk.Treeview):
    """Readonly table for queue snapshots."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, columns=("priority", "label"), show="headings", height=6)
        self.heading("priority", text="Priority")
        self.heading("label", text="Details")
        self.column("priority", width=100, anchor="center")
        self.column("label", width=220, anchor="w")

    def update_snapshot(self, step: Optional[GraphStep]) -> None:
        for item in self.get_children():
            self.delete(item)
        if not step:
            return
        for entry in step.queue_snapshot:
            self.insert("", "end", values=(f"{entry.sort_key:.2f}", entry.label))


class SequenceCanvasView(tk.Canvas):
    def __init__(self, parent: tk.Widget, *, width: int, height: int) -> None:
        super().__init__(
            parent,
            width=width,
            height=height,
            background=THEME.canvas_background,
            highlightthickness=0,
            bd=0,
        )
        self.dataset: Optional[SequenceDataset] = None
        self.step: Optional[SequenceStep] = None

    def draw(self, dataset: SequenceDataset, step: Optional[SequenceStep]) -> None:
        self.dataset = dataset
        self.step = step
        self.delete("all")
        if not dataset.values:
            return

        width = int(self["width"])
        height = int(self["height"])
        margin = 40
        bar_width = (width - 2 * margin) / max(len(dataset.values), 1)

        for idx, (value, weight) in enumerate(zip(dataset.values, dataset.weights)):
            x0 = margin + idx * bar_width + bar_width * 0.1
            x1 = margin + (idx + 1) * bar_width - bar_width * 0.1
            base_y = height - margin
            bar_height = (value / max(dataset.values)) * (height - 2 * margin)
            y0 = base_y - bar_height
            fill = THEME.node_default
            outline = THEME.edge_background
            text_colour = THEME.text_primary
            if step:
                if idx == step.active_index:
                    outline = THEME.edge_candidate
                if idx in step.chosen_indices:
                    fill = THEME.node_visited
                if idx in step.discarded_indices:
                    fill = THEME.edge_background
                    text_colour = THEME.text_secondary
            self.create_rectangle(x0, y0, x1, base_y, fill=fill, outline=outline, width=3)
            self.create_text((x0 + x1) / 2, base_y + 14, text=f"#{idx}", fill=THEME.text_secondary, font=("Segoe UI", 9))
            self.create_text((x0 + x1) / 2, y0 - 12, text=f"v={value}", fill=text_colour, font=("Segoe UI", 9))
            self.create_text((x0 + x1) / 2, y0 - 26, text=f"w={weight}", fill=text_colour, font=("Segoe UI", 9))
            if step and idx in step.fractions and step.fractions[idx] < 1.0:
                frac_height = bar_height * step.fractions[idx]
                self.create_rectangle(
                    x0,
                    base_y - frac_height,
                    x1,
                    base_y,
                    fill=THEME.edge_selected,
                    outline="",
                )

        if step and step.capacity_remaining is not None:
            self.create_text(
                width / 2,
                margin / 2,
                text=f"Remaining capacity: {step.capacity_remaining:.1f}",
                fill=THEME.text_primary,
                font=("Segoe UI", 11),
            )

        self._draw_progress_bar(width, height, margin, step.progress_value if step else 0.0)
        self._draw_legend(width, margin)

    def _draw_progress_bar(self, width: int, height: int, margin: int, progress: float) -> None:
        track_y0 = height - margin / 2 - 12
        track_y1 = track_y0 + 10
        x0 = margin
        x1 = width - margin
        self.create_rectangle(x0, track_y0, x1, track_y1, fill=THEME.surface_alt, outline=THEME.edge_background, width=1)
        fill_width = x0 + max(0.0, min(progress, 1.0)) * (x1 - x0)
        self.create_rectangle(x0, track_y0, fill_width, track_y1, fill=THEME.accent, outline="")
        self.create_text(
            width / 2,
            track_y1 + 12,
            text=f"İlerleme: {progress * 100:.0f}%",
            fill=THEME.text_secondary,
            font=("Segoe UI", 9),
        )

    def _draw_legend(self, width: int, margin: int) -> None:
        box_x0 = width - margin - 140
        box_y0 = margin
        box_x1 = width - margin
        box_y1 = box_y0 + 110
        self.create_rectangle(box_x0, box_y0, box_x1, box_y1, fill=THEME.surface_alt, outline=THEME.edge_background, width=1)
        self.create_text(box_x0 + 10, box_y0 + 14, text="Legend", fill=THEME.text_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        y = box_y0 + 32
        for label, colour in SEQUENCE_LEGEND_ITEMS:
            self.create_rectangle(box_x0 + 12, y, box_x0 + 32, y + 16, fill=colour, outline=THEME.edge_background)
            self.create_text(box_x0 + 38, y + 8, text=label, fill=THEME.text_primary, font=("Segoe UI", 9), anchor="w")
            y += 22


class GreedyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Greedy Algorithm Visualiser")
        self.root.configure(background=THEME.background)
        self.root.minsize(1280, 900)

        self.rng = random.Random()

        self._build_style()
        self._build_layout()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Main.TFrame", background=THEME.background)
        style.configure("Panel.TFrame", background=THEME.surface, relief="flat")
        style.configure("Controls.TFrame", background=THEME.surface, relief="flat")
        style.configure("Accent.TButton", background=THEME.accent, foreground=THEME.background, padding=(16, 8), font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Accent.TButton", background=[("active", THEME.accent), ("pressed", THEME.accent)])
        style.configure("Flat.TButton", background=THEME.surface_alt, foreground=THEME.text_primary, padding=(14, 8), font=("Segoe UI", 10), relief="flat")
        style.map(
            "Flat.TButton",
            background=[("active", THEME.surface_alt), ("pressed", THEME.surface_alt)],
            foreground=[("disabled", THEME.text_secondary)],
        )
        style.configure("Section.TLabelframe", background=THEME.surface, relief="flat", borderwidth=0)
        style.configure("Section.TLabelframe.Label", background=THEME.surface, foreground=THEME.text_secondary, font=("Segoe UI", 10, "bold"))
        style.configure("Heading.TLabel", background=THEME.surface, foreground=THEME.text_primary, font=("Segoe UI", 12, "bold"))
        style.configure("Body.TLabel", background=THEME.surface, foreground=THEME.text_secondary, font=("Segoe UI", 10))
        style.configure("Surface.TFrame", background=THEME.surface)
        style.configure("Surface.TLabel", background=THEME.surface, foreground=THEME.text_primary)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, style="Main.TFrame", padding=24)
        container.pack(fill="both", expand=True)

        self.tabs = ttk.Notebook(container)
        self.tabs.pack(fill="both", expand=True)

        self.graph_tab = GraphTab(self.tabs, rng=self.rng)
        self.sequence_tab = SequenceTab(self.tabs, rng=self.rng)

        self.tabs.add(self.graph_tab.frame, text="Graph Algorithms")
        self.tabs.add(self.sequence_tab.frame, text="Sequence Problems")


class GraphTab:
    def __init__(self, parent: tk.Widget, *, rng: random.Random) -> None:
        self.rng = rng
        self.frame = ttk.Frame(parent, style="Main.TFrame")

        self.dataset = GraphDataset(nodes=set(), edges={}, positions={})
        self.start_node: Optional[NodeId] = None
        self.goal_node: Optional[NodeId] = None

        self.engine = AnimationEngine()
        self.compare_engine = AnimationEngine()
        self.playing = False
        self.after_id: Optional[str] = None
        self.current_step: Optional[GraphStep] = None
        self.compare_overlay: Set[EdgeId] = set()

        self.compare_enabled = tk.BooleanVar(value=False)
        self.algorithm_var = tk.StringVar()
        self.compare_algorithm_var = tk.StringVar()
        self.graph_kind_var = tk.StringVar(value="random")
        self.node_count_var = tk.IntVar(value=GRAPH_CONFIG.default_node_count)
        self.edit_mode = tk.BooleanVar(value=False)
        self.pending_edit: Optional[NodeId] = None
        self.selected_edge: Optional[EdgeId] = None
        self.edge_weight_var = tk.DoubleVar(value=float(GRAPH_CONFIG.min_weight))
        self.edge_label_var = tk.StringVar(value="Select two nodes to edit an edge.")
        self._suspend_weight_callback = False
        self.hover_node: Optional[NodeId] = None
        self.tutorial_shown = False
        self._has_generated = False

        self.speed_var = tk.DoubleVar(value=1.0)
        self.message_var = tk.StringVar(value="Generate a graph to begin.")
        self._message_flash_id: Optional[str] = None
        self._finish_notified = False

        self._build()
        self.generate_graph()

    def _build(self) -> None:
        layout = ttk.Frame(self.frame, style="Main.TFrame")
        layout.pack(fill="both", expand=True)

        controls = ttk.Frame(layout, style="Controls.TFrame", padding=(20, 20))
        controls.pack(side="left", fill="y", padx=(0, 20))

        ttk.Label(controls, text="Greedy Algorithm", style="Heading.TLabel").pack(anchor="w")
        self.graph_algorithms = graph_algorithms()
        self.algo_label_to_key = {alg.name: alg.key for alg in self.graph_algorithms}
        self.algo_key_to_def = {alg.key: alg for alg in self.graph_algorithms}
        algo_labels = list(self.algo_label_to_key.keys()) or ["(none)"]
        self.algorithm_var.set(algo_labels[0])
        if len(algo_labels) > 1:
            self.compare_algorithm_var.set(algo_labels[1])
        else:
            self.compare_algorithm_var.set(algo_labels[0])

        self.algo_menu = ttk.Combobox(controls, textvariable=self.algorithm_var, values=algo_labels, state="readonly")
        self.algo_menu.pack(fill="x", pady=(6, 12))
        self.algo_menu.bind("<<ComboboxSelected>>", lambda _: self._on_algo_changed())

        ttk.Checkbutton(
            controls,
            text="Enable comparison",
            variable=self.compare_enabled,
            command=self._on_compare_toggled,
            style="Surface.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(controls, text="Comparison Algorithm", style="Body.TLabel").pack(anchor="w")
        self.compare_menu = ttk.Combobox(controls, textvariable=self.compare_algorithm_var, values=algo_labels, state="disabled")
        self.compare_menu.pack(fill="x", pady=(6, 12))

        ttk.Label(controls, text="Graph Type", style="Body.TLabel").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.graph_kind_var,
            values=["random", "grid", "complete"],
            state="readonly",
        ).pack(fill="x", pady=(6, 12))

        ttk.Label(controls, text="Node count", style="Body.TLabel").pack(anchor="w")
        tk.Scale(
            controls,
            from_=GRAPH_CONFIG.min_node_count,
            to=GRAPH_CONFIG.max_node_count,
            orient="horizontal",
            variable=self.node_count_var,
            background=THEME.surface,
            troughcolor=THEME.surface_alt,
            highlightthickness=0,
            fg=THEME.text_primary,
            relief="flat",
        ).pack(fill="x", pady=(6, 12))

        ttk.Checkbutton(
            controls,
            text="Manual edit mode",
            variable=self.edit_mode,
            command=self._on_edit_mode_toggled,
            style="Surface.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        self.edit_frame = ttk.Frame(controls, style="Surface.TFrame")
        self.edit_frame.pack(fill="x", pady=(0, 12))
        self.edit_frame.configure(height=96)
        self.edit_frame.pack_propagate(False)

        self.edge_label_widget = ttk.Label(self.edit_frame, textvariable=self.edge_label_var, style="Body.TLabel", wraplength=220)
        self.edge_label_widget.pack(anchor="w")

        self.edge_weight_scale = tk.Scale(
            self.edit_frame,
            from_=GRAPH_CONFIG.min_weight,
            to=GRAPH_CONFIG.max_weight,
            orient="horizontal",
            resolution=1,
            variable=self.edge_weight_var,
            command=self._on_weight_changed,
            state="disabled",
            background=THEME.surface,
            troughcolor=THEME.surface_alt,
            highlightthickness=0,
        )
        self.edge_weight_scale.pack(fill="x", pady=(6, 0))

        ttk.Button(controls, text="Generate Graph", command=self.generate_graph, style="Flat.TButton").pack(fill="x", pady=(0, 12))
        ttk.Button(controls, text="Start", command=self.start, style="Accent.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Pause / Resume", command=self.toggle_play, style="Flat.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Step", command=self.step_once, style="Flat.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Reset", command=self.reset, style="Flat.TButton").pack(fill="x")

        ttk.Label(controls, text="Playback speed", style="Body.TLabel").pack(anchor="w", pady=(12, 0))
        tk.Scale(
            controls,
            from_=0.2,
            to=3.0,
            resolution=0.1,
            orient="horizontal",
            variable=self.speed_var,
            background=THEME.surface,
            troughcolor=THEME.surface_alt,
            highlightthickness=0,
        ).pack(fill="x")

        self.message_card = tk.Frame(
            controls,
            background=THEME.surface_alt,
            highlightbackground=THEME.edge_background,
            highlightcolor=THEME.edge_background,
            highlightthickness=1,
            bd=0,
            height=96,
        )
        self.message_card.pack(fill="x", pady=(12, 0))
        self.message_card.pack_propagate(False)
        self.message_label = tk.Label(
            self.message_card,
            textvariable=self.message_var,
            wraplength=220,
            justify="left",
            background=THEME.surface_alt,
            fg=THEME.text_primary,
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
            anchor="w",
        )
        self.message_label.pack(fill="x")
        self.message_var.trace_add("write", lambda *_: self._flash_message())

        canvas_panel = ttk.Frame(layout, style="Surface.TFrame", padding=16)
        canvas_panel.pack(side="left", fill="both", expand=True)

        self.canvas = GraphCanvasView(canvas_panel, width=APP_CONFIG.canvas_size[0], height=APP_CONFIG.canvas_size[1])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)
        self.canvas.bind("<Leave>", lambda _: self._clear_hover())

        self.queue_view = QueueListbox(canvas_panel)
        self.queue_view.pack(fill="x", pady=(16, 0))

        explanation_panel = ttk.Frame(layout, style="Surface.TFrame", padding=16)
        explanation_panel.pack(side="left", fill="y")

        ttk.Label(explanation_panel, text="Explanation", style="Heading.TLabel").pack(anchor="w")
        self.description_var = tk.StringVar(value="")
        ttk.Label(explanation_panel, textvariable=self.description_var, style="Body.TLabel", wraplength=260, justify="left").pack(anchor="w", pady=(8, 16))

        self.distance_list = tk.Text(explanation_panel, height=10, width=32, background=THEME.surface_alt, foreground=THEME.text_primary, relief="flat")
        self.distance_list.pack(fill="both", expand=True)
        self.distance_list.configure(state="disabled")

        self.canvas.after(800, self._maybe_show_tutorial)
        self._update_edge_controls()

    def _on_algo_changed(self) -> None:
        key = self.algo_label_to_key.get(self.algorithm_var.get())
        alg = self.algo_key_to_def.get(key) if key else None
        if not alg:
            return
        if not alg.requires_goal:
            self.goal_node = None
        self._refresh_canvas()

    def _on_compare_toggled(self) -> None:
        enabled = self.compare_enabled.get()
        state = "readonly" if enabled else "disabled"
        self.compare_menu.configure(state=state)
        if not enabled:
            self.compare_overlay.clear()
            self._refresh_canvas()

    def _on_canvas_click(self, event: tk.Event) -> None:
        if not self.dataset.nodes:
            return
        node = self._node_at(event.x, event.y)
        if node is None:
            return
        if self.edit_mode.get():
            self._handle_edit_click(node)
            return
        key = self.algo_label_to_key.get(self.algorithm_var.get())
        alg = self.algo_key_to_def.get(key) if key else None
        if alg and alg.requires_goal:
            if self.start_node is None:
                self.start_node = node
            elif self.goal_node is None:
                self.goal_node = node
            else:
                self.start_node, self.goal_node = node, None
        else:
            self.start_node = node
        self._refresh_canvas()

    def _node_at(self, x: float, y: float) -> Optional[NodeId]:
        for node, (px, py) in self.dataset.positions.items():
            cx = CANVAS_PADDING + px * (self.canvas.winfo_width() - 2 * CANVAS_PADDING)
            cy = CANVAS_PADDING + py * (self.canvas.winfo_height() - 2 * CANVAS_PADDING)
            if (cx - x) ** 2 + (cy - y) ** 2 <= NODE_RADIUS ** 2:
                return node
        return None

    def _handle_edit_click(self, node: NodeId) -> None:
        if self.pending_edit is None:
            self.pending_edit = node
            self.message_var.set(f"Selected node {node}. Pick another node to toggle an edge.")
            return
        if node == self.pending_edit:
            self.message_var.set("Choose a different node to form an edge.")
            return
        a, b = sorted((self.pending_edit, node))
        existing = self.dataset.edges[a].get(b)
        if existing is not None:
            del self.dataset.edges[a][b]
            del self.dataset.edges[b][a]
            self.message_var.set(f"Removed edge {a}-{b}.")
            if self.selected_edge == (a, b):
                self.selected_edge = None
        else:
            weight = float(self.edge_weight_var.get())
            self.dataset.edges[a][b] = weight
            self.dataset.edges[b][a] = weight
            self.selected_edge = (a, b)
            self.message_var.set(f"Added edge {a}-{b} with weight {weight:.1f}.")
        self.pending_edit = None
        self.current_step = None
        self.engine.reset()
        self.compare_engine.reset()
        self.playing = False
        self._update_edge_controls()
        self._refresh_canvas()

    def _on_canvas_motion(self, event: tk.Event) -> None:
        node = self._node_at(event.x, event.y)
        if node == self.hover_node:
            return
        self.hover_node = node
        if node is None:
            return
        flags: List[str] = []
        if self.current_step:
            if node in self.current_step.visited_nodes:
                flags.append("visited")
            elif node in self.current_step.frontier_nodes:
                flags.append("frontier")
            if self.current_step.active_node == node:
                flags.append("active")
        if node == self.start_node:
            flags.append("start")
        if node == self.goal_node:
            flags.append("goal")
        status = ", ".join(flags) if flags else "no current role"
        self.message_var.set(f"Node {node}: {status}")

    def _clear_hover(self) -> None:
        self.hover_node = None

    def _flash_message(self) -> None:
        if not hasattr(self, "message_card"):
            return
        if self._message_flash_id:
            self.message_card.after_cancel(self._message_flash_id)
        self.message_card.configure(background=THEME.accent, highlightbackground=THEME.accent)
        self.message_label.configure(background=THEME.accent, fg=THEME.background)

        def _restore() -> None:
            self.message_card.configure(background=THEME.surface_alt, highlightbackground=THEME.edge_background)
            self.message_label.configure(background=THEME.surface_alt, fg=THEME.text_primary)
            self._message_flash_id = None

        self._message_flash_id = self.message_card.after(280, _restore)

    def _on_edit_mode_toggled(self) -> None:
        if not self.edit_mode.get():
            self.pending_edit = None
        if self.edit_mode.get():
            self.message_var.set("Manual editing on. Select two nodes to toggle an edge.")
            self.edge_label_var.set("Select two nodes to edit an edge.")
        else:
            self.message_var.set("Manual editing off.")
        self._update_edge_controls()

    def _on_weight_changed(self, value: str) -> None:
        if self._suspend_weight_callback:
            return
        if not self.selected_edge:
            return
        weight = float(value)
        a, b = self.selected_edge
        if b not in self.dataset.edges.get(a, {}):
            return
        self.dataset.edges[a][b] = weight
        self.dataset.edges[b][a] = weight
        self.message_var.set(f"Set weight of edge {a}-{b} to {weight:.1f}.")
        self._refresh_canvas()

    def _update_edge_controls(self) -> None:
        if not self.edit_mode.get():
            self._suspend_weight_callback = True
            self.edge_weight_var.set(float(GRAPH_CONFIG.min_weight))
            self._suspend_weight_callback = False
            self.edge_weight_scale.configure(state="disabled")
            self.edge_label_var.set("Enable edit mode to adjust edge weights.")
            return

        if self.selected_edge:
            a, b = self.selected_edge
            weight = self.dataset.edges.get(a, {}).get(b)
            if weight is not None:
                self._suspend_weight_callback = True
                self.edge_weight_var.set(weight)
                self._suspend_weight_callback = False
                self.edge_label_var.set(f"Editing edge {a}-{b}")
                self.edge_weight_scale.configure(state="normal")
                return
        self._suspend_weight_callback = True
        self.edge_weight_var.set(float(GRAPH_CONFIG.min_weight))
        self._suspend_weight_callback = False
        self.edge_label_var.set("Select two nodes to edit an edge.")
        self.edge_weight_scale.configure(state="disabled")

    def _maybe_show_tutorial(self) -> None:
        if self.tutorial_shown:
            return
        self.tutorial_shown = True
        overlay = tk.Toplevel(self.frame)
        overlay.title("Greedy Visualiser Tour")
        overlay.configure(background=THEME.surface)
        overlay.transient(self.frame.winfo_toplevel())
        overlay.grab_set()
        ttk.Label(overlay, text="Hoş geldin!", style="Heading.TLabel").pack(anchor="w", padx=24, pady=(24, 8))
        for line in (
            "Soldaki panelden algoritma ve hız ayarlarını yapabilirsin.",
            "Tuvalde düğümlere tıklayarak başlangıç ve hedef noktalarını seç.",
            "Karşılaştırma moduyla iki algoritmanın seçimlerini üst üste izle.",
            "Manual edit modunda kenar ekleyip sil, ağırlığı kaydırıcıdan güncelle.",
        ):
            ttk.Label(overlay, text=f"• {line}", style="Body.TLabel", wraplength=360, justify="left").pack(anchor="w", padx=24, pady=2)
        ttk.Button(overlay, text="Tamam", style="Accent.TButton", command=overlay.destroy).pack(anchor="e", padx=24, pady=(16, 24))

    def generate_graph(self) -> None:
        options = GraphGenerationOptions(
            node_count=self.node_count_var.get(),
            kind=self.graph_kind_var.get(),
            seed=self.rng.randint(0, 1_000_000),
        )
        self.dataset = build_graph(options, rng=self.rng)
        self.start_node = min(self.dataset.nodes, default=None)
        self.goal_node = max(self.dataset.nodes, default=None)
        self.reset()
        self.message_var.set("Graph ready. Click nodes to set start/goal.")
        self._has_generated = True

    def reset(self) -> None:
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None
        self.engine.reset()
        self.compare_engine.reset()
        self.playing = False
        self.description_var.set("")
        self.queue_view.update_snapshot(None)
        self.distance_list.configure(state="normal")
        self.distance_list.delete("1.0", tk.END)
        self.distance_list.configure(state="disabled")
        self.current_step = None
        self.compare_overlay.clear()
        self.edit_mode.set(False)
        self.pending_edit = None
        self.selected_edge = None
        self._finish_notified = False
        self._update_edge_controls()
        self._refresh_canvas()

    def start(self) -> None:
        key = self.algo_label_to_key.get(self.algorithm_var.get())
        alg_def = self.algo_key_to_def.get(key) if key else None
        if not alg_def:
            return
        if not self.dataset.nodes:
            self.message_var.set("Generate a graph first.")
            return
        start = self.start_node or min(self.dataset.nodes)
        goal = self.goal_node if alg_def.requires_goal else None
        generator = iter(alg_def.runner(self.dataset, start, goal))
        self.engine.bind(generator)
        self.compare_overlay.clear()
        self._finish_notified = False
        if self.compare_enabled.get():
            compare_key = self.algo_label_to_key.get(self.compare_algorithm_var.get())
            compare_def = self.algo_key_to_def.get(compare_key) if compare_key else None
            if compare_def:
                compare_goal = self.goal_node if compare_def.requires_goal else None
                compare_gen = iter(compare_def.runner(self.dataset, start, compare_goal))
                self.compare_engine.bind(compare_gen)
        else:
            self.compare_engine.reset()
        self.playing = True
        self._tick()

    def toggle_play(self) -> None:
        self.playing = not self.playing
        if self.playing:
            self._tick()

    def step_once(self) -> None:
        self.playing = False
        self._next_step()

    def _tick(self) -> None:
        if not self.playing:
            return
        if not self._next_step():
            self.playing = False
            return
        delay = int(APP_CONFIG.animation_delay_ms / max(self.speed_var.get(), 0.1))
        self.after_id = self.canvas.after(delay, self._tick)

    def _next_step(self) -> bool:
        primary = self.engine.step_forward()
        compare: Optional[GraphStep] = None
        if self.compare_enabled.get():
            compare = self.compare_engine.step_forward()
        if not primary and not compare:
            return False
        self._apply_step(primary)
        if compare:
            self._apply_step(compare, is_compare=True)
        elif self.compare_enabled.get():
            if self.compare_overlay:
                self.compare_overlay.clear()
                self._refresh_canvas()
        return True

    def _apply_step(self, step: Optional[GraphStep], *, is_compare: bool = False) -> None:
        if not step:
            return
        if not is_compare:
            self.current_step = step
            self.description_var.set(step.description)
            if not step.done:
                self.message_var.set(step.description)
            if step.distances:
                self.distance_list.configure(state="normal")
                self.distance_list.delete("1.0", tk.END)
                for node, dist in sorted(step.distances.items()):
                    text = "∞" if math.isinf(dist) else f"{dist:.1f}"
                    self.distance_list.insert(tk.END, f"{node}: {text}\n")
                self.distance_list.configure(state="disabled")
            self.queue_view.update_snapshot(step)
            self._refresh_canvas()
        else:
            if step.selected_edges:
                self.compare_overlay = set(step.selected_edges)
            else:
                self.compare_overlay.clear()
            self._refresh_canvas()
        if step.done and not is_compare:
            if not self._finish_notified:
                self._finish_notified = True
                final_message = step.description or "Algorithm completed."
                self.message_var.set(final_message)
        elif step.done and is_compare:
            pass

    def _refresh_canvas(self) -> None:
        state = GraphRenderState(
            dataset=self.dataset,
            start=self.start_node,
            goal=self.goal_node,
            step=self.current_step,
            compare_edges=set(self.compare_overlay),
        )
        self.canvas.draw(state)


class SequenceTab:
    def __init__(self, parent: tk.Widget, *, rng: random.Random) -> None:
        self.rng = rng
        self.frame = ttk.Frame(parent, style="Main.TFrame")

        self.dataset = SequenceDataset(weights=[], values=[])
        self.capacity = SEQUENCE_CONFIG.capacity_default

        self.algorithm_var = tk.StringVar()
        self.engine = AnimationEngine()
        self.playing = False
        self.after_id: Optional[str] = None
        self.tutorial_shown = False
        self._has_generated = False
        self._finish_notified = False
        self._message_flash_id: Optional[str] = None

        self.message_var = tk.StringVar(value="Generate a dataset to begin.")

        self._build()
        self.generate_dataset()

    def _build(self) -> None:
        layout = ttk.Frame(self.frame, style="Main.TFrame")
        layout.pack(fill="both", expand=True)

        controls = ttk.Frame(layout, style="Controls.TFrame", padding=(20, 20))
        controls.pack(side="left", fill="y", padx=(0, 20))

        self.sequence_algorithms = sequence_algorithms()
        self.sequence_label_to_key = {alg.name: alg.key for alg in self.sequence_algorithms}
        self.sequence_key_to_def = {alg.key: alg for alg in self.sequence_algorithms}
        seq_labels = list(self.sequence_label_to_key.keys()) or ["(none)"]
        self.algorithm_var.set(seq_labels[0])

        ttk.Label(controls, text="Greedy Strategy", style="Heading.TLabel").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.algorithm_var,
            values=seq_labels,
            state="readonly",
        ).pack(fill="x", pady=(6, 12))

        ttk.Button(controls, text="Generate", command=self.generate_dataset, style="Flat.TButton").pack(fill="x", pady=(0, 12))
        ttk.Button(controls, text="Start", command=self.start, style="Accent.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Pause / Resume", command=self.toggle_play, style="Flat.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Step", command=self.step_once, style="Flat.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(controls, text="Reset", command=self.reset, style="Flat.TButton").pack(fill="x")

        self.capacity_var = tk.DoubleVar(value=float(self.capacity))
        ttk.Label(controls, text="Capacity", style="Body.TLabel").pack(anchor="w", pady=(12, 0))
        tk.Scale(
            controls,
            from_=10,
            to=120,
            orient="horizontal",
            resolution=1,
            variable=self.capacity_var,
            background=THEME.surface,
            troughcolor=THEME.surface_alt,
            highlightthickness=0,
        ).pack(fill="x")

        self.message_card = tk.Frame(
            controls,
            background=THEME.surface_alt,
            highlightbackground=THEME.edge_background,
            highlightcolor=THEME.edge_background,
            highlightthickness=1,
            bd=0,
            height=96,
        )
        self.message_card.pack(fill="x", pady=(12, 0))
        self.message_card.pack_propagate(False)
        self.message_label = tk.Label(
            self.message_card,
            textvariable=self.message_var,
            wraplength=220,
            justify="left",
            background=THEME.surface_alt,
            fg=THEME.text_primary,
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
            anchor="w",
        )
        self.message_label.pack(fill="x")
        self.message_var.trace_add("write", lambda *_: self._flash_message())

        canvas_panel = ttk.Frame(layout, style="Surface.TFrame", padding=16)
        canvas_panel.pack(side="left", fill="both", expand=True)

        self.canvas = SequenceCanvasView(canvas_panel, width=APP_CONFIG.canvas_size[0], height=APP_CONFIG.canvas_size[1])
        self.canvas.pack(fill="both", expand=True)

        self.description_var = tk.StringVar(value="")
        ttk.Label(canvas_panel, textvariable=self.description_var, style="Body.TLabel", wraplength=420, justify="left").pack(fill="x", pady=(16, 0))

        self.canvas.after(1200, self._maybe_show_tutorial)

    def generate_dataset(self) -> None:
        alg_key = self.sequence_label_to_key.get(self.algorithm_var.get(), "fractional_knapsack")
        options = SequenceGenerationOptions(item_count=self.rng.randint(SEQUENCE_CONFIG.min_items, SEQUENCE_CONFIG.max_items))
        if alg_key == "activity_selection":
            self.dataset = build_activity_dataset(options, rng=self.rng)
            self.capacity = float(len(self.dataset.durations or []))
        else:
            self.dataset, self.capacity = build_knapsack_dataset(options, rng=self.rng)
        self.capacity_var.set(self.capacity)
        self.reset()
        self.message_var.set("Dataset generated. Press start to animate.")
        self._has_generated = True

    def reset(self) -> None:
        if self.after_id:
            self.canvas.after_cancel(self.after_id)
            self.after_id = None
        self.engine.reset()
        self.playing = False
        self.canvas.draw(self.dataset, None)
        self.description_var.set("")
        self._finish_notified = False
        self.message_var.set("Ready. Press Start to watch the run.")

    def start(self) -> None:
        key = self.sequence_label_to_key.get(self.algorithm_var.get())
        alg_def = self.sequence_key_to_def.get(key) if key else None
        if not alg_def:
            return
        capacity = float(self.capacity_var.get()) if alg_def.key == "fractional_knapsack" else None
        generator = iter(alg_def.runner(self.dataset, capacity))
        self.engine.bind(generator)
        self._finish_notified = False
        self.message_var.set("Running... use Pause or Step to control the flow.")
        self.playing = True
        self._tick()

    def toggle_play(self) -> None:
        self.playing = not self.playing
        if self.playing:
            self._tick()

    def step_once(self) -> None:
        self.playing = False
        self._next_step()

    def _tick(self) -> None:
        if not self.playing:
            return
        if not self._next_step():
            self.playing = False
            return
        delay = int(APP_CONFIG.animation_delay_ms * 1.5)
        self.after_id = self.canvas.after(delay, self._tick)

    def _next_step(self) -> bool:
        step = self.engine.step_forward()
        if not step:
            return False
        self.canvas.draw(self.dataset, step)
        self.description_var.set(step.description)
        self.message_var.set(step.description)
        if step.done and not self._finish_notified:
            self._finish_notified = True
            final_message = step.description or "Sequence completed."
            self.message_var.set(final_message)
            self.playing = False
        return True

    def _flash_message(self) -> None:
        if not hasattr(self, "message_card"):
            return
        if self._message_flash_id:
            self.message_card.after_cancel(self._message_flash_id)
        self.message_card.configure(background=THEME.accent, highlightbackground=THEME.accent)
        self.message_label.configure(background=THEME.accent, fg=THEME.background)

        def _restore() -> None:
            self.message_card.configure(background=THEME.surface_alt, highlightbackground=THEME.edge_background)
            self.message_label.configure(background=THEME.surface_alt, fg=THEME.text_primary)
            self._message_flash_id = None

        self._message_flash_id = self.message_card.after(280, _restore)

    def _maybe_show_tutorial(self) -> None:
        if self.tutorial_shown:
            return
        self.tutorial_shown = True
        overlay = tk.Toplevel(self.frame)
        overlay.title("Greedy Sequence Tour")
        overlay.configure(background=THEME.surface)
        overlay.transient(self.frame.winfo_toplevel())
        overlay.grab_set()
        ttk.Label(overlay, text="Kısa tur", style="Heading.TLabel").pack(anchor="w", padx=24, pady=(24, 8))
        for line in (
            "Generate ile yeni veri seti üret.",
            "Capacity kaydırıcısı fractional knapsack için çantayı belirler.",
            "Step ile adım adım izle, mesajlar kararların nedenini anlatır.",
        ):
            ttk.Label(overlay, text=f"• {line}", style="Body.TLabel", wraplength=360, justify="left").pack(anchor="w", padx=24, pady=2)
        ttk.Button(overlay, text="Anladım", style="Accent.TButton", command=overlay.destroy).pack(anchor="e", padx=24, pady=(16, 24))


def launch() -> None:
    root = tk.Tk()
    app = GreedyApp(root)
    root.mainloop()
