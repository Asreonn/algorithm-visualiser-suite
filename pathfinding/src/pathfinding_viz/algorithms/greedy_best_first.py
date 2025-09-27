"""Greedy best-first search: expands the node closest to the goal by heuristic."""
from __future__ import annotations

import heapq

from ..grid import Tile
from .astar import manhattan
from .base import AlgorithmVisualizer, DrawStep, PathfindingAlgorithm


class GreedyBestFirst(PathfindingAlgorithm):
    def __init__(self) -> None:
        super().__init__("Greedy Best-First")

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

        if visualiser:
            visualiser.reset()
            visualiser.record(start, h=manhattan(start, end), label="start")
            visualiser.focus(start)
            visualiser.set_metric("frontier", 1)
            visualiser.set_metric("expanded", 0)
            visualiser.set_metric("steps", 0)

        came_from: dict[Tile, Tile] = {}
        visited: set[Tile] = {start}

        count = 0
        frontier: list[tuple[int, int, Tile]] = []
        heapq.heappush(frontier, (manhattan(start, end), count, start))

        while frontier:
            _, _, current = heapq.heappop(frontier)

            if visualiser:
                visualiser.focus(current)
                visualiser.record(current, h=manhattan(current, end))
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
                count += 1
                heuristic = manhattan(neighbor, end)
                heapq.heappush(frontier, (heuristic, count, neighbor))
                if not neighbor.is_end():
                    neighbor.make_open()
                if visualiser:
                    visualiser.record(neighbor, h=heuristic)
                    visualiser.set_metric("frontier", len(frontier))

            if visualiser:
                visualiser.increment("steps")
            if not draw_step():
                return False

            if current != start:
                current.make_closed()

        return False


def create() -> GreedyBestFirst:
    return GreedyBestFirst()
