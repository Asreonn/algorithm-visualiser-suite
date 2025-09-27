# Sorting Algorithm Visualizer

Modern Tkinter application for watching multiple sorting algorithms operate on the same dataset, side by side and step by step. Each algorithm produces rich telemetry, colour-coded highlights, and human-readable explanations for every operation.

## Highlights
- **Parallel panels** – Bubble, Cocktail Shaker, Insertion, Selection, Gnome, Comb, Shell, Merge, Quick, Heap, Counting, and Radix sort animate together.
- **Interactive controls** – Pause, resume, single-step, or stop the run entirely; generate fresh datasets on demand.
- **Colour legend** – Comparisons, swaps, overwrites, pivots, and fixed elements are mapped to a consistent palette.
- **Structured architecture** – Core algorithms live under `sorting_viz.core`; the Tkinter UI consumes generator steps only.
- **Live metrics** – Each panel displays counts for steps, comparisons, swaps, and elapsed time.

## Getting Started
```bash
cd sorting
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

> Windows: `.venv\Scripts\activate`
> `requirements.txt` is optional today; keep it if you later externalise dependencies.

## Controls
- **Generate** – Produce a new random dataset with default length/range.
- **Start** – Reset every panel and launch all algorithms in sync.
- **Pause / Resume** – Toggle the animation loop globally.
- **Step** – When paused, advance all algorithms by a single tick.
- **Stop** – Cancel the current run and keep the current dataset for inspection.

## Project Layout
```
app.py
src/sorting_viz/
  __init__.py
  config.py
  core/
  ui/app.py
```

## Extending
- Add or tweak algorithms inside `src/sorting_viz/core/algorithms.py`; register new variants via `core/registry.py`.
- Adjust colours, dataset sizes, and animation speed in `src/sorting_viz/config.py`.
- The UI layer only depends on generator-driven `Step` objects, making it straightforward to plug in alternative data sources.

Enjoy exploring how classic sorting strategies tackle the same data in different ways!
