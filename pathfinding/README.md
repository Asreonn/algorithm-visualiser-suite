# Pathfinding Visualiser

Modernised, modular Pygame application for experimenting with classic grid-based pathfinding algorithms. Build custom mazes, switch algorithms on the fly, and watch each search strategy solve the puzzle in real time.

## Features
- Multiple algorithms out of the box: A* Search, Dijkstra, and Breadth-First Search.
- Interactive editing: place start/end nodes and barriers directly on the grid.
- Real-time visual feedback for open, closed, and final path states.
- Keyboard shortcuts to reset, clear paths, and swap algorithms without leaving the app.

## Getting Started
```bash
cd pathfinding
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py --width 800 --rows 24 --fps 60
```

> Windows: `.venv\Scripts\activate`
> `requirements.txt` remains optional until external dependencies are introduced.

## Controls
- `Left Click`: set start, end, and barrier tiles (in that order).
- `Right Click`: clear a tile (removes start/end/barriers).
- `1 / 2 / 3`: select A*, Dijkstra, or Breadth-First search respectively.
- `Space`: run the currently selected algorithm.
- `S`: stop the active search and keep the current dataset.
- `R`: clear the algorithm trail while keeping barriers.
- `C`: reset the grid entirely.
- `Esc` or window close: exit the application.

## Project Layout
```
app.py
src/pathfinding_viz/
  __init__.py
  constants.py
  grid.py
  algorithms/
  ui/app.py
```

## Notes
- Add new algorithms by subclassing `PathfindingAlgorithm` inside `src/pathfinding_viz/algorithms` and registering them in `AlgorithmOption` within `ui/app.py`.
