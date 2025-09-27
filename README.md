# Algorithm Visualiser Suite

An advanced collection of desktop visualisation apps for classic algorithm families. Each project is intentionally isolated so new demos can be added or shipped independently while sharing a consistent design language, animation pipeline, and development workflow.

---
## Repository Layout
```
pathfinding/
  app.py
  README.md
  src/pathfinding_viz/
sorting/
  app.py
  README.md
  src/sorting_viz/
greedy/
  app.py
  README.md
  src/greedy_viz/
```

### Shared Architectural Concepts
- **Launcher parity** – Every `app.py` adjusts `PYTHONPATH`, instantiates its UI module, and keeps the CLI surface minimal.
- **Generator-driven animation** – Algorithms yield structured step dataclasses consumed by the UI, decoupling data production from rendering and enabling rewind/step-forward features.
- **Theme consistency** – Colours, typography, and layout primitives mirror the sorting visualiser; Tkinter apps reuse the same palette definitions, while the Pygame app applies equivalent hex values.
- **Zero implicit dependencies** – No hidden global state or cross-package imports; each app can be packaged or frozen without touching siblings.

---
## Runtime Stack
| Component  | Version / Notes                                   |
|------------|---------------------------------------------------|
| Python     | 3.9+ (tested on CPython 3.11, Fedora Linux)       |
| Tkinter    | Bundled with CPython; used by `sorting` & `greedy` |
| Pygame     | Optional, required only for `pathfinding`          |
| Tooling    | `rg`, `black`, `ruff`, `mypy` (recommended locally) |

> Install platform GUI libraries (X11/Wayland, Tk) before launching on headless servers.

---
## Quick Start
1. Clone the repository and switch into the root directory.
2. Choose the target app (example below uses `greedy`).
3. Create and activate a virtual environment.
   ```bash
   cd greedy
   python -m venv .venv
   source .venv/bin/activate
   ```
   Windows alternative: `.venv\Scripts\Activate.ps1`
4. Install dependencies if a `requirements.txt` is provided (only `pathfinding` currently bundles one; the others rely on the standard library).
5. Launch the app.
   ```bash
   python app.py
   ```
6. See the app-specific README for controls, CLI flags, and troubleshooting tips.

---
## Application Notes
### Pathfinding Visualiser
- **Tech**: Pygame rendering loop, grid abstraction, strategy interface for algorithms.
- **CLI options**: `--width`, `--rows`, `--fps` allow tuning resolution and animation speed.
- **Extensibility**: Add subclasses of `PathfindingAlgorithm` in `src/pathfinding_viz/algorithms` and register them in `ui/app.py`.

### Sorting Visualiser
- **Tech**: Tkinter layout with per-algorithm canvases, background animation ticker via `after` scheduling.
- **Parallel runs**: All algorithms operate on cloned datasets, broadcasting telemetry through shared `Step` records.
- **Extensibility**: Implement additional routines inside `src/sorting_viz/core/algorithms.py`, register them in `core/registry.py`, and they automatically appear in the UI grid.

### Greedy Visualiser
- **Tech**: Tkinter tabs for graph vs sequence problems, custom animation engine supporting rewind and overlays.
- **Graph playground**: Random/grid/complete graph generators, manual edge editing, comparison overlays for MST vs shortest-path algorithms.
- **Sequence mode**: Fractional Knapsack and Activity Selection share a unified `SequenceStep` model, enabling progress bars and partial selections.

---
## Development Workflow
### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install pygame
pip install black ruff mypy pytest
```
Skip the `pygame` install if you will not run the pathfinding app.

### Code Style & Linting
```bash
black greedy sorting pathfinding
ruff check greedy sorting pathfinding
mypy greedy/src sorting/src pathfinding/src
```
- Stick to type hints for new modules; existing code uses `from __future__ import annotations`.
- Keep Tkinter styling centralised in each app’s `config.py`.

### Testing & Verification
- **Smoke tests**: `python app.py` inside each app directory remains the fastest verification loop.
- **Automated hooks**: add `pytest` suites under `src/<package>/tests/` as the project grows; animation generators are pure functions and trivial to unit-test.
- **Static checks**: run `mypy` for type integrity and `ruff` for lint + import ordering.

### Packaging / Distribution
- The apps are pure Python; for frozen builds use `pyinstaller` or `briefcase` with `app.py` as the entry point.
- When shipping binaries, bundle only the selected `src/` package and theme assets to minimise size.

---
## Contributing & Extension Guidelines
1. Model new algorithms as generators yielding lightweight step dataclasses (`Step`, `GraphStep`, `SequenceStep`).
2. Keep UI code declarative; legend layouts, message cards, or keyboard shortcuts belong in `ui/app.py` not in algorithm modules.
3. Document new controls or CLI flags in the relevant app README.
4. If you add external dependencies, list them in `pathfinding/requirements.txt` or a new `requirements.txt` alongside the app and mention them in this README.
5. Update the layout section when new top-level apps are introduced.

For large proposals (new visualisers, architecture changes), open an issue describing:
- Problem domain and expected visual output.
- Proposed generator outputs, UI components, and state management.
- Third-party libraries or assets required.

---
## Release Checklist
- [ ] Run `black`, `ruff`, and `mypy` across all apps.
- [ ] Launch each app manually to confirm animations and controls behave as expected.
- [ ] Bump version identifiers (if maintained) and update per-app change logs.
- [ ] Tag the release (`git tag vX.Y.Z`) and push the tag.
- [ ] Draft release notes summarising new features, refactors, and dependency updates.

Treat each app as an independent product within the suite, and use this README as the technical contract for architecture, tooling, and contribution standards.
