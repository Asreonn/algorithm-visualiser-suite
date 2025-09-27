"""Shared dataclasses describing animation state for greedy algorithms."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

NodeId = int
EdgeId = Tuple[NodeId, NodeId]


def normalize_edge(edge: Tuple[NodeId, NodeId]) -> EdgeId:
    """Return a normalised, direction-agnostic edge identifier."""
    a, b = edge
    return (a, b) if a <= b else (b, a)


@dataclass(frozen=True)
class QueueEntry:
    """Snapshot-friendly representation of a priority queue item."""

    sort_key: float
    payload: Tuple[NodeId, Optional[NodeId]]
    label: str


@dataclass
class GraphStep:
    """Atomic animation update for graph-based greedy algorithms."""

    active_node: Optional[NodeId]
    active_edge: Optional[EdgeId]
    visited_nodes: Set[NodeId] = field(default_factory=set)
    frontier_nodes: Set[NodeId] = field(default_factory=set)
    selected_edges: Set[EdgeId] = field(default_factory=set)
    candidate_edges: Set[EdgeId] = field(default_factory=set)
    queue_snapshot: Sequence[QueueEntry] = field(default_factory=tuple)
    distances: Dict[NodeId, float] = field(default_factory=dict)
    description: str = ""
    done: bool = False

    def clone_with(self, **updates: object) -> "GraphStep":
        """Return a shallow copy with certain attributes replaced."""
        data = {
            "active_node": self.active_node,
            "active_edge": self.active_edge,
            "visited_nodes": set(self.visited_nodes),
            "frontier_nodes": set(self.frontier_nodes),
            "selected_edges": set(self.selected_edges),
            "candidate_edges": set(self.candidate_edges),
            "queue_snapshot": list(self.queue_snapshot),
            "distances": dict(self.distances),
            "description": self.description,
            "done": self.done,
        }
        data.update(updates)
        data.setdefault("queue_snapshot", list(data["queue_snapshot"]))
        return GraphStep(**data)  # type: ignore[arg-type]


@dataclass
class SequenceStep:
    """Animation update for sequence-based greedy problems."""

    active_index: Optional[int]
    chosen_indices: List[int] = field(default_factory=list)
    discarded_indices: List[int] = field(default_factory=list)
    fractions: Dict[int, float] = field(default_factory=dict)
    progress_value: float = 0.0
    capacity_remaining: Optional[float] = None
    description: str = ""
    done: bool = False


@dataclass
class GraphDataset:
    """Graph structure used by greedy algorithms."""

    nodes: Set[NodeId]
    edges: Dict[NodeId, Dict[NodeId, float]]
    positions: Dict[NodeId, Tuple[float, float]] = field(default_factory=dict)

    def neighbours(self, node: NodeId) -> Iterable[Tuple[NodeId, float]]:
        for neighbour, weight in self.edges.get(node, {}).items():
            yield neighbour, weight

    def weight(self, start: NodeId, end: NodeId) -> float:
        return self.edges[start][end]

    def as_edge_list(self) -> List[Tuple[EdgeId, float]]:
        seen: Set[EdgeId] = set()
        results: List[Tuple[EdgeId, float]] = []
        for a, adjacency in self.edges.items():
            for b, weight in adjacency.items():
                edge = normalize_edge((a, b))
                if edge in seen:
                    continue
                seen.add(edge)
                results.append((edge, weight))
        return results


@dataclass
class SequenceDataset:
    """Container for ratio/value based greedy problems."""

    weights: List[float]
    values: List[float]
    durations: Optional[List[Tuple[int, int]]] = None

    def ratios(self) -> List[float]:
        return [v / w if w else 0.0 for v, w in zip(self.values, self.weights)]


def ensure_edge_order(edge: EdgeId) -> EdgeId:
    """Helper kept for backwards compatibility with earlier revisions."""
    return normalize_edge(edge)
