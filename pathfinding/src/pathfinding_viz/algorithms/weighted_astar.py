"""Weighted A* variant that multiples the heuristic by a constant factor."""
from __future__ import annotations

import heapq

from ..grid import Tile
from .astar import manhattan
from .base import AlgorithmVisualizer, DrawStep, PathfindingAlgorithm


class WeightedAStar(PathfindingAlgorithm):
    def __init__(self, weight: float = 1.5) -> None:
        super().__init__(f"Weighted A* (w={weight})")
        if weight <= 0:
            raise ValueError("weight must be positive")
        self.weight = weight

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
            h_start = manhattan(start, end)
            visualiser.record(start, g=0, h=h_start, f=h_start * self.weight, label="start")
            visualiser.focus(start)
            visualiser.set_metric("frontier", 1)
            visualiser.set_metric("expanded", 0)
            visualiser.set_metric("steps", 0)

        count = 0
        open_heap: list[tuple[float, int, Tile]] = []
        heapq.heappush(open_heap, (0.0, count, start))
        came_from: dict[Tile, Tile] = {}

        g_score = {tile: float('inf') for tile in grid.iter_tiles()}
        g_score[start] = 0.0

        f_score = {tile: float('inf') for tile in grid.iter_tiles()}
        f_score[start] = manhattan(start, end) * self.weight

        open_set = {start}
        processed: set[Tile] = set()

        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            open_set.discard(current)

            if current in processed:
                continue
            processed.add(current)

            if visualiser:
                h_val = manhattan(current, end)
                visualiser.focus(current)
                visualiser.record(
                    current,
                    g=g_score[current],
                    h=h_val,
                    f=g_score[current] + h_val * self.weight,
                )
                visualiser.increment("expanded")
                visualiser.set_metric("frontier", len(open_set))

            if current == end:
                success, _ = self._reconstruct_path(came_from, end, draw_step, visualiser)
                if not success:
                    return False
                end.make_end()
                if visualiser:
                    visualiser.focus(None)
                return True

            for neighbor in current.neighbors:
                tentative_g = g_score[current] + 1

                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    heuristic = manhattan(neighbor, end)
                    f_score[neighbor] = tentative_g + heuristic * self.weight

                    if neighbor not in open_set:
                        count += 1
                        heapq.heappush(open_heap, (f_score[neighbor], count, neighbor))
                        open_set.add(neighbor)
                        if not neighbor.is_end():
                            neighbor.make_open()
                    if visualiser:
                        visualiser.record(
                            neighbor,
                            g=g_score[neighbor],
                            h=heuristic,
                            f=f_score[neighbor],
                        )
                        visualiser.set_metric("frontier", len(open_set))

            if visualiser:
                visualiser.increment("steps")
            if not draw_step():
                return False

            if current != start:
                current.make_closed()

        return False


def create(weight: float = 1.5) -> WeightedAStar:
    return WeightedAStar(weight=weight)
