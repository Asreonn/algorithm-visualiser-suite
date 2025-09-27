# Greedy Algorithm Visualiser

Modern Tkinter application that keeps the suite's dark aesthetic while showcasing classic greedy strategies on graphs and sequences. Adjust datasets on the fly, compare algorithms side by side, and inspect every decision through annotated overlays and tooltips.

## Highlights
- **Graph playground** – Generate random, grid, or complete weighted graphs, edit edges manually, and pick start/goal nodes directly on the canvas.
- **Algorithm roster** – Prim and Kruskal for MSTs, Dijkstra and Greedy Best-First for shortest paths, plus Fractional Knapsack and Activity Selection for sequence-style problems.
- **Comparison mode** – Overlay a second algorithm's spanning tree or path to contrast behaviours step by step.
- **Interactive coaching** – Hover tooltips convey node status, queue snapshots stay in sync, and tutorial overlays greet first-time visitors.
- **Vivid messaging** – Highlighted message cards anlık kararları vurgular, gereksiz pop-up kullanmadan akışı açık tutar.
- **Shared design language** – Reuses the minimalist palette, typography, and control layout from the existing sorting visualiser for a cohesive experience.

## Getting Started
```bash
cd greedy
python -m venv .venv
source .venv/bin/activate
python app.py
```

> Windows: `.venv\Scripts\activate`

## Controls (Graph Tab)
- **Generate Graph** – Build a new dataset using the current graph type and node count.
- **Manual edit mode** – Toggle to add/remove edges by selecting two nodes; adjust the last edge weight with the slider.
- **Start / Pause / Step** – Drive the primary algorithm's animation; speed slider controls playback tempo.
- **Comparison mode** – Enable to overlay a second algorithm's selections as dashed accents.
- **Canvas interactions** – Click nodes (when not editing) to set start/goal; hover nodes to read their role in the current step.

## Controls (Sequence Tab)
- **Generate** – Produce a fresh knapsack or activity schedule dataset.
- **Capacity** – Adjust the knapsack capacity before starting the run.
- **Playback controls** – Start, pause/resume, or single-step through the greedy decisions.

## Project Layout
```
app.py
src/greedy_viz/
  __init__.py
  config.py
  data.py
  engine.py
  state.py
  algorithms/
    graph.py
    sequences.py
  ui/app.py
```

Enjoy experimenting with greedy strategies in the same polished environment as the sorting and pathfinding modules.
