"""Application-wide configuration and theme definitions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Theme:
    """Defines the minimalist colour palette used by the visualizer UI."""

    background: str = "#0f1115"
    surface: str = "#181b21"
    surface_alt: str = "#20242c"
    canvas_background: str = "#0b0d10"
    bar: str = "#38bdf8"
    bar_dim: str = "#1d4ed8"
    compare_primary: str = "#facc15"
    compare_secondary: str = "#f97316"
    compare_aux: str = "#f472b6"
    swap_primary: str = "#22d3ee"
    swap_secondary: str = "#a855f7"
    overwrite_primary: str = "#22c55e"
    overwrite_secondary: str = "#16a34a"
    sorted: str = "#8b5cf6"
    pivot: str = "#ef4444"
    highlight: str = "#a855f7"
    range_start: str = "#0ea5e9"
    range_end: str = "#f43f5e"
    text_primary: str = "#f8fafc"
    text_secondary: str = "#94a3b8"
    accent: str = "#38bdf8"


@dataclass(frozen=True)
class AppConfig:
    """Immutable configuration knobs for the visualizer."""

    dataset_length: int = 120
    dataset_min_value: int = 5
    dataset_max_value: int = 380
    steps_per_second: int = 90
    panel_canvas_size: Tuple[int, int] = (760, 180)
    persistent_highlight_labels: Tuple[str, ...] = ("pivot",)


THEME = Theme()
APP_CONFIG = AppConfig()
