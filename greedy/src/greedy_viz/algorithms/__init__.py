"""Registry for greedy algorithm animations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional

from greedy_viz.state import GraphDataset, GraphStep, NodeId, SequenceDataset, SequenceStep

GraphAlgorithmFn = Callable[[GraphDataset, NodeId, Optional[NodeId]], Iterable[GraphStep]]
SequenceAlgorithmFn = Callable[[SequenceDataset, Optional[float]], Iterable[SequenceStep]]


@dataclass(frozen=True)
class GraphAlgorithmDefinition:
    key: str
    name: str
    summary: str
    requires_goal: bool
    runner: GraphAlgorithmFn


@dataclass(frozen=True)
class SequenceAlgorithmDefinition:
    key: str
    name: str
    summary: str
    runner: SequenceAlgorithmFn


_GRAPH_ALGORITHMS: Dict[str, GraphAlgorithmDefinition] = {}
_SEQUENCE_ALGORITHMS: Dict[str, SequenceAlgorithmDefinition] = {}


def register_graph_algorithm(definition: GraphAlgorithmDefinition) -> None:
    _GRAPH_ALGORITHMS[definition.key] = definition


def register_sequence_algorithm(definition: SequenceAlgorithmDefinition) -> None:
    _SEQUENCE_ALGORITHMS[definition.key] = definition


def graph_algorithms() -> List[GraphAlgorithmDefinition]:
    return list(_GRAPH_ALGORITHMS.values())


def sequence_algorithms() -> List[SequenceAlgorithmDefinition]:
    return list(_SEQUENCE_ALGORITHMS.values())


def get_graph_algorithm(key: str) -> GraphAlgorithmDefinition:
    return _GRAPH_ALGORITHMS[key]


def get_sequence_algorithm(key: str) -> SequenceAlgorithmDefinition:
    return _SEQUENCE_ALGORITHMS[key]
