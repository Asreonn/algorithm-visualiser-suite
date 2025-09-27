"""Library of sorting algorithms implemented as generator pipelines."""
from __future__ import annotations

from typing import Iterable, List

from .types import AlgorithmDefinition, Step, StepGenerator, StepRole, StepType


def _mark_final(length: int, message: str = "Sorting complete") -> Iterable[Step]:
    if length == 0:
        return
    roles = tuple(StepRole.PRIMARY for _ in range(length))
    yield Step(StepType.MARK_FINAL, tuple(range(length)), roles=roles, message=message)


def _highlight_range(start: int, end: int, label: str) -> Step:
    return Step(
        StepType.MARK_RANGE,
        (start, end),
        roles=(StepRole.RANGE_START, StepRole.RANGE_END),
        label=label,
    )


# ---------------------------------------------------------------------------
# Comparison-based algorithms
# ---------------------------------------------------------------------------

def bubble_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            yield Step(
                StepType.COMPARE,
                (j, j + 1),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message=f"Comparing {data[j]} and {data[j + 1]}",
            )
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                swapped = True
                yield Step(
                    StepType.SWAP,
                    (j, j + 1),
                    values=(data[j], data[j + 1]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Swapping adjacent elements",
                )
        yield Step(
            StepType.MARK_FINAL,
            (n - i - 1,),
            roles=(StepRole.PRIMARY,),
            message="Element locked at correct position",
        )
        if not swapped:
            break
    yield from _mark_final(n)


def cocktail_shaker_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    start = 0
    end = n - 1
    swapped = True
    while swapped:
        swapped = False
        for i in range(start, end):
            yield Step(
                StepType.COMPARE,
                (i, i + 1),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Forward scan comparison",
            )
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
                yield Step(
                    StepType.SWAP,
                    (i, i + 1),
                    values=(data[i], data[i + 1]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Swap while scanning forward",
                )
        if not swapped:
            break
        yield Step(
            StepType.MARK_FINAL,
            (end,),
            roles=(StepRole.PRIMARY,),
            message="Right boundary locked",
        )
        swapped = False
        end -= 1
        for i in range(end, start, -1):
            yield Step(
                StepType.COMPARE,
                (i - 1, i),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Backward scan comparison",
            )
            if data[i - 1] > data[i]:
                data[i], data[i - 1] = data[i - 1], data[i]
                swapped = True
                yield Step(
                    StepType.SWAP,
                    (i - 1, i),
                    values=(data[i - 1], data[i]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Swap while scanning backward",
                )
        yield Step(
            StepType.MARK_FINAL,
            (start,),
            roles=(StepRole.PRIMARY,),
            message="Left boundary locked",
        )
        start += 1
    yield from _mark_final(n)


def insertion_sort(data: List[int]) -> StepGenerator:
    for i in range(1, len(data)):
        key = data[i]
        yield Step(
            StepType.HIGHLIGHT,
            (i,),
            values=(key,),
            roles=(StepRole.PRIMARY,),
            label="key",
            message=f"Insert {key} into its position",
        )
        j = i - 1
        while j >= 0 and data[j] > key:
            yield Step(
                StepType.COMPARE,
                (j, j + 1),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Left element larger, shifting right",
            )
            data[j + 1] = data[j]
            yield Step(
                StepType.OVERWRITE,
                (j + 1,),
                values=(data[j + 1],),
                roles=(StepRole.TARGET,),
                message="Element shifted right",
            )
            j -= 1
        data[j + 1] = key
        yield Step(
            StepType.OVERWRITE,
            (j + 1,),
            values=(key,),
            roles=(StepRole.TARGET,),
            message="Key inserted into new position",
        )
    yield from _mark_final(len(data))


def selection_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    for i in range(n):
        min_index = i
        yield Step(
            StepType.HIGHLIGHT,
            (i,),
            values=(data[i],),
            roles=(StepRole.PRIMARY,),
            label="min",
            message="Scanning for next minimum",
        )
        for j in range(i + 1, n):
            yield Step(
                StepType.COMPARE,
                (min_index, j),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Checking candidate for smaller value",
            )
            if data[j] < data[min_index]:
                min_index = j
                yield Step(
                    StepType.HIGHLIGHT,
                    (min_index,),
                    values=(data[min_index],),
                    roles=(StepRole.PRIMARY,),
                    label="min",
                    message="New minimum found",
                )
        if min_index != i:
            data[i], data[min_index] = data[min_index], data[i]
            yield Step(
                StepType.SWAP,
                (i, min_index),
                values=(data[i], data[min_index]),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Swap with current minimum",
            )
        yield Step(
            StepType.MARK_FINAL,
            (i,),
            roles=(StepRole.PRIMARY,),
            message="Position locked",
        )
    yield from _mark_final(n)


def gnome_sort(data: List[int]) -> StepGenerator:
    index = 0
    n = len(data)
    while index < n:
        if index == 0:
            index += 1
            continue
        yield Step(
            StepType.COMPARE,
            (index - 1, index),
            roles=(StepRole.PRIMARY, StepRole.SECONDARY),
            message="Checking next pair",
        )
        if data[index] >= data[index - 1]:
            index += 1
        else:
            data[index], data[index - 1] = data[index - 1], data[index]
            yield Step(
                StepType.SWAP,
                (index - 1, index),
                values=(data[index - 1], data[index]),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Swap and step backward",
            )
            index -= 1
    yield from _mark_final(n)


def comb_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    gap = n
    shrink = 1.3
    sorted_flag = False
    while not sorted_flag:
        gap = int(gap / shrink)
        if gap <= 1:
            gap = 1
            sorted_flag = True
        index = 0
        while index + gap < n:
            j = index + gap
            yield Step(
                StepType.COMPARE,
                (index, j),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message=f"Gap comparison (gap={gap})",
            )
            if data[index] > data[j]:
                data[index], data[j] = data[j], data[index]
                sorted_flag = False
                yield Step(
                    StepType.SWAP,
                    (index, j),
                    values=(data[index], data[j]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Gap swap",
                )
            index += 1
    yield from _mark_final(n)


def odd_even_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    if n <= 1:
        yield from _mark_final(n)
        return

    is_sorted = False
    iteration = 0
    while not is_sorted:
        is_sorted = True
        yield Step(
            StepType.HIGHLIGHT,
            (),
            label="phase",
            message=f"Starting iteration {iteration}",
        )

        for i in range(1, n - 1, 2):
            yield Step(
                StepType.COMPARE,
                (i, i + 1),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Odd phase comparison",
            )
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                is_sorted = False
                yield Step(
                    StepType.SWAP,
                    (i, i + 1),
                    values=(data[i], data[i + 1]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Odd phase swap",
                )

        for i in range(0, n - 1, 2):
            yield Step(
                StepType.COMPARE,
                (i, i + 1),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Even phase comparison",
            )
            if data[i] > data[i + 1]:
                data[i], data[i + 1] = data[i + 1], data[i]
                is_sorted = False
                yield Step(
                    StepType.SWAP,
                    (i, i + 1),
                    values=(data[i], data[i + 1]),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Even phase swap",
                )

        iteration += 1

    yield from _mark_final(n)


def shell_sort(data: List[int]) -> StepGenerator:
    n = len(data)
    gap = n // 2
    while gap > 0:
        yield _highlight_range(0, n - 1, f"Gap={gap}")
        for i in range(gap, n):
            temp = data[i]
            j = i
            while j >= gap and data[j - gap] > temp:
                yield Step(
                    StepType.COMPARE,
                    (j - gap, j),
                    roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                    message="Gap comparison",
                )
                data[j] = data[j - gap]
                yield Step(
                    StepType.OVERWRITE,
                    (j,),
                    values=(data[j],),
                    roles=(StepRole.TARGET,),
                    message="Element shifted by gap",
                )
                j -= gap
            data[j] = temp
            yield Step(
                StepType.OVERWRITE,
                (j,),
                values=(temp,),
                roles=(StepRole.TARGET,),
                message="Insertion within gap",
            )
        gap //= 2
    yield from _mark_final(n)


# ---------------------------------------------------------------------------
# Divide & conquer algorithms
# ---------------------------------------------------------------------------

def merge_sort(data: List[int]) -> StepGenerator:
    def merge(left: int, mid: int, right: int) -> StepGenerator:
        left_copy = data[left : mid + 1]
        right_copy = data[mid + 1 : right + 1]
        i = j = 0
        k = left
        yield _highlight_range(left, right, "Merge")
        while i < len(left_copy) and j < len(right_copy):
            yield Step(
                StepType.COMPARE,
                (left + i, mid + 1 + j),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Comparing left and right halves",
            )
            if left_copy[i] <= right_copy[j]:
                data[k] = left_copy[i]
                yield Step(
                    StepType.OVERWRITE,
                    (k,),
                    values=(left_copy[i],),
                    roles=(StepRole.TARGET,),
                    message="Copy from left half",
                )
                i += 1
            else:
                data[k] = right_copy[j]
                yield Step(
                    StepType.OVERWRITE,
                    (k,),
                    values=(right_copy[j],),
                    roles=(StepRole.TARGET,),
                    message="Copy from right half",
                )
                j += 1
            k += 1
        while i < len(left_copy):
            data[k] = left_copy[i]
            yield Step(
                StepType.OVERWRITE,
                (k,),
                values=(left_copy[i],),
                roles=(StepRole.TARGET,),
                message="Copy remaining left value",
            )
            i += 1
            k += 1
        while j < len(right_copy):
            data[k] = right_copy[j]
            yield Step(
                StepType.OVERWRITE,
                (k,),
                values=(right_copy[j],),
                roles=(StepRole.TARGET,),
                message="Copy remaining right value",
            )
            j += 1
            k += 1

    def sort(left: int, right: int) -> StepGenerator:
        if left >= right:
            return
        mid = (left + right) // 2
        yield from sort(left, mid)
        yield from sort(mid + 1, right)
        yield from merge(left, mid, right)

    if data:
        yield from sort(0, len(data) - 1)
        yield from _mark_final(len(data))


def quick_sort(data: List[int]) -> StepGenerator:
    def partition(low: int, high: int) -> StepGenerator:
        pivot = data[high]
        yield Step(
            StepType.HIGHLIGHT,
            (high,),
            values=(pivot,),
            roles=(StepRole.PRIMARY,),
            label="pivot",
            message=f"Pivot = {pivot}",
        )
        i = low
        for j in range(low, high):
            yield Step(
                StepType.COMPARE,
                (j, high),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Compare with pivot",
            )
            if data[j] <= pivot:
                if i != j:
                    data[i], data[j] = data[j], data[i]
                    yield Step(
                        StepType.SWAP,
                        (i, j),
                        values=(data[i], data[j]),
                        roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                        message="Move element to pivot's left",
                    )
                i += 1
        data[i], data[high] = data[high], data[i]
        yield Step(
            StepType.SWAP,
            (i, high),
            values=(data[i], data[high]),
            roles=(StepRole.PRIMARY, StepRole.SECONDARY),
            message="Pivot moved into position",
        )
        yield Step(
            StepType.MARK_FINAL,
            (i,),
            roles=(StepRole.PRIMARY,),
            message="Pivot locked",
        )
        return i

    def sort(low: int, high: int) -> StepGenerator:
        if low < high:
            pivot_index = yield from partition(low, high)
            yield from sort(low, pivot_index - 1)
            yield from sort(pivot_index + 1, high)

    if data:
        yield from sort(0, len(data) - 1)
        yield from _mark_final(len(data))


def heap_sort(data: List[int]) -> StepGenerator:
    def heapify(size: int, root: int) -> StepGenerator:
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2
        if left < size:
            yield Step(
                StepType.COMPARE,
                (left, largest),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Compare left child",
            )
            if data[left] > data[largest]:
                largest = left
        if right < size:
            yield Step(
                StepType.COMPARE,
                (right, largest),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Compare right child",
            )
            if data[right] > data[largest]:
                largest = right
        if largest != root:
            data[root], data[largest] = data[largest], data[root]
            yield Step(
                StepType.SWAP,
                (root, largest),
                values=(data[root], data[largest]),
                roles=(StepRole.PRIMARY, StepRole.SECONDARY),
                message="Swap root with larger child",
            )
            yield from heapify(size, largest)

    n = len(data)
    for i in range(n // 2 - 1, -1, -1):
        yield from heapify(n, i)
    for end in range(n - 1, 0, -1):
        data[0], data[end] = data[end], data[0]
        yield Step(
            StepType.SWAP,
            (0, end),
            values=(data[0], data[end]),
            roles=(StepRole.PRIMARY, StepRole.SECONDARY),
            message="Move max element to end",
        )
        yield Step(
            StepType.MARK_FINAL,
            (end,),
            roles=(StepRole.PRIMARY,),
            message="Element locked",
        )
        yield from heapify(end, 0)
    yield Step(
        StepType.MARK_FINAL,
        (0,),
        roles=(StepRole.PRIMARY,),
        message="Final element locked",
    )


# ---------------------------------------------------------------------------
# Non-comparison algorithms
# ---------------------------------------------------------------------------

def counting_sort(data: List[int]) -> StepGenerator:
    if not data:
        return
    min_value = min(data)
    max_value = max(data)
    range_size = max_value - min_value + 1
    count = [0] * range_size
    output = [0] * len(data)
    for index, value in enumerate(data):
        bucket = value - min_value
        count[bucket] += 1
        yield Step(
            StepType.HIGHLIGHT,
            (index,),
            values=(value,),
            roles=(StepRole.PRIMARY,),
            label="count",
            message=f"Increment counter for {value}",
        )
    for i in range(1, len(count)):
        count[i] += count[i - 1]
    for index in range(len(data) - 1, -1, -1):
        value = data[index]
        bucket = value - min_value
        count[bucket] -= 1
        position = count[bucket]
        output[position] = value
        yield Step(
            StepType.HIGHLIGHT,
            (index, position),
            values=(value, value),
            roles=(StepRole.PRIMARY, StepRole.SECONDARY),
            label="place",
            message=f"Move {value} from index {index} to position {position}",
        )
        yield Step(
            StepType.OVERWRITE,
            (position,),
            values=(value,),
            roles=(StepRole.TARGET,),
            message=f"Place {value} into output array",
        )
    for i, value in enumerate(output):
        data[i] = value
        yield Step(
            StepType.OVERWRITE,
            (i,),
            values=(value,),
            roles=(StepRole.TARGET,),
            message="Copy output back into array",
        )
        yield Step(
            StepType.MARK_FINAL,
            (i,),
            roles=(StepRole.PRIMARY,),
            message=f"Position {i} locked",
        )


def radix_sort(data: List[int]) -> StepGenerator:
    if not data:
        return
    max_value = max(data)
    exp = 1
    while max_value // exp > 0:
        buckets = [[] for _ in range(10)]
        yield Step(
            StepType.HIGHLIGHT,
            (),
            label="digit",
            message=f"Processing digit place {exp}",
        )
        for index, value in enumerate(data):
            digit = (value // exp) % 10
            buckets[digit].append(value)
            yield Step(
                StepType.HIGHLIGHT,
                (index,),
                values=(value,),
                roles=(StepRole.PRIMARY,),
                label=f"d{digit}",
                message=f"Bucket {digit} collects value {value}",
            )
        i = 0
        for digit, bucket in enumerate(buckets):
            for value in bucket:
                data[i] = value
                yield Step(
                    StepType.OVERWRITE,
                    (i,),
                    values=(value,),
                    roles=(StepRole.TARGET,),
                    message=f"Write {value} from bucket {digit}",
                )
                i += 1
        exp *= 10
    yield from _mark_final(len(data))


def shell_registry() -> List[AlgorithmDefinition]:
    return [
        AlgorithmDefinition(
            name="Bubble Sort",
            generator=bubble_sort,
            description="Adaptive comparison sort that bubbles the largest element to the end each pass.",
            is_stable=True,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Cocktail Shaker",
            generator=cocktail_shaker_sort,
            description="Bidirectional variant of bubble sort that pushes large and small values toward opposite ends.",
            is_stable=True,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Insertion Sort",
            generator=insertion_sort,
            description="Stable insertion-based method that excels on nearly sorted data by placing keys directly.",
            is_stable=True,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Selection Sort",
            generator=selection_sort,
            description="Simple, unstable routine that repeatedly selects the minimum and swaps it into place.",
            is_stable=False,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Gnome Sort",
            generator=gnome_sort,
            description="Heuristic that walks forward and steps back whenever neighbouring elements are out of order.",
            is_stable=False,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Comb Sort",
            generator=comb_sort,
            description="Bubble-sort derivative that shrinks a gap size to eliminate distant inversions quickly.",
            is_stable=False,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Odd-Even Sort",
            generator=odd_even_sort,
            description="Parallel-friendly comparison sort alternating odd and even phases to resolve inversions.",
            is_stable=False,
            time_complexity="O(n^2)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Shell Sort",
            generator=shell_sort,
            description="Incremental gap-based sorter that diminishes large displacements before a final insertion pass.",
            is_stable=False,
            time_complexity="O(n^{3/2})",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Merge Sort",
            generator=merge_sort,
            description="Stable divide-and-conquer algorithm delivering guaranteed O(n log n) performance.",
            is_stable=True,
            time_complexity="O(n log n)",
            space_complexity="O(n)",
        ),
        AlgorithmDefinition(
            name="Quick Sort",
            generator=quick_sort,
            description="In-place partitioning sort that achieves average O(n log n) time by recursing around a pivot.",
            is_stable=False,
            time_complexity="O(n log n)",
            space_complexity="O(log n)",
        ),
        AlgorithmDefinition(
            name="Heap Sort",
            generator=heap_sort,
            description="Heap-based sorter that repeatedly extracts the maximum to build the sorted suffix.",
            is_stable=False,
            time_complexity="O(n log n)",
            space_complexity="O(1)",
        ),
        AlgorithmDefinition(
            name="Radix Sort",
            generator=radix_sort,
            description="Non-comparison sort that processes digits into buckets to produce linear-time ordering.",
            is_stable=True,
            time_complexity="O(nk)",
            space_complexity="O(n + k)",
        ),
    ]
