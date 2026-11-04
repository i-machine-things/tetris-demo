# tetris-demo

A single-player Tetris clone built with PyQt6.

![Tetris Demo gameplay screenshot](docs/images/screenshot.png)

## Playing on Windows without installing Python

Download `TetrisDemo.exe` from the [latest release](../../releases/latest) and run it —
no Python or dependencies required. Every `v*` tag triggers
[`.github/workflows/release.yml`](.github/workflows/release.yml), which builds the `.exe`
with PyInstaller and attaches it to the corresponding GitHub Release.

## Running from source

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Key          | Action      |
|--------------|-------------|
| Left / Right | Move        |
| Up           | Rotate      |
| Down         | Soft drop   |
| Space        | Hard drop   |
| P            | Pause       |

## Project layout

- `main.py` — entry point.
- `tetris/board.py` — game logic (grid, pieces, rotation, line clears, scoring). No Qt dependency.
- `tetris/widget.py` — PyQt6 rendering and input handling.
- `tests/test_board.py` — unit tests for the game logic.

## Testing

```bash
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v
```
