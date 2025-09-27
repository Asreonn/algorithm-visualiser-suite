"""Core typing primitives for the sorting visualizer."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Generator, List, Optional, Tuple


class StepType(str, Enum):
    """Enumerates the primitive operations that can be visualised."""

    COMPARE = "compare"
    SWAP = "swap"
    OVERWRITE = "overwrite"
    HIGHLIGHT = "highlight"
    MARK_FINAL = "mark_final"
    MARK_RANGE = "mark_range"


class StepRole(str, Enum):
    """Describes how an index participates in a visual step."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    TARGET = "target"
    RANGE_START = "range_start"
    RANGE_END = "range_end"
    AUXILIARY = "auxiliary"


@dataclass(frozen=True)
class Step:
    """Immutable instruction emitted by an algorithm for visualisation."""

    action: StepType
    indices: Tuple[int, ...] = ()
    values: Tuple[int, ...] = ()
    roles: Tuple[StepRole, ...] = ()
    label: Optional[str] = None
    message: Optional[str] = None

    def role_map(self) -> Dict[int, StepRole]:
        """Map index → role for convenience."""

        return {
            index: (self.roles[idx] if idx < len(self.roles) else StepRole.PRIMARY)
            for idx, index in enumerate(self.indices)
        }


StepGenerator = Generator[Step, None, None]


@dataclass(frozen=True)
class AlgorithmDefinition:
    """Metadata wrapper describing a registered sorting algorithm."""

    name: str
    generator: Callable[[List[int]], StepGenerator]
    description: str
    is_stable: bool
    time_complexity: str
    space_complexity: str


AlgorithmRegistry = Dict[str, AlgorithmDefinition]
