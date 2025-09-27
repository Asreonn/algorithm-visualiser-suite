"""Graph-focused greedy algorithms with step-by-step generators."""
from __future__ import annotations

import heapq
import math
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

from greedy_viz.algorithms import GraphAlgorithmDefinition, GraphAlgorithmFn, register_graph_algorithm
from greedy_viz.state import EdgeId, GraphDataset, GraphStep, NodeId, QueueEntry, normalize_edge


def _queue_snapshot(heap: List[Tuple[float, NodeId, NodeId]], *, label_fn) -> List[QueueEntry]:
    ordered = sorted(heap)
    return [QueueEntry(sort_key=weight, payload=(to, frm), label=label_fn(weight, frm, to)) for weight, frm, to in ordered]


def _build_step(
    *,
    visited: Set[NodeId],
    frontier: Set[NodeId],
    selected: Set[EdgeId],
    candidates: Set[EdgeId],
    heap: Iterable[Tuple[float, NodeId, NodeId]] = (),
    label_fn=None,
    distances: Optional[Dict[NodeId, float]] = None,
    active_node: Optional[NodeId] = None,
    active_edge: Optional[EdgeId] = None,
    description: str,
    done: bool = False,
) -> GraphStep:
    snapshot = []
    if heap and label_fn is not None:
        snapshot = _queue_snapshot(list(heap), label_fn=label_fn)
    return GraphStep(
        active_node=active_node,
        active_edge=active_edge,
        visited_nodes=set(visited),
        frontier_nodes=set(frontier),
        selected_edges=set(selected),
        candidate_edges=set(candidates),
        queue_snapshot=snapshot,
        distances=dict(distances or {}),
        description=description,
        done=done,
    )


def prim_mst(dataset: GraphDataset, start: NodeId, _: Optional[NodeId]) -> Iterator[GraphStep]:
    visited: Set[NodeId] = {start}
    selected: Set[EdgeId] = set()
    frontier: Set[NodeId] = set()
    candidates: Set[EdgeId] = set()
    heap: List[Tuple[float, NodeId, NodeId]] = []

    for neighbour, weight in dataset.neighbours(start):
        heapq.heappush(heap, (weight, start, neighbour))
        frontier.add(neighbour)
        candidates.add(normalize_edge((start, neighbour)))

    yield _build_step(
        visited=visited,
        frontier=frontier,
        selected=selected,
        candidates=candidates,
        heap=heap,
        label_fn=lambda w, frm, to: f"w={w:.1f} via {frm}",
        active_node=start,
        description=f"Initial frontier from node {start}.",
    )

    while heap:
        weight, frm, to = heapq.heappop(heap)
        edge = normalize_edge((frm, to))
        candidates.discard(edge)
        step = _build_step(
            visited=visited,
            frontier=frontier,
            selected=selected,
            candidates=candidates,
            heap=heap,
            label_fn=lambda w, f, t: f"w={w:.1f} via {f}",
            active_node=to,
            active_edge=edge,
            description=f"Considering edge {frm}-{to} (w={weight:.1f}).",
        )
        if to in visited:
            yield step.clone_with(description=f"Edge {frm}-{to} discarded; {to} already in tree.")
            continue

        visited.add(to)
        selected.add(edge)
        frontier.discard(to)

        yield step.clone_with(
            visited_nodes=set(visited),
            selected_edges=set(selected),
            frontier_nodes=set(frontier),
            description=f"Accepted edge {frm}-{to}; {to} joins the tree.",
        )

        for neighbour, neigh_weight in dataset.neighbours(to):
            if neighbour in visited:
                continue
            frontier.add(neighbour)
            next_edge = normalize_edge((to, neighbour))
            candidates.add(next_edge)
            heapq.heappush(heap, (neigh_weight, to, neighbour))
            yield _build_step(
                visited=visited,
                frontier=frontier,
                selected=selected,
                candidates=candidates,
                heap=heap,
                label_fn=lambda w, f, t: f"w={w:.1f} via {f}",
                active_node=neighbour,
                active_edge=next_edge,
                description=f"Queued candidate edge {to}-{neighbour} (w={neigh_weight:.1f}).",
            )

    yield _build_step(
        visited=visited,
        frontier=frontier,
        selected=selected,
        candidates=candidates,
        heap=[],
        label_fn=lambda *_: "",
        description="Prim's algorithm completed.",
        done=True,
    )


def kruskal_mst(dataset: GraphDataset, start: NodeId, _: Optional[NodeId]) -> Iterator[GraphStep]:
    parent: Dict[NodeId, NodeId] = {node: node for node in dataset.nodes}
    rank: Dict[NodeId, int] = {node: 0 for node in dataset.nodes}

    def find(node: NodeId) -> NodeId:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: NodeId, b: NodeId) -> bool:
        root_a = find(a)
        root_b = find(b)
        if root_a == root_b:
            return False
        if rank[root_a] < rank[root_b]:
            parent[root_a] = root_b
        elif rank[root_a] > rank[root_b]:
            parent[root_b] = root_a
        else:
            parent[root_b] = root_a
            rank[root_a] += 1
        return True

    edges = sorted(dataset.as_edge_list(), key=lambda item: item[1])
    selected: Set[EdgeId] = set()

    for edge, weight in edges:
        u, v = edge
        accepted = union(u, v)
        description = (
            f"Accepted edge {u}-{v} (w={weight:.1f})" if accepted else f"Skipped edge {u}-{v}; cycle detected."
        )
        if accepted:
            selected.add(edge)
        yield GraphStep(
            active_node=v,
            active_edge=edge,
            visited_nodes=set(),
            frontier_nodes=set(),
            selected_edges=set(selected),
            candidate_edges={normalize_edge(e[0]) for e in edges if normalize_edge(e[0]) not in selected},
            queue_snapshot=[
                QueueEntry(sort_key=w, payload=(a, b), label=f"{a}-{b} | w={w:.1f}") for (a, b), w in edges
            ],
            description=description,
        )

    yield GraphStep(
        active_node=None,
        active_edge=None,
        selected_edges=set(selected),
        candidate_edges=set(),
        queue_snapshot=[],
        description="Kruskal's algorithm completed.",
        done=True,
    )


def dijkstra_shortest_path(
    dataset: GraphDataset,
    start: NodeId,
    goal: Optional[NodeId],
) -> Iterator[GraphStep]:
    distances: Dict[NodeId, float] = {node: math.inf for node in dataset.nodes}
    distances[start] = 0.0
    previous: Dict[NodeId, Optional[NodeId]] = {node: None for node in dataset.nodes}
    visited: Set[NodeId] = set()
    heap: List[Tuple[float, NodeId, NodeId]] = [(0.0, start, start)]

    while heap:
        dist, frm, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        step = _build_step(
            visited=visited,
            frontier={n for _, _, n in heap if n not in visited},
            selected=_reconstruct_edges(previous, node),
            candidates=set(),
            heap=heap,
            label_fn=lambda d, f, t: f"d={d:.1f} via {f}",
            distances=distances,
            active_node=node,
            description=f"Visiting node {node} with distance {dist:.1f}.",
        )
        yield step

        if goal is not None and node == goal:
            yield step.clone_with(description=f"Reached goal {goal}.", done=True)
            return

        for neighbour, weight in dataset.neighbours(node):
            if neighbour in visited:
                continue
            new_distance = dist + weight
            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = node
                heapq.heappush(heap, (new_distance, node, neighbour))
                yield _build_step(
                    visited=visited,
                    frontier={n for _, _, n in heap if n not in visited},
                    selected=_reconstruct_edges(previous, neighbour),
                    candidates=set(),
                    heap=heap,
                    label_fn=lambda d, f, t: f"d={d:.1f} via {f}",
                    distances=distances,
                    active_node=neighbour,
                    active_edge=normalize_edge((node, neighbour)),
                    description=f"Updated {neighbour} distance to {new_distance:.1f} via {node}.",
                )

    yield GraphStep(
        active_node=None,
        active_edge=None,
        visited_nodes=visited,
        selected_edges=_reconstruct_edges(previous, goal) if goal is not None else set(),
        distances=distances,
        description="Dijkstra completed; goal unreachable." if goal is not None else "Dijkstra completed.",
        done=True,
    )


def _reconstruct_edges(previous: Dict[NodeId, Optional[NodeId]], node: Optional[NodeId]) -> Set[EdgeId]:
    path: Set[EdgeId] = set()
    while node is not None and previous.get(node) is not None:
        edge = normalize_edge((node, previous[node]))
        path.add(edge)
        node = previous[node]
    return path


def greedy_best_first(
    dataset: GraphDataset,
    start: NodeId,
    goal: Optional[NodeId],
) -> Iterator[GraphStep]:
    if goal is None:
        raise ValueError("Greedy Best-First Search requires a goal node.")

    positions = dataset.positions
    if start not in positions or goal not in positions:
        raise ValueError("Heuristic requires layout positions for nodes.")

    def heuristic(node: NodeId) -> float:
        ax, ay = positions[node]
        bx, by = positions[goal]
        return math.dist((ax, ay), (bx, by))

    heap: List[Tuple[float, NodeId, NodeId]] = [(heuristic(start), start, start)]
    visited: Set[NodeId] = set()
    previous: Dict[NodeId, Optional[NodeId]] = {start: None}

    while heap:
        h, frm, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        step = _build_step(
            visited=visited,
            frontier={n for _, _, n in heap if n not in visited},
            selected=_reconstruct_edges(previous, node),
            candidates=set(),
            heap=heap,
            label_fn=lambda priority, f, t: f"h={priority:.2f} via {f}",
            active_node=node,
            active_edge=normalize_edge((frm, node)),
            description=f"Expanding node {node} (h={h:.2f}).",
        )
        yield step

        if node == goal:
            yield step.clone_with(description=f"Reached goal {goal}.", done=True)
            return

        for neighbour, _weight in dataset.neighbours(node):
            if neighbour in visited:
                continue
            if neighbour not in previous:
                previous[neighbour] = node
            heapq.heappush(heap, (heuristic(neighbour), node, neighbour))
            yield _build_step(
                visited=visited,
                frontier={n for _, _, n in heap if n not in visited},
                selected=_reconstruct_edges(previous, neighbour),
                candidates=set(),
                heap=heap,
                label_fn=lambda priority, f, t: f"h={priority:.2f} via {f}",
                active_node=neighbour,
                active_edge=normalize_edge((node, neighbour)),
                description=f"Queued {neighbour} with heuristic {heuristic(neighbour):.2f}.",
            )

    yield GraphStep(
        active_node=None,
        active_edge=None,
        visited_nodes=visited,
        selected_edges=_reconstruct_edges(previous, goal),
        description="Greedy best-first search exhausted frontier without reaching goal.",
        done=True,
    )


register_graph_algorithm(
    GraphAlgorithmDefinition(
        key="prim",
        name="Prim MST",
        summary="Grow a minimum spanning tree by expanding the lightest frontier edge.",
        requires_goal=False,
        runner=prim_mst,
    )
)

register_graph_algorithm(
    GraphAlgorithmDefinition(
        key="kruskal",
        name="Kruskal MST",
        summary="Sort edges by weight and greedily add them unless they create a cycle.",
        requires_goal=False,
        runner=kruskal_mst,
    )
)

register_graph_algorithm(
    GraphAlgorithmDefinition(
        key="dijkstra",
        name="Dijkstra",
        summary="Shortest path using a priority queue of accumulated distances.",
        requires_goal=True,
        runner=dijkstra_shortest_path,
    )
)

register_graph_algorithm(
    GraphAlgorithmDefinition(
        key="greedy_bfs",
        name="Greedy Best-First",
        summary="Chase the goal using only heuristic distance guidance.",
        requires_goal=True,
        runner=greedy_best_first,
    )
)
