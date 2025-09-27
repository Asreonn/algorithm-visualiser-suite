"""Implementation of Dijkstra's shortest path algorithm."""
from __future__ import annotations

import heapq

from ..grid import Tile
from .base import AlgorithmVisualizer, DrawStep, PathfindingAlgorithm


class Dijkstra(PathfindingAlgorithm):
    def __init__(self) -> None:
        super().__init__("Dijkstra")

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

        distances = {tile: float('inf') for tile in grid.iter_tiles()}
        distances[start] = 0

        count = 0
        heap: list[tuple[float, int, Tile]] = [(0, count, start)]
        came_from: dict[Tile, Tile] = {}
        visited: set[Tile] = set()

        if visualiser:
            visualiser.reset()
            visualiser.record(start, g=0, f=0, label="start")
            visualiser.focus(start)
            visualiser.set_metric("frontier", 1)
            visualiser.set_metric("expanded", 0)
            visualiser.set_metric("steps", 0)

        while heap:
            current_distance, _, current = heapq.heappop(heap)

            if current in visited:
                continue
            visited.add(current)

            if visualiser:
                visualiser.focus(current)
                visualiser.record(current, g=current_distance, f=current_distance)
                visualiser.increment("expanded")
                visualiser.set_metric("frontier", len(heap))

            if current == end:
                success, _ = self._reconstruct_path(came_from, end, draw_step, visualiser)
                if not success:
                    return False
                end.make_end()
                if visualiser:
                    visualiser.focus(None)
                return True

            for neighbor in current.neighbors:
                distance = current_distance + 1
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    came_from[neighbor] = current
                    count += 1
                    heapq.heappush(heap, (distance, count, neighbor))
                    if not neighbor.is_end():
                        neighbor.make_open()
                    if visualiser:
                        visualiser.record(neighbor, g=distance, f=distance)
                        visualiser.set_metric("frontier", len(heap))

            if visualiser:
                visualiser.increment("steps")
            if not draw_step():
                return False

            if current != start:
                current.make_closed()

        return False


def create() -> Dijkstra:
    return Dijkstra()
