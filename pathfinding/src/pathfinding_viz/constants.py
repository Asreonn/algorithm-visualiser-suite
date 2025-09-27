"""Shared constants for the pathfinding visualiser."""

from __future__ import annotations

from dataclasses import dataclass


def _hex(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6 hex digits, got {value!r}")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


@dataclass(frozen=True)
class Theme:
    background: tuple[int, int, int]
    surface: tuple[int, int, int]
    surface_alt: tuple[int, int, int]
    canvas_background: tuple[int, int, int]
    border_strong: tuple[int, int, int]
    border_subtle: tuple[int, int, int]
    text_primary: tuple[int, int, int]
    text_muted: tuple[int, int, int]
    accent: tuple[int, int, int]
    accent_hover: tuple[int, int, int]
    control_background: tuple[int, int, int]
    control_hover: tuple[int, int, int]
    tile_empty: tuple[int, int, int]
    tile_barrier: tuple[int, int, int]
    tile_frontier: tuple[int, int, int]
    tile_explored: tuple[int, int, int]
    tile_path: tuple[int, int, int]
    tile_start: tuple[int, int, int]
    tile_end: tuple[int, int, int]
    legend_badge: tuple[int, int, int]
    heat_low: tuple[int, int, int]
    heat_high: tuple[int, int, int]
    heat_alpha: int


THEME = Theme(
    background=_hex("#0f1115"),
    surface=_hex("#181b21"),
    surface_alt=_hex("#20242c"),
    canvas_background=_hex("#0b0d10"),
    border_strong=_hex("#2a2f3c"),
    border_subtle=_hex("#2b3240"),
    text_primary=_hex("#f8fafc"),
    text_muted=_hex("#94a3b8"),
    accent=_hex("#38bdf8"),
    accent_hover=_hex("#52c8fa"),
    control_background=_hex("#252a35"),
    control_hover=_hex("#2e3441"),
    tile_empty=_hex("#20242c"),
    tile_barrier=_hex("#0b0d10"),
    tile_frontier=_hex("#22c55e"),
    tile_explored=_hex("#ef4444"),
    tile_path=_hex("#8b5cf6"),
    tile_start=_hex("#0ea5e9"),
    tile_end=_hex("#f43f5e"),
    legend_badge=_hex("#1f242d"),
    heat_low=_hex("#38bdf8"),
    heat_high=_hex("#f472b6"),
    heat_alpha=150,
)

# Tile palette ----------------------------------------------------------------
TILE_EMPTY = THEME.tile_empty
TILE_BARRIER = THEME.tile_barrier
TILE_OPEN = THEME.tile_frontier
TILE_CLOSED = THEME.tile_explored
TILE_PATH = THEME.tile_path
TILE_START = THEME.tile_start
TILE_END = THEME.tile_end

# UI palette ------------------------------------------------------------------
BACKGROUND = THEME.background
GRID_BACKGROUND = THEME.canvas_background
GRID_LINES = THEME.border_subtle
PANEL_BACKGROUND = THEME.surface
PANEL_BORDER = THEME.border_strong
BADGE_BACKGROUND = THEME.legend_badge
TEXT_PRIMARY = THEME.text_primary
TEXT_MUTED = THEME.text_muted
CONTROL_BACKGROUND = THEME.control_background
CONTROL_HOVER = THEME.control_hover
CONTROL_ACTIVE = THEME.accent
CONTROL_ACTIVE_HOVER = THEME.accent_hover
CONTROL_TEXT_ON_ACCENT = THEME.background
ACCENT = THEME.accent
HEAT_LOW = THEME.heat_low
HEAT_HIGH = THEME.heat_high
HEAT_ALPHA = THEME.heat_alpha
