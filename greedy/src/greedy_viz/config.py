"""Configuration and theme settings for the greedy visualiser."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Theme:
    """Minimalist dark theme shared with the other visualisers."""

    background: str = "#0f1115"
    surface: str = "#181b21"
    surface_alt: str = "#20242c"
    canvas_background: str = "#0b0d10"
    node_default: str = "#38bdf8"
    node_visited: str = "#22c55e"
    node_frontier: str = "#facc15"
    edge_selected: str = "#8b5cf6"
    edge_candidate: str = "#f97316"
    edge_background: str = "#334155"
    text_primary: str = "#f8fafc"
    text_secondary: str = "#94a3b8"
    accent: str = "#38bdf8"
    warning: str = "#f43f5e"


@dataclass(frozen=True)
class GraphConfig:
    """Generation knobs for graph-based greedy algorithms."""

    default_node_count: int = 10
    min_node_count: int = 5
    max_node_count: int = 18
    min_weight: int = 1
    max_weight: int = 12
    grid_rows: int = 5
    grid_cols: int = 5


@dataclass(frozen=True)
class SequenceConfig:
    """Configuration for sequence-style greedy problems."""

    min_items: int = 5
    max_items: int = 12
    value_range: Tuple[int, int] = (10, 140)
    weight_range: Tuple[int, int] = (1, 15)
    capacity_default: int = 35


@dataclass(frozen=True)
class AppConfig:
    """Global settings for the Tkinter app."""

    steps_per_second: int = 24
    animation_delay_ms: int = 40
    max_history: int = 800
    canvas_size: Tuple[int, int] = (860, 540)


THEME = Theme()
GRAPH_CONFIG = GraphConfig()
SEQUENCE_CONFIG = SequenceConfig()
APP_CONFIG = AppConfig()
