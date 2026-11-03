"""Pure game logic for Tetris. No Qt dependency, so it can be unit tested headlessly."""

from dataclasses import dataclass
from random import choice

BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# Each entry is a list of rotation states; each state is a list of (x, y)
# cell offsets within the piece's bounding box. Simplified fixed rotations
# (no SRS wall-kicks) — adequate for a demo.
TETROMINOES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "S": [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "Z": [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


@dataclass
class Piece:
    kind: str
    rotation: int = 0
    x: int = 0
    y: int = 0

    def cells(self):
        states = TETROMINOES[self.kind]
        return states[self.rotation % len(states)]

    def occupied_cells(self):
        return [(self.x + cx, self.y + cy) for cx, cy in self.cells()]


class Board:
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT):
        self.width = width
        self.height = height
        self.grid = [[None] * width for _ in range(height)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.game_over = False
        self.current = self._new_piece()
        self.next_piece = self._new_piece()

    def _new_piece(self):
        kind = choice(list(TETROMINOES))
        return Piece(kind=kind, x=self.width // 2 - 2, y=0)

    def _fits(self, piece):
        for x, y in piece.occupied_cells():
            if x < 0 or x >= self.width or y >= self.height:
                return False
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True

    def move(self, dx, dy):
        if self.game_over:
            return False
        trial = Piece(self.current.kind, self.current.rotation, self.current.x + dx, self.current.y + dy)
        if self._fits(trial):
            self.current = trial
            return True
        return False

    def rotate(self):
        if self.game_over:
            return False
        trial = Piece(self.current.kind, self.current.rotation + 1, self.current.x, self.current.y)
        if self._fits(trial):
            self.current = trial
            return True
        return False

    def soft_drop(self):
        if not self.move(0, 1):
            self.lock()

    def hard_drop(self):
        while self.move(0, 1):
            pass
        self.lock()

    def lock(self):
        for x, y in self.current.occupied_cells():
            if y < 0:
                self.game_over = True
                return
            self.grid[y][x] = self.current.kind
        self._clear_lines()
        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if not self._fits(self.current):
            self.game_over = True

    def _clear_lines(self):
        full_rows = [y for y, row in enumerate(self.grid) if all(cell is not None for cell in row)]
        if not full_rows:
            return
        for y in full_rows:
            del self.grid[y]
            self.grid.insert(0, [None] * self.width)
        n = len(full_rows)
        self.lines_cleared += n
        self.score += LINE_SCORES.get(n, 0) * self.level
        self.level = 1 + self.lines_cleared // 10
