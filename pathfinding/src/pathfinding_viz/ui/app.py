"""Pygame front-end for experimenting with different pathfinding algorithms."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pygame as pg

from .. import constants
from ..algorithms import (
    AStar,
    BidirectionalBreadthFirst,
    BreadthFirst,
    Dijkstra,
    GreedyBestFirst,
    WeightedAStar,
)
from ..algorithms.base import AlgorithmVisualizer, PathfindingAlgorithm
from ..grid import Grid, Tile


@dataclass(frozen=True)
class AlgorithmOption:
    """Descriptor used to render and activate algorithm choices."""

    key: int
    title: str
    tagline: str
    description: str
    factory: type[PathfindingAlgorithm]


@dataclass
class TileMetrics:
    """Numbers displayed on top of grid tiles for debugging."""

    g: float | None = None
    h: float | None = None
    f: float | None = None
    depth: int | None = None
    label: str | None = None

    def lines(self) -> list[str]:
        lines: list[str] = []

        def fmt(value: float | None) -> str | None:
            if value is None:
                return None
            if abs(value - int(value)) < 1e-3:
                return str(int(value))
            return f"{value:.1f}"

        primary_parts: list[str] = []
        if self.f is not None:
            primary_parts.append(f"f={fmt(self.f)}")
        elif self.g is not None:
            primary_parts.append(f"g={fmt(self.g)}")
        if self.h is not None and self.f is None:
            primary_parts.append(f"h={fmt(self.h)}")
        if primary_parts:
            lines.append(" ".join(part for part in primary_parts if part))

        secondary_parts: list[str] = []
        if self.g is not None and self.f is not None:
            secondary_parts.append(f"g={fmt(self.g)}")
        if self.h is not None and self.f is not None:
            secondary_parts.append(f"h={fmt(self.h)}")
        if self.depth is not None:
            secondary_parts.append(f"d={self.depth}")
        if secondary_parts:
            lines.append(" ".join(secondary_parts))

        if self.label and len(lines) < 2:
            lines.append(self.label)

        return lines[:2]

    def primary_score(self) -> float | None:
        for value in (self.f, self.g, self.h, self.depth):
            if value is not None:
                return float(value)
        return None


class AppAlgorithmVisualizer(AlgorithmVisualizer):
    """Adapter that lets algorithms push data back into the UI."""

    def __init__(self, app: 'PathfindingApp') -> None:
        self._app = app

    def reset(self) -> None:  # noqa: D401 - interface match
        self._app._clear_metrics()
        self._app._runtime_metrics = {
            "frontier": 0,
            "expanded": 0,
            "steps": 0,
            "path": 0,
        }

    def record(
        self,
        tile: Tile,
        *,
        g: float | None = None,
        h: float | None = None,
        f: float | None = None,
        depth: int | None = None,
        label: str | None = None,
    ) -> None:
        self._app._tile_metrics[tile] = TileMetrics(g=g, h=h, f=f, depth=depth, label=label)

    def focus(self, tile: Tile | None) -> None:
        self._app._focus_tile = tile

    def set_metric(self, name: str, value: float | int) -> None:
        self._app._runtime_metrics[name] = value

    def increment(self, name: str, amount: int = 1) -> None:
        self._app._runtime_metrics[name] = self._app._runtime_metrics.get(name, 0) + amount


class PathfindingApp:
    def __init__(
        self,
        *,
        width: int = 800,
        rows: int = 40,
        fps: int = 60,
        height: int | None = None,
    ) -> None:
        pg.init()
        pg.display.set_caption("Pathfinding Studio")

        self.rows = rows
        self.panel_width = 400
        self._grid_target = max(width, 640)
        self._height_override = height
        self.start: Tile | None = None
        self.end: Tile | None = None

        self._running = False
        self._is_solving = False
        self._drag_mode: str | None = None
        self._paused = False
        self._abort_requested = False
        self._stop_requested = False

        self._tile_metrics: Dict[Tile, TileMetrics] = {}
        self._focus_tile: Tile | None = None
        self._runtime_metrics: Dict[str, float] = {
            "frontier": 0,
            "expanded": 0,
            "steps": 0,
            "path": 0,
        }

        self._scale = 1.0
        self._init_fonts(self._scale)

        self.algorithm_options: list[AlgorithmOption] = [
            AlgorithmOption(
                key=pg.K_1,
                title="A* Search",
                tagline="Heuristic-guided shortest path",
                description=(
                    "A* combines the exact path cost g(n) with a Manhattan heuristic to "
                    "prioritise promising frontier tiles."
                ),
                factory=AStar,
            ),
            AlgorithmOption(
                key=pg.K_2,
                title="Dijkstra",
                tagline="Uniform-cost exploration",
                description=(
                    "Dijkstra expands neighbours in order of path cost and finds the "
                    "shortest route without using a heuristic."
                ),
                factory=Dijkstra,
            ),
            AlgorithmOption(
                key=pg.K_3,
                title="Breadth-First",
                tagline="Layer-by-layer sweep",
                description=(
                    "Breadth-First Search explores layer by layer and guarantees the "
                    "shortest route on unweighted grids."
                ),
                factory=BreadthFirst,
            ),
            AlgorithmOption(
                key=pg.K_4,
                title="Weighted A*",
                tagline="Bias towards heuristic",
                description=(
                    "Weighted A* multiplies heuristics (w=1.5) to race toward the goal "
                    "while still respecting path cost updates."
                ),
                factory=WeightedAStar,
            ),
            AlgorithmOption(
                key=pg.K_5,
                title="Greedy Best-First",
                tagline="Heuristic only",
                description=(
                    "Greedy Best-First picks the tile with the lowest heuristic value, "
                    "ignoring accumulated cost for maximum speed."
                ),
                factory=GreedyBestFirst,
            ),
            AlgorithmOption(
                key=pg.K_6,
                title="Bidirectional BFS",
                tagline="Meet in the middle",
                description=(
                    "Bidirectional BFS grows from start and goal simultaneously to cut the "
                    "search depth dramatically."
                ),
                factory=BidirectionalBreadthFirst,
            ),
        ]
        self._algorithm_lookup = {
            option.key: index for index, option in enumerate(self.algorithm_options)
        }
        self._selected_algorithm_index = 0

        self._algorithm_button_rects: list[tuple[pg.Rect, int]] = []
        self._control_entry_rects: list[tuple[pg.Rect, str]] = []

        self.visualiser = AppAlgorithmVisualizer(self)
        self._instructions_text = (
            "Left click: set start & goal or draw barriers.  "
            "Drag while holding left to paint walls.  "
            "Hold right click to erase."
        )

        self.fps = fps
        self.clock = pg.time.Clock()

        self._configure_layout()

    def _configure_layout(self) -> None:
        padding = 24
        inner_width = self.panel_width - 2 * padding
        tagline_width = max(inner_width - 48, inner_width // 2)

        info = pg.display.Info()
        display_width = info.current_w or 1920
        display_height = info.current_h or 1080
        margin = 96
        available_height = max(display_height - margin, 640)
        available_width = max(display_width - self.panel_width - margin, 640)

        panel_height = self._compute_panel_height(inner_width, tagline_width)
        attempts = 0
        while panel_height > available_height and self._scale > 0.66 and attempts < 5:
            scale_ratio = available_height / panel_height
            new_scale = max(0.65, self._scale * scale_ratio * 0.96)
            if abs(new_scale - self._scale) < 0.01:
                self._scale = new_scale
                self._init_fonts(self._scale)
                panel_height = self._compute_panel_height(inner_width, tagline_width)
                break
            self._scale = new_scale
            self._init_fonts(self._scale)
            panel_height = self._compute_panel_height(inner_width, tagline_width)
            attempts += 1

        panel_height = self._compute_panel_height(inner_width, tagline_width)

        target_tile = 34
        max_rows_width = max(12, available_width // target_tile)
        max_rows_height = max(12, available_height // target_tile)
        effective_rows = min(self.rows, max_rows_width, max_rows_height)
        if effective_rows < 12:
            effective_rows = 12
        self.rows = effective_rows

        available_tile = min(available_width // self.rows, available_height // self.rows)
        if available_tile <= 0:
            available_tile = target_tile
        if self._height_override is not None:
            available_tile = min(available_tile, self._height_override // self.rows)

        tile_size = min(max(24, available_tile), 44)
        def target_tile_for_rows(rows: int) -> int:
            if not self._grid_target:
                return 0
            target = self._grid_target // rows
            if target <= 0:
                return 0
            return min(44, max(24, target))

        target_tile_from_request = target_tile_for_rows(self.rows)
        if target_tile_from_request:
            tile_size = min(44, max(tile_size, target_tile_from_request))
        while tile_size < 30 and self.rows > 12:
            self.rows = max(12, self.rows - 2)
            available_tile = min(available_width // self.rows, available_height // self.rows)
            if available_tile <= 0:
                available_tile = target_tile
            tile_size = min(max(24, available_tile), 44)
            target_tile_from_request = target_tile_for_rows(self.rows)
            if target_tile_from_request:
                tile_size = min(44, max(tile_size, target_tile_from_request))
            if self.rows == 12:
                break

        max_tile_by_space = min(available_width // self.rows, available_height // self.rows)
        if max_tile_by_space > 0:
            tile_size = min(tile_size, max_tile_by_space)
        tile_size = max(24, tile_size)

        grid_size = tile_size * self.rows
        window_height = max(grid_size, int(panel_height))
        if self._height_override is not None:
            window_height = max(window_height, self._height_override)

        self.height = window_height

        self.grid = Grid(rows=self.rows, width=grid_size)
        actual_grid_size = self.grid.tile_size * self.rows
        self.width = actual_grid_size

        self.screen = pg.display.set_mode((self.width + self.panel_width, self.height))
        self.grid_rect = pg.Rect(0, 0, self.width, self.width)
        self.panel_rect = pg.Rect(self.width, 0, self.panel_width, self.height)

    def _compute_panel_height(self, inner_width: int, tagline_width: int) -> int:
        padding = 24
        y = padding
        y += self.font_heading.get_linesize() + 10
        y += self.font_label.get_linesize() + 8

        card_gap = 14
        for option in self.algorithm_options:
            tagline_lines = self._wrap_text(option.tagline, self.font_small, tagline_width)
            rect_height = self.font_title.get_linesize() + len(tagline_lines) * self.font_small.get_linesize() + 36
            y += rect_height + card_gap

        y += 4
        y += self.font_label.get_linesize() + 4

        description_heights = [
            len(self._wrap_text(option.description, self.font_text, inner_width)) * self.font_text.get_linesize()
            for option in self.algorithm_options
        ]
        if description_heights:
            y += max(description_heights)

        y += 18
        y += self.font_label.get_linesize() + 8

        controls = 3
        control_line = self.font_text.get_linesize() + 6
        y += controls * control_line

        y += 8
        y += self.font_label.get_linesize() + 6
        legend_items = 7
        y += legend_items * self.font_text.get_linesize()

        y += 10
        instruction_lines = self._wrap_text(self._instructions_text, self.font_small, inner_width)
        y += len(instruction_lines) * self.font_small.get_linesize()

        y += padding
        return int(y)

    def _clear_metrics(self) -> None:
        self._tile_metrics.clear()
        self._focus_tile = None

    # Public API --------------------------------------------------------------
    def run(self) -> None:
        self._running = True
        while self._running:
            self.clock.tick(self.fps)
            self._handle_events()
            if not self._is_solving:
                self._render()
        pg.quit()

    # Event handling ---------------------------------------------------------
    def _handle_events(self) -> None:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._running = False
                continue

            if event.type == pg.MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)
            elif event.type == pg.MOUSEBUTTONUP:
                self._handle_mouse_up()
            elif event.type == pg.MOUSEMOTION:
                self._handle_mouse_motion(event)
            elif event.type == pg.KEYDOWN:
                self._handle_key(event)

    def _handle_mouse_down(self, event: pg.event.Event) -> None:
        if self.panel_rect.collidepoint(event.pos):
            self._handle_panel_click(event.pos)
            return

        if not self.grid_rect.collidepoint(event.pos):
            return

        tile = self.grid.get_tile_from_pos(event.pos)
        if not tile:
            return

        if event.button == 1:  # left click
            self._drag_mode = self._apply_left_click(tile)
        elif event.button == 3:  # right click
            self._drag_mode = self._apply_right_click(tile)

    def _handle_mouse_up(self) -> None:
        self._drag_mode = None

    def _handle_mouse_motion(self, event: pg.event.Event) -> None:
        if not self.grid_rect.collidepoint(event.pos):
            return

        tile = self.grid.get_tile_from_pos(event.pos)
        if not tile:
            return

        if self._drag_mode == "barrier" and event.buttons[0]:
            if tile not in {self.start, self.end}:
                tile.make_barrier()
                self._invalidate_path()
        elif self._drag_mode == "erase" and event.buttons[2]:
            self._reset_tile(tile)
            self._invalidate_path()

    def _handle_panel_click(self, position: tuple[int, int]) -> None:
        for rect, index in self._algorithm_button_rects:
            if rect.collidepoint(position):
                self._select_algorithm(index)
                return

        for rect, action in self._control_entry_rects:
            if rect.collidepoint(position):
                if action == "run":
                    self._trigger_pathfinding()
                elif action == "stop":
                    self._request_stop()
                elif action == "clear":
                    self.grid.clear_path()
                    self._clear_metrics()
                    self._refresh_special_tiles()
                elif action == "reset":
                    self._reset_grid()
                return

    def _handle_key(self, event: pg.event.Event) -> None:
        if event.key == pg.K_SPACE:
            self._trigger_pathfinding()
        elif event.key == pg.K_s:
            self._request_stop()
        elif event.key == pg.K_c:
            self._reset_grid()
        elif event.key == pg.K_r:
            self.grid.clear_path()
            self._clear_metrics()
            self._refresh_special_tiles()
        elif event.key in self._algorithm_lookup:
            self._select_algorithm(self._algorithm_lookup[event.key])

    def _apply_left_click(self, tile: Tile) -> str | None:
        if not self.start and tile != self.end:
            self.start = tile
            self.start.make_start()
            self._invalidate_path()
            return None
        if not self.end and tile != self.start:
            self.end = tile
            self.end.make_end()
            self._invalidate_path()
            return None
        if tile not in {self.start, self.end}:
            tile.make_barrier()
            self._invalidate_path()
            return "barrier"
        return None

    def _apply_right_click(self, tile: Tile) -> str | None:
        self._reset_tile(tile)
        self._invalidate_path()
        return "erase"

    def _reset_tile(self, tile: Tile) -> None:
        if tile == self.start:
            tile.reset()
            self.start = None
        elif tile == self.end:
            tile.reset()
            self.end = None
        else:
            tile.reset()

    # Algorithm management ---------------------------------------------------
    def _select_algorithm(self, index: int) -> None:
        if index == self._selected_algorithm_index:
            return
        self._selected_algorithm_index = index
        self.grid.clear_path()
        self._clear_metrics()
        self._refresh_special_tiles()

    def _trigger_pathfinding(self) -> None:
        if not self.start or not self.end:
            return

        self._clear_metrics()
        self._is_solving = True
        self._stop_requested = False
        option = self.algorithm_options[self._selected_algorithm_index]
        algorithm = option.factory()
        found = algorithm.find_path(
            self.grid,
            self.start,
            self.end,
            self._draw_step,
            visualiser=self.visualiser,
        )
        if found:
            self.start.make_start()
            self.end.make_end()
        self._is_solving = False
        self._stop_requested = False

    # Rendering ---------------------------------------------------------------
    def _render(self) -> None:
        self.screen.fill(constants.BACKGROUND)
        pg.draw.rect(self.screen, constants.GRID_BACKGROUND, self.grid_rect)
        self.grid.draw(self.screen)
        self._draw_heatmap_overlay()
        self._draw_metric_labels()
        pg.draw.line(
            self.screen,
            constants.PANEL_BORDER,
            (self.grid_rect.width, 0),
            (self.grid_rect.width, self.height),
        )
        self._draw_panel()
        pg.display.flip()

    def _draw_step(self) -> bool:
        self._render()
        self.clock.tick(self.fps)
        return not (self._abort_requested or self._stop_requested)

    def _request_stop(self) -> None:
        if not self._is_solving:
            return
        self._stop_requested = True
        self.grid.clear_path()
        self._clear_metrics()
        self._refresh_special_tiles()

    def _draw_panel(self) -> None:
        pg.draw.rect(self.screen, constants.PANEL_BACKGROUND, self.panel_rect)
        pg.draw.rect(self.screen, constants.PANEL_BORDER, self.panel_rect, width=1)

        padding = 24
        x = self.panel_rect.x + padding
        y = padding
        max_width = self.panel_rect.width - 2 * padding
        mouse_pos = pg.mouse.get_pos()

        self._blit_text("Pathfinding Studio", self.font_heading, constants.TEXT_PRIMARY, x, y)
        y += self.font_heading.get_linesize() + 10

        self._blit_text("Algorithms", self.font_label, constants.TEXT_MUTED, x, y)
        y += self.font_label.get_linesize() + 8

        self._algorithm_button_rects = []
        for index, option in enumerate(self.algorithm_options):
            tagline_lines = self._wrap_text(option.tagline, self.font_small, max_width - 48)
            content_height = self.font_title.get_linesize() + len(tagline_lines) * self.font_small.get_linesize()
            rect_height = content_height + 36
            rect = pg.Rect(x, y, max_width, rect_height)
            is_selected = index == self._selected_algorithm_index
            fill_color = constants.CONTROL_BACKGROUND
            title_color = constants.TEXT_PRIMARY
            tagline_color = constants.TEXT_MUTED
            badge_fill = constants.BADGE_BACKGROUND
            badge_border = constants.PANEL_BORDER
            badge_text = constants.TEXT_MUTED

            if is_selected:
                fill_color = constants.CONTROL_ACTIVE
                title_color = constants.CONTROL_TEXT_ON_ACCENT
                tagline_color = constants.CONTROL_TEXT_ON_ACCENT
                badge_fill = constants.CONTROL_TEXT_ON_ACCENT
                badge_border = 0
                badge_text = constants.CONTROL_ACTIVE
            elif rect.collidepoint(mouse_pos):
                fill_color = constants.CONTROL_HOVER

            pg.draw.rect(self.screen, fill_color, rect, border_radius=16)
            if not is_selected:
                pg.draw.rect(self.screen, constants.PANEL_BORDER, rect, width=1, border_radius=16)

            title_surface = self.font_title.render(option.title, True, title_color)
            self.screen.blit(title_surface, (rect.x + 20, rect.y + 12))

            tagline_y = rect.y + 12 + self.font_title.get_linesize() + 6
            for line in tagline_lines:
                line_surface = self.font_small.render(line, True, tagline_color)
                self.screen.blit(line_surface, (rect.x + 20, tagline_y))
                tagline_y += self.font_small.get_linesize()

            shortcut_label = str(index + 1)
            shortcut_surface = self.font_small.render(shortcut_label, True, badge_text)
            shortcut_bg = pg.Rect(rect.right - 40, rect.y + 12, 28, 24)
            pg.draw.rect(self.screen, badge_fill, shortcut_bg, border_radius=8)
            if badge_border:
                pg.draw.rect(self.screen, constants.PANEL_BORDER, shortcut_bg, width=1, border_radius=8)
            self.screen.blit(
                shortcut_surface,
                (shortcut_bg.x + (shortcut_bg.width - shortcut_surface.get_width()) / 2,
                 shortcut_bg.y + (shortcut_bg.height - shortcut_surface.get_height()) / 2),
            )

            self._algorithm_button_rects.append((rect, index))
            y += rect.height + 14

        y += 4
        self._blit_text("Method", self.font_label, constants.TEXT_MUTED, x, y)
        y += self.font_label.get_linesize() + 4
        selected = self.algorithm_options[self._selected_algorithm_index]
        y = self._draw_wrapped_text(selected.description, self.font_text, constants.TEXT_PRIMARY, x, y, max_width)

        y += 18
        self._blit_text("Controls", self.font_label, constants.TEXT_MUTED, x, y)
        y += 8

        controls = [
            ("Run all algorithms", "Space", "run"),
            ("Stop run", "S", "stop"),
            ("Clear paths", "R", "clear"),
            ("Reset grid", "C", "reset"),
        ]

        line_spacing = self.font_text.get_linesize() + 6
        self._control_entry_rects = []
        for label, shortcut, action in controls:
            entry_text = f"{label}  ·  {shortcut}"
            text_surface = self.font_text.render(entry_text, True, constants.TEXT_PRIMARY)
            text_width = text_surface.get_width()
            text_height = text_surface.get_height()
            hit_rect = pg.Rect(x - 6, y - 4, text_width + 12, text_height + 8)
            hovered = hit_rect.collidepoint(mouse_pos)
            colour = constants.ACCENT if hovered else constants.TEXT_PRIMARY
            text_surface = self.font_text.render(entry_text, True, colour)
            self.screen.blit(text_surface, (x, y))
            self._control_entry_rects.append((hit_rect, action))
            y += line_spacing

        y += 8
        self._blit_text("Legend", self.font_label, constants.TEXT_MUTED, x, y)
        y += self.font_label.get_linesize() + 6
        legend_items = [
            ("Start", constants.TILE_START),
            ("Goal", constants.TILE_END),
            ("Wall", constants.TILE_BARRIER),
            ("Frontier", constants.TILE_OPEN),
            ("Explored", constants.TILE_CLOSED),
            ("Solution", constants.TILE_PATH),
            ("Empty", constants.TILE_EMPTY),
        ]
        swatch_size = 14
        line_height = self.font_text.get_linesize()
        for label, colour in legend_items:
            swatch_rect = pg.Rect(x, y, swatch_size, swatch_size)
            pg.draw.rect(self.screen, colour, swatch_rect, border_radius=4)
            pg.draw.rect(self.screen, constants.PANEL_BORDER, swatch_rect, width=1, border_radius=4)
            text_surface = self.font_text.render(label, True, constants.TEXT_PRIMARY)
            self.screen.blit(text_surface, (swatch_rect.right + 12, y - 2))
            y += line_height

        y += 10
        self._draw_wrapped_text(self._instructions_text, self.font_small, constants.TEXT_MUTED, x, y, max_width)

    def _draw_heatmap_overlay(self) -> None:
        if not self._tile_metrics:
            return

        samples: list[tuple[Tile, float | None, float | None]] = []
        for tile, metrics in self._tile_metrics.items():
            if tile.is_start() or tile.is_end() or tile.is_barrier():
                continue

            g_value = metrics.g if metrics.g is not None else metrics.depth
            h_value = metrics.h
            if g_value is None and h_value is None:
                continue
            samples.append((tile, g_value, h_value))

        if not samples:
            return

        g_values = [float(val) for _, val, _ in samples if val is not None]
        h_values = [float(val) for _, _, val in samples if val is not None]
        g_min = min(g_values) if g_values else 0.0
        g_span = max((max(g_values) - g_min), 1e-6) if g_values else 1.0
        h_min = min(h_values) if h_values else 0.0
        h_span = max((max(h_values) - h_min), 1e-6) if h_values else 1.0

        overlay = pg.Surface((self.grid_rect.width, self.grid_rect.height), pg.SRCALPHA)
        for tile, g_value, h_value in samples:
            g_ratio = (float(g_value) - g_min) / g_span if g_value is not None else 0.0
            h_ratio = (float(h_value) - h_min) / h_span if h_value is not None else 1.0
            colour = self._heat_colour(g_ratio, h_ratio)
            rect = pg.Rect(tile.x, tile.y, tile.size, tile.size)
            pg.draw.rect(overlay, colour, rect)

        self.screen.blit(overlay, self.grid_rect.topleft)

    def _draw_metric_labels(self) -> None:
        if not self._tile_metrics:
            return

        for tile, metrics in self._tile_metrics.items():
            lines = metrics.lines()
            if not lines:
                continue

            tile_size = tile.size
            if tile_size >= 34:
                primary_font = self.font_metrics_large
                secondary_font = self.font_metrics
            elif tile_size >= 22:
                primary_font = self.font_metrics
                secondary_font = self.font_metrics_small
            else:
                primary_font = self.font_metrics_small
                secondary_font = self.font_metrics_small

            base_x = tile.x + tile_size * 0.14
            base_y = tile.y + tile_size * 0.12
            for idx, line in enumerate(lines):
                font = primary_font if idx == 0 else secondary_font
                colour = constants.TEXT_PRIMARY
                surface = font.render(line, True, colour)
                offset_y = base_y + idx * (font.get_linesize() + 2)
                self.screen.blit(surface, (base_x, offset_y))

    def _heat_colour(self, g_ratio: float, h_ratio: float) -> tuple[int, int, int, int]:
        g_ratio = max(0.0, min(1.0, g_ratio))
        h_ratio = max(0.0, min(1.0, h_ratio))

        start_blend = self._blend(constants.TILE_START, constants.HEAT_LOW, g_ratio)
        goal_blend = self._blend(constants.TILE_END, constants.HEAT_HIGH, 1.0 - h_ratio)
        combined = self._blend(start_blend, goal_blend, 0.5)
        intensity = max(g_ratio, 1.0 - h_ratio)
        alpha = int(constants.HEAT_ALPHA * (0.45 + 0.55 * intensity))
        return (*combined, alpha)

    def _blend(self, a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
        t = max(0.0, min(1.0, t))
        return (
            int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t),
        )

    def _init_fonts(self, scale: float) -> None:
        def scaled(size: int) -> int:
            return max(10, int(round(size * scale)))

        def load(size: int, *, bold: bool = False) -> pg.font.Font:
            return pg.font.SysFont(("segoe ui", "segoeui", "arial", "sans-serif"), scaled(size), bold=bold)

        self.font_heading = load(24, bold=True)
        self.font_label = load(14, bold=True)
        self.font_title = load(15, bold=True)
        self.font_text = load(13)
        self.font_small = load(11)
        self.font_metrics_large = load(15)
        self.font_metrics = load(12)
        self.font_metrics_small = load(10)

    # Helpers ----------------------------------------------------------------
    def _wrap_text(self, text: str, font: pg.font.Font, max_width: int) -> list[str]:
        lines: list[str] = []
        for paragraph in text.splitlines():
            words = paragraph.split()
            current = ""
            for word in words:
                test = f"{current} {word}".strip()
                if font.size(test)[0] <= max_width:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            if current:
                lines.append(current)
        return lines

    def _draw_wrapped_text(
        self,
        text: str,
        font: pg.font.Font,
        colour: tuple[int, int, int],
        x: int,
        y: int,
        max_width: int,
    ) -> int:
        for line in self._wrap_text(text, font, max_width):
            self._blit_text(line, font, colour, x, y)
            y += font.get_linesize()
        return y

    def _blit_text(
        self,
        text: str,
        font: pg.font.Font,
        colour: tuple[int, int, int],
        x: int,
        y: int,
    ) -> None:
        surface = font.render(text, True, colour)
        self.screen.blit(surface, (x, y))

    def _invalidate_path(self) -> None:
        self.grid.clear_path()
        self._clear_metrics()
        self._refresh_special_tiles()

    def _refresh_special_tiles(self) -> None:
        if self.start:
            self.start.make_start()
        if self.end:
            self.end.make_end()

    def _reset_grid(self) -> None:
        self.grid = Grid(rows=self.rows, width=self.width)
        self.start = None
        self.end = None
        self._clear_metrics()
