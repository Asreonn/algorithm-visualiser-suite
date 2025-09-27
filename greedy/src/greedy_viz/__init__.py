"""Public entry-point for the greedy algorithm visualiser."""
from __future__ import annotations

from greedy_viz.algorithms import graph as _graph_algorithms  # noqa: F401
from greedy_viz.algorithms import sequences as _sequence_algorithms  # noqa: F401
from greedy_viz.ui.app import launch

__all__ = ["launch"]
