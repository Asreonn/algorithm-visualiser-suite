"""Lightweight animation engine for stepping through greedy algorithm generators."""
from __future__ import annotations

from collections import deque
from typing import Deque, Generic, Iterator, List, Optional, TypeVar

TStep = TypeVar("TStep")


class AnimationEngine(Generic[TStep]):
    """Wraps a generator and exposes forward/backward stepping."""

    def __init__(self) -> None:
        self._generator: Optional[Iterator[TStep]] = None
        self._history: Deque[TStep] = deque()
        self._future: Deque[TStep] = deque()
        self._finished = False

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def history(self) -> List[TStep]:
        return list(self._history)

    def bind(self, generator: Iterator[TStep]) -> None:
        self._generator = generator
        self._history.clear()
        self._future.clear()
        self._finished = False

    def reset(self) -> None:
        self._generator = None
        self._history.clear()
        self._future.clear()
        self._finished = False

    def step_forward(self) -> Optional[TStep]:
        if self._future:
            step = self._future.pop()
            self._history.append(step)
            return step

        if self._generator is None or self._finished:
            return None

        try:
            step = next(self._generator)
        except StopIteration:
            self._finished = True
            return None

        self._history.append(step)
        if getattr(step, "done", False):
            self._finished = True
        return step

    def step_backward(self) -> Optional[TStep]:
        if not self._history:
            return None
        step = self._history.pop()
        self._future.append(step)
        if getattr(step, "done", False):
            self._finished = False
        return self._history[-1] if self._history else None

    def peek_current(self) -> Optional[TStep]:
        return self._history[-1] if self._history else None

    def has_future(self) -> bool:
        if self._future:
            return True
        if self._generator is None or self._finished:
            return False
        return True
