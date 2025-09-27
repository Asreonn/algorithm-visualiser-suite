"""Grid and tile primitives used by the pathfinding algorithms."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

import pygame as pg

from . import constants


@dataclass(eq=False)
class Tile:
    row: int
    col: int
    size: int
    total_rows: int
    color: tuple[int, int, int] = field(default=constants.TILE_EMPTY)

    def __post_init__(self) -> None:
        self.x = self.col * self.size
        self.y = self.row * self.size
        self.neighbors: list[Tile] = []

    # Convenience predicates -------------------------------------------------
    def is_start(self) -> bool:
        return self.color == constants.TILE_START

    def is_end(self) -> bool:
        return self.color == constants.TILE_END

    def is_barrier(self) -> bool:
        return self.color == constants.TILE_BARRIER

    def is_path(self) -> bool:
        return self.color == constants.TILE_PATH

    def is_closed(self) -> bool:
        return self.color == constants.TILE_CLOSED

    def is_open(self) -> bool:
        return self.color == constants.TILE_OPEN

    def reset(self) -> None:
        self.color = constants.TILE_EMPTY

    def reset_path_state(self) -> None:
        if self.is_open() or self.is_closed() or self.is_path():
            self.reset()

    # Mutators ----------------------------------------------------------------
    def make_start(self) -> None:
        self.color = constants.TILE_START

    def make_end(self) -> None:
        self.color = constants.TILE_END

    def make_barrier(self) -> None:
        self.color = constants.TILE_BARRIER

    def make_open(self) -> None:
        self.color = constants.TILE_OPEN

    def make_closed(self) -> None:
        self.color = constants.TILE_CLOSED

    def make_path(self) -> None:
        self.color = constants.TILE_PATH

    # Rendering ----------------------------------------------------------------
    def draw(self, surface: pg.Surface) -> None:
        pg.draw.rect(surface, self.color, (self.x, self.y, self.size, self.size))

    # Graph helpers -----------------------------------------------------------
    def update_neighbors(self, grid: 'Grid') -> None:  # type: ignore[name-defined]
        self.neighbors = []

        if self.row < self.total_rows - 1 and not grid[self.row + 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row + 1][self.col])

        if self.row > 0 and not grid[self.row - 1][self.col].is_barrier():
            self.neighbors.append(grid[self.row - 1][self.col])

        if self.col < self.total_rows - 1 and not grid[self.row][self.col + 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col + 1])

        if self.col > 0 and not grid[self.row][self.col - 1].is_barrier():
            self.neighbors.append(grid[self.row][self.col - 1])


class Grid:
    """Square grid abstraction that pairs tile logic with rendering helpers."""

    def __init__(self, rows: int, width: int) -> None:
        if rows <= 0:
            raise ValueError("rows must be positive")
        if width <= 0:
            raise ValueError("width must be positive")

        self.rows = rows
        self.width = width
        self.tile_size = width // rows
        self.tiles: list[list[Tile]] = [
            [Tile(row, col, self.tile_size, rows) for col in range(rows)]
            for row in range(rows)
        ]

    # Collection helpers ------------------------------------------------------
    def __getitem__(self, index: int) -> list[Tile]:
        return self.tiles[index]

    def __iter__(self) -> Iterator[list[Tile]]:
        return iter(self.tiles)

    def iter_tiles(self) -> Iterator[Tile]:
        for row in self.tiles:
            for tile in row:
                yield tile

    # Rendering ---------------------------------------------------------------
    def draw(self, surface: pg.Surface) -> None:
        for tile in self.iter_tiles():
            tile.draw(surface)
        self._draw_grid_lines(surface)

    def _draw_grid_lines(self, surface: pg.Surface) -> None:
        for i in range(self.rows):
            pg.draw.line(
                surface,
                constants.GRID_LINES,
                (0, i * self.tile_size),
                (self.width, i * self.tile_size),
            )
            pg.draw.line(
                surface,
                constants.GRID_LINES,
                (i * self.tile_size, 0),
                (i * self.tile_size, self.width),
            )

    # Manipulation ------------------------------------------------------------
    def clear(self) -> None:
        for tile in self.iter_tiles():
            tile.reset()

    def clear_path(self) -> None:
        for tile in self.iter_tiles():
            tile.reset_path_state()

    def update_neighbors(self) -> None:
        for tile in self.iter_tiles():
            tile.update_neighbors(self)

    def get_tile_from_pos(self, pos: tuple[int, int]) -> Optional[Tile]:
        x, y = pos
        row = y // self.tile_size
        col = x // self.tile_size

        if 0 <= row < self.rows and 0 <= col < self.rows:
            return self.tiles[row][col]
        return None
