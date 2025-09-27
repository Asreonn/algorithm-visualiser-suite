"""Implementation of breadth-first search for unweighted grids."""
from __future__ import annotations

from collections import deque

from ..grid import Tile
from .base import AlgorithmVisualizer, DrawStep, PathfindingAlgorithm


class BreadthFirst(PathfindingAlgorithm):
    def __init__(self) -> None:
        super().__init__('Breadth-First Search')

    def find_path(
        self,
        grid,
        start: Tile,
        end: Tile,
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None = None,
    ) -> bool:
        grid.clear_path()
        grid.update_neighbors()

        frontier = deque([start])
        came_from: dict[Tile, Tile] = {}
        visited: set[Tile] = {start}
        depth_map: dict[Tile, int] = {start: 0}

        if visualiser:
            visualiser.reset()
            visualiser.record(start, depth=0, label="start")
            visualiser.focus(start)
            visualiser.set_metric("frontier", len(frontier))
            visualiser.set_metric("expanded", 0)
            visualiser.set_metric("steps", 0)

        while frontier:
            current = frontier.popleft()

            if visualiser:
                visualiser.focus(current)
                visualiser.record(current, depth=depth_map[current])
                visualiser.increment("expanded")
                visualiser.set_metric("frontier", len(frontier))

            if current == end:
                success, _ = self._reconstruct_path(came_from, end, draw_step, visualiser)
                if not success:
                    return False
                end.make_end()
                if visualiser:
                    visualiser.focus(None)
                return True

            for neighbor in current.neighbors:
                if neighbor in visited or neighbor.is_barrier():
                    continue
                visited.add(neighbor)
                came_from[neighbor] = current
                frontier.append(neighbor)
                if not neighbor.is_end():
                    neighbor.make_open()
                depth_map[neighbor] = depth_map[current] + 1
                if visualiser:
                    visualiser.record(neighbor, depth=depth_map[neighbor])
                    visualiser.set_metric("frontier", len(frontier))

            if visualiser:
                visualiser.increment("steps")
            if not draw_step():
                return False

            if current != start:
                current.make_closed()

        return False


def create() -> BreadthFirst:
    return BreadthFirst()
