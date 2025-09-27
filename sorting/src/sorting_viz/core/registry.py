"""Algorithm registry used by the UI layer."""
from __future__ import annotations

from typing import List

from .algorithms import shell_registry
from .types import AlgorithmDefinition, AlgorithmRegistry


_ALGORITHMS: AlgorithmRegistry = {definition.name: definition for definition in shell_registry()}


def algorithm_names() -> List[str]:
    return list(_ALGORITHMS.keys())


def get_algorithm(name: str) -> AlgorithmDefinition:
    try:
        return _ALGORITHMS[name]
    except KeyError as exc:
        available = ", ".join(_ALGORITHMS)
        raise ValueError(f"Unknown algorithm: {name}. Options: {available}") from exc


def algorithms() -> AlgorithmRegistry:
    return dict(_ALGORITHMS)
