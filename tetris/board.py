# tetris/board.py — the game's "rules engine."
#
# This file has no idea a window or graphics even exist. It only knows about a
# grid of cells and the rules for how pieces move, lock into place, and clear
# lines. That separation is deliberate: tetris/widget.py is in charge of
# *drawing* the game and reading the keyboard, and this file is in charge of
# deciding what's actually *true* about the game at any moment (what's on the
# board, whether a move is legal, the score). Keeping those two concerns apart
# is why this file can be tested without ever opening a window — see
# tests/test_board.py, which does exactly that.
#
# If you're new to Python, read this file's comments top to bottom; they
# introduce ideas roughly in the order you'll need them.

"""Pure game logic for Tetris. No Qt dependency, so it can be unit tested headlessly."""

# `from X import Y` pulls just the specific tool(s) named Y out of module X,
# rather than the whole thing. `dataclass` is explained below, right where
# it's used. `choice` is a function from Python's built-in `random` module
# that picks one random item out of a list.
from dataclasses import dataclass
from random import choice

# These are just named numbers. Writing BOARD_WIDTH instead of the bare
# number 10 everywhere means: (a) the code reads like English, and (b) if the
# board size ever needs to change, there's exactly one place to edit it.
# ALL_CAPS names are a Python convention (not a rule the language enforces)
# meaning "treat this as a constant — don't reassign it."
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# A Tetris piece is called a "tetromino" (any shape made of 4 connected
# squares). TETROMINOES is a *dictionary* — a collection of key/value pairs,
# written as `{key: value, key: value, ...}`. Here, each key is a one-letter
# piece name ("I", "O", "T", ...) and each value is a *list* of possible
# rotations for that piece. Each rotation is itself a list of 4 (x, y) pairs
# — small bundles of two numbers — describing which 4 squares, relative to
# the piece's own position, are filled in for that rotation.
#
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

# Another dictionary: each piece letter maps to an (R, G, B) color — three
# numbers from 0-255 for how much Red, Green, and Blue light to mix,
# the standard way computers represent color. tetris/widget.py reads this
# when it draws each piece.
COLORS = {
    "I": (0, 240, 240),
    "O": (240, 240, 0),
    "T": (160, 0, 240),
    "S": (0, 240, 0),
    "Z": (240, 0, 0),
    "J": (0, 0, 240),
    "L": (240, 160, 0),
}

# How many points you earn for clearing 1, 2, 3, or 4 lines at once (classic
# Tetris rewards clearing several lines in a single move much more than one
# at a time). `.get(n, 0)` later on means "look up n, or use 0 if it's not
# a key in this dictionary" — relevant because you can clear at most 4 lines
# in one move, but this guards against that assumption changing.
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


# A "class" is a blueprint for creating objects — bundles of related data plus
# the functions ("methods") that work on that data. `@dataclass` is a
# "decorator": a bit of code, prefixed with @, that modifies the class
# directly below it. Here it automatically writes the boilerplate code every
# simple data-holding class needs (like a constructor that takes `kind`,
# `rotation`, `x`, `y` as arguments) so we don't have to type it by hand.
#
# `kind: str` means "this piece has a field called `kind`, and it's expected
# to hold a string (text)." Python doesn't *enforce* these type hints at
# runtime the way some languages do — they're documentation and a way for
# editors/tools to catch mistakes, not a hard guarantee. `rotation: int = 0`
# adds a default value: if nobody specifies a rotation when creating a Piece,
# it starts at 0.
@dataclass
class Piece:
    kind: str
    rotation: int = 0
    x: int = 0
    y: int = 0

    # Every method on a class takes `self` as its first parameter — it's how
    # the method refers back to "the specific object I'm running on," since
    # the same method body is shared by every Piece that ever gets created.
    # `self.kind` means "the kind field belonging to this particular piece."
    def cells(self):
        states = TETROMINOES[self.kind]
        # `%` is the modulo operator: it returns the remainder after
        # division. Using it here makes rotation "wrap around" — if there
        # are 4 rotation states (indices 0, 1, 2, 3) and self.rotation
        # becomes 4, `4 % 4` is 0, so it loops back to the first state
        # instead of crashing on a missing index.
        return states[self.rotation % len(states)]

    def occupied_cells(self):
        # This is a *list comprehension*: a compact way to build a new list
        # by transforming every item in an existing one. It's equivalent to
        # writing a loop that appends to an empty list each time, just
        # shorter. `for cx, cy in self.cells()` unpacks each (x, y) pair from
        # cells() into two separate names, cx and cy, for use in that one
        # expression. The result shifts every relative cell by the piece's
        # actual board position (self.x, self.y).
        return [(self.x + cx, self.y + cy) for cx, cy in self.cells()]


# The main class: everything about the state of one game in progress.
class Board:
    # `__init__` (two underscores on each side — called a "dunder", short for
    # "double underscore") is the constructor: the method Python
    # automatically runs when you create a new Board, e.g. `Board()`. Its job
    # is to set up the object's starting state. `width=BOARD_WIDTH` means
    # "this parameter is optional, and defaults to BOARD_WIDTH if not given."
    def __init__(self, width=BOARD_WIDTH, height=BOARD_HEIGHT):
        self.width = width
        self.height = height
        # The board itself: a list of `height` rows, where each row is a
        # list of `width` cells, all starting out as `None` (Python's "no
        # value here" placeholder) meaning "empty." `[[None] * width for _
        # in range(height)]` is a list comprehension (see above) that builds
        # one fresh list per row — written this way (rather than `[[None] *
        # width] * height`) specifically so each row is its own independent
        # list, not the exact same list repeated, which would make changing
        # one row accidentally change all of them. `range(height)` counts
        # from 0 up to (but not including) height; the throwaway name `_` is
        # a Python convention for "a loop variable I'm not actually going to
        # use."
        self.grid = [[None] * width for _ in range(height)]
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        # `False` is one of Python's two boolean (true/false) values. This
        # flag starts false and flips to true once the board fills up to the
        # point a new piece can't spawn.
        self.game_over = False
        # Methods whose names start with an underscore, like `_new_piece`
        # below, are a Python convention meaning "internal detail of this
        # class — other code shouldn't need to call this directly." Python
        # doesn't actually enforce that privacy (unlike some languages); it's
        # a signal to other programmers, not a lock.
        self.current = self._new_piece()
        self.next_piece = self._new_piece()

    def _new_piece(self):
        # `list(TETROMINOES)` turns the dictionary's keys ("I", "O", "T", ...)
        # into a plain list, and `choice(...)` (imported at the top of this
        # file) picks one at random.
        kind = choice(list(TETROMINOES))
        # `//` is integer division: divide and round down, discarding any
        # remainder, so the result is always a whole number — needed here
        # since you can't position a piece at a fractional column.
        return Piece(kind=kind, x=self.width // 2 - 2, y=0)

    def _fits(self, piece):
        # Check every cell the piece would occupy. If any of them is off the
        # board, or already filled by a locked piece, this move is illegal.
        for x, y in piece.occupied_cells():
            if x < 0 or x >= self.width or y >= self.height:
                return False
            # A new piece can start partly above the visible board (negative
            # y) while it's dropping in — only check the grid for collisions
            # once a cell is actually on it (y >= 0).
            if y >= 0 and self.grid[y][x] is not None:
                return False
        # If we checked every cell and never returned False above, the move
        # is legal.
        return True

    def move(self, dx, dy):
        if self.game_over:
            return False
        # Build a *hypothetical* piece at the new position without
        # committing to it yet — "trial" as in "let's try this and see."
        trial = Piece(self.current.kind, self.current.rotation, self.current.x + dx, self.current.y + dy)
        if self._fits(trial):
            # Only now, after confirming it's legal, replace the real
            # current piece with the trial one.
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
        # "Soft drop" = nudge the piece down one row if there's room;
        # otherwise it's hit bottom, so lock it in place for good.
        if not self.move(0, 1):
            self.lock()

    def hard_drop(self):
        # `while` repeats the loop body for as long as its condition stays
        # true. Here: keep moving the piece down, one row at a time, for as
        # long as that's a legal move. The moment move() returns False
        # (can't go further), the loop stops on its own — `pass` just means
        # "do nothing extra inside the loop body; the move() call itself is
        # the whole point."
        while self.move(0, 1):
            pass
        self.lock()

    def lock(self):
        # The piece has landed — permanently stamp each of its cells onto
        # the grid.
        for x, y in self.current.occupied_cells():
            if y < 0:
                # The piece is still partly above the visible board and
                # already can't move — there's no room left. Game over.
                self.game_over = True
                return
            self.grid[y][x] = self.current.kind
        self._clear_lines()
        # The piece that was "on deck" becomes the one in play, and a fresh
        # one is generated to take its place as the new "on deck" piece.
        self.current = self.next_piece
        self.next_piece = self._new_piece()
        if not self._fits(self.current):
            self.game_over = True

    def _clear_lines(self):
        # Find every row that's completely full. `enumerate(self.grid)`
        # pairs each row with its row number (y), so we know *which* rows
        # are full, not just that some are. `all(cell is not None for cell
        # in row)` is a *generator expression* feeding Python's built-in
        # `all()` function: it means "true only if every single cell in this
        # row is non-empty." The whole line is a list comprehension that
        # collects just the row numbers meeting that condition.
        full_rows = [y for y, row in enumerate(self.grid) if all(cell is not None for cell in row)]
        if not full_rows:
            return
        for y in full_rows:
            # `del` removes an item from a list by its position. Removing a
            # full row leaves a gap at the top, so we immediately insert a
            # fresh, empty row there — `.insert(0, ...)` means "put this at
            # position 0," i.e. the very top of the board. The net effect:
            # everything above the cleared row visually "falls" down by one.
            del self.grid[y]
            self.grid.insert(0, [None] * self.width)
        n = len(full_rows)
        self.lines_cleared += n
        # `.get(n, 0)` looks up n lines' worth of points, or 0 if n somehow
        # isn't a key in LINE_SCORES (see that dict's comment above).
        # Score scales with the current level, so clearing lines is worth
        # more the further into the game you get.
        self.score += LINE_SCORES.get(n, 0) * self.level
        self.level = 1 + self.lines_cleared // 10
