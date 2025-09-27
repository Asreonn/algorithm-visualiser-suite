"""Utility builders for graphs and sequences used by greedy animations."""
from __future__ import annotations

import itertools
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from greedy_viz.config import GRAPH_CONFIG, SEQUENCE_CONFIG
from greedy_viz.state import EdgeId, GraphDataset, NodeId, SequenceDataset, normalize_edge


@dataclass
class GraphGenerationOptions:
    node_count: Optional[int] = None
    weight_range: Optional[Tuple[int, int]] = None
    kind: str = "random"
    seed: Optional[int] = None


class GraphBuilder:
    """Factory for creating weighted undirected graphs."""

    def __init__(self, *, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()

    def build(self, options: GraphGenerationOptions) -> GraphDataset:
        kind = options.kind
        if kind == "grid":
            return self._grid_graph(options)
        if kind == "complete":
            return self._complete_graph(options)
        return self._random_graph(options)

    def _random_graph(self, options: GraphGenerationOptions) -> GraphDataset:
        node_count = options.node_count or GRAPH_CONFIG.default_node_count
        weight_range = options.weight_range or (GRAPH_CONFIG.min_weight, GRAPH_CONFIG.max_weight)
        nodes = set(range(node_count))
        edges: Dict[NodeId, Dict[NodeId, float]] = {n: {} for n in nodes}
        positions: Dict[NodeId, Tuple[float, float]] = {}

        for idx, node in enumerate(sorted(nodes)):
            angle = (2 * math.pi * idx) / max(len(nodes), 1)
            radius = 0.4 + 0.18 * self.rng.random()
            positions[node] = (
                0.5 + radius * math.cos(angle),
                0.5 + radius * math.sin(angle),
            )

        for a, b in itertools.combinations(nodes, 2):
            if self.rng.random() < 0.45:  # sparse-ish graph
                weight = self.rng.randint(*weight_range)
                edges[a][b] = float(weight)
                edges[b][a] = float(weight)

        # ensure connectivity via spanning tree
        unordered = list(nodes)
        self.rng.shuffle(unordered)
        for idx in range(1, len(unordered)):
            a = unordered[idx - 1]
            b = unordered[idx]
            if b not in edges[a]:
                weight = self.rng.randint(*weight_range)
                edges[a][b] = float(weight)
                edges[b][a] = float(weight)

        return GraphDataset(nodes=nodes, edges=edges, positions=positions)

    def _complete_graph(self, options: GraphGenerationOptions) -> GraphDataset:
        node_count = options.node_count or max(GRAPH_CONFIG.min_node_count, 8)
        weight_range = options.weight_range or (GRAPH_CONFIG.min_weight, GRAPH_CONFIG.max_weight)
        nodes = set(range(node_count))
        edges: Dict[NodeId, Dict[NodeId, float]] = {n: {} for n in nodes}
        positions: Dict[NodeId, Tuple[float, float]] = {}
        for idx, node in enumerate(sorted(nodes)):
            angle = (2 * math.pi * idx) / max(len(nodes), 1)
            positions[node] = (
                0.5 + 0.42 * math.cos(angle),
                0.5 + 0.42 * math.sin(angle),
            )
        for a, b in itertools.combinations(nodes, 2):
            weight = self.rng.randint(*weight_range)
            edges[a][b] = float(weight)
            edges[b][a] = float(weight)
        return GraphDataset(nodes=nodes, edges=edges, positions=positions)

    def _grid_graph(self, options: GraphGenerationOptions) -> GraphDataset:
        rows = GRAPH_CONFIG.grid_rows
        cols = GRAPH_CONFIG.grid_cols
        weight_range = options.weight_range or (GRAPH_CONFIG.min_weight, GRAPH_CONFIG.max_weight)
        nodes: Set[NodeId] = set()
        edges: Dict[NodeId, Dict[NodeId, float]] = {}
        positions: Dict[NodeId, Tuple[float, float]] = {}

        for r in range(rows):
            for c in range(cols):
                node_id = r * cols + c
                nodes.add(node_id)
                edges[node_id] = {}
                positions[node_id] = (
                    (c + 0.5) / max(cols, 1),
                    (r + 0.5) / max(rows, 1),
                )

        def _connect(a: NodeId, b: NodeId) -> None:
            weight = self.rng.randint(*weight_range)
            edges[a][b] = float(weight)
            edges[b][a] = float(weight)

        for r in range(rows):
            for c in range(cols):
                node = r * cols + c
                if c + 1 < cols:
                    _connect(node, r * cols + (c + 1))
                if r + 1 < rows:
                    _connect(node, (r + 1) * cols + c)

        return GraphDataset(nodes=nodes, edges=edges, positions=positions)


@dataclass
class SequenceGenerationOptions:
    item_count: Optional[int] = None
    seed: Optional[int] = None
    capacity: Optional[int] = None


class SequenceBuilder:
    """Factory for crafting item/value datasets for greedy demos."""

    def __init__(self, *, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()

    def build_knapsack(self, options: SequenceGenerationOptions) -> Tuple[SequenceDataset, float]:
        item_count = options.item_count or max(SEQUENCE_CONFIG.min_items, 7)
        values: List[int] = []
        weights: List[int] = []
        for _ in range(item_count):
            weights.append(self.rng.randint(*SEQUENCE_CONFIG.weight_range))
            values.append(self.rng.randint(*SEQUENCE_CONFIG.value_range))
        capacity = float(options.capacity or SEQUENCE_CONFIG.capacity_default)
        return SequenceDataset(weights=weights, values=values), capacity

    def build_activity_selection(self, options: SequenceGenerationOptions) -> SequenceDataset:
        item_count = options.item_count or max(SEQUENCE_CONFIG.min_items, 8)
        slots: List[Tuple[int, int]] = []
        start = 0
        for _ in range(item_count):
            duration = self.rng.randint(1, 6)
            gap = self.rng.randint(0, 3)
            begin = start + gap
            end = begin + duration
            slots.append((begin, end))
            start = begin
        slots.sort(key=lambda s: (s[1], s[0]))
        weights = [1.0 for _ in slots]
        values = [1.0 for _ in slots]
        return SequenceDataset(weights=weights, values=values, durations=slots)


def build_graph(options: GraphGenerationOptions, *, rng: Optional[random.Random] = None) -> GraphDataset:
    builder = GraphBuilder(rng=rng)
    return builder.build(options)


def build_knapsack_dataset(options: SequenceGenerationOptions, *, rng: Optional[random.Random] = None) -> Tuple[SequenceDataset, float]:
    builder = SequenceBuilder(rng=rng)
    return builder.build_knapsack(options)


def build_activity_dataset(options: SequenceGenerationOptions, *, rng: Optional[random.Random] = None) -> SequenceDataset:
    builder = SequenceBuilder(rng=rng)
    return builder.build_activity_selection(options)


def heuristic_distance(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    """Euclidean distance helper for grid heuristics."""
    return math.dist(a, b)
