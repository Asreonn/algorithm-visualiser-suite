"""Abstract base class for pathfinding algorithms."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, Protocol

from ..grid import Grid, Tile

DrawStep = Callable[[], bool]


class AlgorithmVisualizer(Protocol):
    """Optional hooks implemented by the UI for richer visual debugging."""

    def reset(self) -> None:
        ...

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
        ...

    def focus(self, tile: Tile | None) -> None:
        ...

    def set_metric(self, name: str, value: float | int) -> None:
        ...

    def increment(self, name: str, amount: int = 1) -> None:
        ...


class PathfindingAlgorithm(ABC):
    """Base contract for algorithms used by the visualiser."""

    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def find_path(
        self,
        grid: Grid,
        start: Tile,
        end: Tile,
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None = None,
    ) -> bool:
        """Perform a search and paint intermediate states."""

    # Shared helpers ---------------------------------------------------------
    def _reconstruct_path(
        self,
        came_from: Dict[Tile, Tile],
        current: Tile,
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None = None,
    ) -> tuple[bool, int]:
        length = 0
        while current in came_from:
            current = came_from[current]
            if not current.is_start():
                current.make_path()
            length += 1
            if not draw_step():
                return False, length
        if visualiser:
            visualiser.set_metric("path", length)
        return True, length
