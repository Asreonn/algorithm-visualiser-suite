"""Sequence-based greedy algorithm generators."""
from __future__ import annotations

from typing import Dict, Iterator, List, Optional, Tuple

from greedy_viz.algorithms import (
    SequenceAlgorithmDefinition,
    SequenceAlgorithmFn,
    register_sequence_algorithm,
)
from greedy_viz.state import SequenceDataset, SequenceStep


def fractional_knapsack(dataset: SequenceDataset, capacity: Optional[float]) -> Iterator[SequenceStep]:
    if capacity is None:
        raise ValueError("Fractional knapsack requires a capacity value.")

    ratios = dataset.ratios()
    order = sorted(range(len(ratios)), key=lambda i: ratios[i], reverse=True)

    remaining = capacity
    chosen: Dict[int, float] = {}
    discarded: List[int] = []

    for index in order:
        weight = dataset.weights[index]
        value = dataset.values[index]
        if weight <= remaining:
            remaining -= weight
            chosen[index] = 1.0
            yield SequenceStep(
                active_index=index,
                chosen_indices=list(chosen.keys()),
                discarded_indices=discarded.copy(),
                fractions=dict(chosen),
                progress_value=(capacity - remaining) / capacity,
                capacity_remaining=remaining,
                description=(
                    f"Took item {index} fully (w={weight}, v={value}). Remaining capacity {remaining:.1f}."
                ),
            )
        else:
            fraction = remaining / weight if weight else 0.0
            if fraction > 0:
                chosen[index] = fraction
                remaining = 0.0
                yield SequenceStep(
                    active_index=index,
                    chosen_indices=list(chosen.keys()),
                    discarded_indices=discarded.copy(),
                    fractions=dict(chosen),
                    progress_value=1.0,
                    capacity_remaining=remaining,
                    description=(
                        f"Took {fraction:.2f} of item {index} (w={weight}, v={value}). Capacity filled."
                    ),
                    done=True,
                )
                return
            else:
                discarded.append(index)
                yield SequenceStep(
                    active_index=index,
                    chosen_indices=list(chosen.keys()),
                    discarded_indices=discarded.copy(),
                    fractions=dict(chosen),
                    progress_value=(capacity - remaining) / capacity,
                    capacity_remaining=remaining,
                    description=f"Skipped item {index}; no capacity remaining.",
                )
    yield SequenceStep(
        active_index=None,
        chosen_indices=list(chosen.keys()),
        discarded_indices=discarded,
        fractions=dict(chosen),
        progress_value=(capacity - remaining) / capacity if capacity else 1.0,
        capacity_remaining=remaining,
        description="Knapsack packed greedily.",
        done=True,
    )


def activity_selection(dataset: SequenceDataset, _: Optional[float]) -> Iterator[SequenceStep]:
    if not dataset.durations:
        raise ValueError("Activity selection dataset must include start/finish durations.")

    chosen: List[int] = []
    discarded: List[int] = []
    current_end = -1

    for index, (start, finish) in enumerate(dataset.durations):
        if start >= current_end:
            chosen.append(index)
            current_end = finish
            yield SequenceStep(
                active_index=index,
                chosen_indices=chosen.copy(),
                discarded_indices=discarded.copy(),
                fractions={idx: 1.0 for idx in chosen},
                progress_value=len(chosen) / len(dataset.durations),
                description=f"Scheduled activity {index} spanning [{start}, {finish}).",
            )
        else:
            discarded.append(index)
            yield SequenceStep(
                active_index=index,
                chosen_indices=chosen.copy(),
                discarded_indices=discarded.copy(),
                fractions={idx: 1.0 for idx in chosen},
                progress_value=len(chosen) / len(dataset.durations),
                description=f"Discarded activity {index}; overlaps with previous finish {current_end}.",
            )

    yield SequenceStep(
        active_index=None,
        chosen_indices=chosen,
        discarded_indices=discarded,
        fractions={idx: 1.0 for idx in chosen},
        progress_value=1.0,
        description="Activity selection completed.",
        done=True,
    )


register_sequence_algorithm(
    SequenceAlgorithmDefinition(
        key="fractional_knapsack",
        name="Fractional Knapsack",
        summary="Sort by value density and take items greedily, allowing partial picks.",
        runner=fractional_knapsack,
    )
)

register_sequence_algorithm(
    SequenceAlgorithmDefinition(
        key="activity_selection",
        name="Activity Selection",
        summary="Pick the maximum number of non-overlapping activities by finish time.",
        runner=activity_selection,
    )
)
