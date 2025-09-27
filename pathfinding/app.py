from __future__ import annotations

import argparse

import sys
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
SRC_ROOT = APP_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pathfinding_viz import PathfindingApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive pathfinding visualiser")
    parser.add_argument('--width', type=int, default=800, help='Window width in pixels (default: 800)')
    parser.add_argument('--rows', type=int, default=24, help='Number of rows/columns in the grid (default: 24)')
    parser.add_argument('--fps', type=int, default=60, help='Frame rate limit (default: 60)')
    parser.add_argument('--height', type=int, default=None, help='Window height in pixels (default: auto)')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app = PathfindingApp(width=args.width, rows=args.rows, fps=args.fps, height=args.height)
    app.run()


if __name__ == '__main__':
    main()
