"""Bidirectional breadth-first search for faster shortest paths."""
from __future__ import annotations

from collections import deque

from ..grid import Tile
from .base import AlgorithmVisualizer, DrawStep, PathfindingAlgorithm


class BidirectionalBreadthFirst(PathfindingAlgorithm):
    def __init__(self) -> None:
        super().__init__("Bidirectional BFS")

    def find_path(
        self,
        grid,
        start: Tile,
        end: Tile,
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None = None,
    ) -> bool:
        if start == end:
            return True

        grid.clear_path()
        grid.update_neighbors()

        frontier_start = deque([start])
        frontier_end = deque([end])

        parents_start: dict[Tile, Tile] = {}
        parents_end: dict[Tile, Tile] = {}

        visited_start: set[Tile] = {start}
        visited_end: set[Tile] = {end}

        depth_start: dict[Tile, int] = {start: 0}
        depth_end: dict[Tile, int] = {end: 0}

        if visualiser:
            visualiser.reset()
            visualiser.record(start, depth=0, label="start")
            visualiser.record(end, depth=0, label="goal")
            visualiser.focus(start)
            visualiser.set_metric("frontier", len(frontier_start) + len(frontier_end))
            visualiser.set_metric("expanded", 0)
            visualiser.set_metric("steps", 0)

        while frontier_start and frontier_end:
            meet, halted = self._expand_layer(
                frontier_start,
                visited_start,
                parents_start,
                depth_start,
                visited_end,
                draw_step,
                visualiser,
            )
            if halted:
                return False
            if meet:
                return self._reconstruct_bidirectional(
                    parents_start,
                    parents_end,
                    meet,
                    start,
                    end,
                    draw_step,
                    visualiser,
                )

            if visualiser:
                visualiser.set_metric("frontier", len(frontier_start) + len(frontier_end))

            meet, halted = self._expand_layer(
                frontier_end,
                visited_end,
                parents_end,
                depth_end,
                visited_start,
                draw_step,
                visualiser,
            )
            if halted:
                return False
            if meet:
                return self._reconstruct_bidirectional(
                    parents_start,
                    parents_end,
                    meet,
                    start,
                    end,
                    draw_step,
                    visualiser,
                )

            if visualiser:
                visualiser.set_metric("frontier", len(frontier_start) + len(frontier_end))

        return False

    def _expand_layer(
        self,
        frontier: deque[Tile],
        visited_self: set[Tile],
        parents_self: dict[Tile, Tile],
        depth_map: dict[Tile, int],
        visited_other: set[Tile],
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None,
    ) -> tuple[Tile | None, bool]:
        if not frontier:
            return None, False

        current = frontier.popleft()

        if visualiser:
            visualiser.focus(current)
            visualiser.record(current, depth=depth_map[current])
            visualiser.increment("expanded")

        found: Tile | None = None
        for neighbor in current.neighbors:
            if neighbor.is_barrier():
                continue

            if neighbor not in visited_self:
                visited_self.add(neighbor)
                parents_self[neighbor] = current
                depth_map[neighbor] = depth_map[current] + 1
                frontier.append(neighbor)
                if not neighbor.is_start() and not neighbor.is_end():
                    neighbor.make_open()
                if visualiser:
                    visualiser.record(neighbor, depth=depth_map[neighbor])

            if neighbor in visited_other:
                parents_self[neighbor] = current
                found = neighbor
                break

        if visualiser:
            visualiser.increment("steps")
        if not draw_step():
            return None, True

        if not current.is_start() and not current.is_end():
            current.make_closed()

        return found, False

    def _reconstruct_bidirectional(
        self,
        parents_start: dict[Tile, Tile],
        parents_end: dict[Tile, Tile],
        meet: Tile,
        start: Tile,
        end: Tile,
        draw_step: DrawStep,
        visualiser: AlgorithmVisualizer | None,
    ) -> bool:
        path_forward = self._path_to_root(meet, parents_start, start, reverse=False)
        path_backward = self._path_to_root(meet, parents_end, end, reverse=True)

        full_path = path_forward + path_backward[1:]
        length = len(full_path) - 1

        if visualiser:
            visualiser.set_metric("path", length)
            visualiser.focus(None)

        for tile in full_path:
            if tile not in {start, end}:
                tile.make_path()
            if not draw_step():
                return False

        end.make_end()
        start.make_start()

        return True

    def _path_to_root(
        self,
        meet: Tile,
        parents: dict[Tile, Tile],
        terminal: Tile,
        reverse: bool,
    ) -> list[Tile]:
        path = [meet]
        current = meet
        while current != terminal and current in parents:
            current = parents[current]
            if reverse:
                path.append(current)
            else:
                path.insert(0, current)

        if reverse:
            if path[-1] != terminal:
                path.append(terminal)
        else:
            if path[0] != terminal:
                path.insert(0, terminal)

        return path
