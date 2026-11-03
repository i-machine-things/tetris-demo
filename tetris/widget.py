# tetris/widget.py — turns the game logic in tetris/board.py into something
# you can actually see and play.
#
# This file is built on PyQt6, a library for building on-screen windows ("GUI"
# — Graphical User Interface — programming). If tetris/board.py hasn't been
# read yet, a few ideas there (classes, `self`, methods) are assumed to make
# sense already; this file's comments focus on what's specific to PyQt6:
# inheritance, drawing, and reacting to keyboard/timer events.

"""PyQt6 rendering and input handling for the Tetris demo."""

# `Qt` bundles together many constants PyQt6 code refers to (like which key
# was pressed). `QTimer` fires an event repeatedly on a schedule — it's what
# makes pieces fall automatically over time, rather than only moving when a
# key is pressed.
from PyQt6.QtCore import Qt, QTimer

# `QColor` represents a color; `QKeyEvent` is the information PyQt6 hands you
# when a key is pressed (which key, whether it's a held-down repeat, etc.);
# `QPainter` is the tool used to actually draw shapes onto the screen.
from PyQt6.QtGui import QColor, QKeyEvent, QPainter

# The on-screen building blocks this file uses: QWidget (a generic drawable
# area), QLabel (a line of text), QMainWindow (a top-level window with the
# usual title bar/minimize/close buttons), and two layout managers
# (QHBoxLayout arranges things left-to-right, QVBoxLayout arranges things
# top-to-bottom) that handle positioning so we don't have to calculate pixel
# coordinates by hand.
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from tetris.board import COLORS, Board

# Tuning numbers, gathered here so they're easy to find and adjust. CELL_SIZE
# is how many on-screen pixels each board square takes up. The *_TICK_MS
# values are in milliseconds (1000ms = 1 second) and control how often the
# piece automatically falls — see _restart_timer below.
CELL_SIZE = 24
EMPTY_COLOR = QColor(20, 20, 20)
GRID_LINE_COLOR = QColor(40, 40, 40)
BASE_TICK_MS = 600
MIN_TICK_MS = 100


# `class BoardWidget(QWidget):` means "BoardWidget is a QWidget, plus
# whatever extra behavior is defined below." This is *inheritance* — PyQt6
# already knows how to make a generic drawable rectangle (QWidget); we're
# customizing it into specifically "a rectangle that draws a Tetris board."
# Everything QWidget already knows how to do, BoardWidget still does too.
class BoardWidget(QWidget):
    def __init__(self, board: Board, parent=None):
        # `super()` refers to the parent class (QWidget). Calling
        # `super().__init__(parent)` runs QWidget's own setup code first,
        # before adding anything specific to BoardWidget. This is standard
        # practice whenever you inherit from something — skipping it would
        # leave the inherited part half-initialized. `parent=None` is the
        # usual Qt convention for "this widget isn't nested inside another
        # one" (a value of `None` is Python's way of saying "nothing here").
        super().__init__(parent)
        self.board = board
        # Tell Qt exactly how big this widget should be on screen: one
        # CELL_SIZE square per column and row of the board.
        self.setFixedSize(board.width * CELL_SIZE, board.height * CELL_SIZE)

    # `paintEvent` is not a name we invented — it's one Qt specifically
    # looks for and calls automatically, any time this widget needs to be
    # (re)drawn: when it first appears, when it's uncovered by another
    # window, or whenever we explicitly ask for a redraw (see `.update()`
    # calls further down). Methods like this, with a name and signature Qt
    # recognizes, are often called "event handlers" or, since we're
    # customizing inherited behavior, "overrides."
    def paintEvent(self, event):  # noqa: N802 - Qt override
        # A QPainter is a short-lived tool for drawing onto this specific
        # widget; `self` here being passed in means "draw onto me."
        painter = QPainter(self)
        # Loop over every row, then every cell in that row. `enumerate(...)`
        # gives us both the item and its position (y for rows, x for
        # columns) at the same time, which we need to know *where* to draw
        # each cell, not just what's in it.
        for y, row in enumerate(self.board.grid):
            for x, kind in enumerate(row):
                # `COLORS[kind] if kind else None` is a one-line if/else
                # (called a "conditional expression"): if `kind` is a
                # truthy value (any non-empty string here), look up its
                # color; if `kind` is `None` (empty cell), use `None`
                # instead. _paint_cell (below) treats `None` as "draw this
                # cell empty."
                self._paint_cell(painter, x, y, COLORS[kind] if kind else None)

        # Also draw the piece that's still actively falling (it isn't part
        # of self.board.grid yet — see lock() in tetris/board.py, which is
        # what actually stamps a piece into the grid once it lands).
        if not self.board.game_over:
            kind = self.board.current.kind
            for x, y in self.board.current.occupied_cells():
                # A falling piece can have cells above the visible board
                # (negative y) right as it spawns; skip drawing those.
                if y >= 0:
                    self._paint_cell(painter, x, y, COLORS[kind])

        # Always explicitly finish a QPainter when done with it, or Qt can
        # leave drawing resources in a half-used state.
        painter.end()

    def _paint_cell(self, painter: QPainter, x: int, y: int, rgb):
        rect_x, rect_y = x * CELL_SIZE, y * CELL_SIZE
        # `QColor(*rgb)` — the `*` "unpacks" the (r, g, b) tuple into three
        # separate arguments, equivalent to writing `QColor(rgb[0], rgb[1],
        # rgb[2])`. Fill the square with its piece color, or EMPTY_COLOR if
        # rgb is None (see the conditional expression above).
        painter.fillRect(rect_x, rect_y, CELL_SIZE, CELL_SIZE, QColor(*rgb) if rgb else EMPTY_COLOR)
        painter.setPen(GRID_LINE_COLOR)
        painter.drawRect(rect_x, rect_y, CELL_SIZE, CELL_SIZE)


# The main window the player actually sees. Like BoardWidget above, this
# *inherits* from an existing Qt building block (QMainWindow — a window with
# a title bar) rather than building one from scratch.
class GameWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tetris Demo")
        # By default, a QMainWindow doesn't necessarily grab keyboard focus
        # just because it's visible — without this, the player might have to
        # click the window before key presses register at all.
        # StrongFocus means "this window accepts keyboard focus, both from
        # clicking on it and from the normal tab-between-widgets order."
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Create the actual game state (tetris/board.py) and the widget that
        # draws it (defined above in this same file).
        self.board = Board()
        self.board_widget = BoardWidget(self.board)

        # QLabel is just a piece of text on screen. These three will show
        # the score, level, and status messages ("Paused", "Game over").
        self.score_label = QLabel()
        self.level_label = QLabel()
        self.status_label = QLabel("Arrows move/rotate, Space hard-drops, P pauses")

        # Layouts are Qt's way of arranging widgets without manually
        # calculating pixel positions. A QVBoxLayout stacks its widgets
        # top-to-bottom, in the order they're added.
        side_panel = QVBoxLayout()
        side_panel.addWidget(self.score_label)
        side_panel.addWidget(self.level_label)
        # `.addStretch()` inserts a flexible, invisible gap that expands to
        # fill any leftover space — it pushes the status label down to the
        # bottom of the side panel instead of leaving it bunched up near the
        # top.
        side_panel.addStretch()
        side_panel.addWidget(self.status_label)

        # A QHBoxLayout arranges things left-to-right: the board on the
        # left, the whole side panel (score/level/status) on the right.
        # `.addLayout(...)` nests one layout inside another, which is how
        # layouts combine into more complex arrangements.
        layout = QHBoxLayout()
        layout.addWidget(self.board_widget)
        layout.addLayout(side_panel)

        # A QMainWindow needs one single "central widget" to hold everything
        # else — you can't hand it a bare layout directly, so a plain
        # QWidget acts as a container, and the layout goes inside that.
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.paused = False
        # Create a timer owned by this window (`self` as the parent means
        # Qt will automatically clean it up when the window is destroyed).
        # `.timeout.connect(self._tick)` is Qt's "signals and slots" system:
        # it wires the timer's recurring "timeout" signal to our `_tick`
        # method, so `_tick` runs automatically every time the timer fires
        # — we never call `_tick` ourselves directly.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._restart_timer()

        self._refresh_labels()

    def _restart_timer(self):
        # Pieces fall faster at higher levels. `max(MIN_TICK_MS, ...)`
        # guarantees the interval never drops below MIN_TICK_MS, no matter
        # how high the level climbs — otherwise the subtraction could
        # eventually reach zero or a negative number of milliseconds, which
        # wouldn't make sense as a timer delay.
        interval = max(MIN_TICK_MS, BASE_TICK_MS - (self.board.level - 1) * 50)
        self.timer.start(interval)

    def _tick(self):
        # Runs automatically every time the timer fires (see
        # `.timeout.connect(self._tick)` above) — this is what makes the
        # piece fall on its own, without the player pressing anything.
        if self.paused or self.board.game_over:
            return
        self.board.soft_drop()
        # The fall speed depends on the level, which can change after a
        # drop (see Board._clear_lines in tetris/board.py) — restart the
        # timer each tick so a level-up takes effect immediately rather
        # than waiting for the old, slower interval to finish.
        self._restart_timer()
        self._refresh_labels()
        # `.update()` doesn't draw anything itself — it tells Qt "this
        # widget is now out of date, please call paintEvent again soon."
        # Actual drawing always happens inside paintEvent, never here.
        self.board_widget.update()

    def _refresh_labels(self):
        # An f-string (the `f` right before the opening quote) lets you
        # embed a Python expression directly inside a piece of text, inside
        # curly braces — `f"Score: {self.board.score}"` builds a string like
        # "Score: 1200" without manually converting the number to text and
        # gluing the pieces together.
        self.score_label.setText(f"Score: {self.board.score}")
        self.level_label.setText(f"Level: {self.board.level}")
        if self.board.game_over:
            self.status_label.setText("Game over")

    # Another Qt-recognized event handler (see the longer explanation on
    # paintEvent above) — called automatically right after the window
    # actually becomes visible.
    def showEvent(self, event):  # noqa: N802 - Qt override
        super().showEvent(event)
        self.setFocus()

    # Called automatically by Qt every time a key is pressed while this
    # window has focus. `event` carries the details of exactly what
    # happened.
    def keyPressEvent(self, event: QKeyEvent):  # noqa: N802 - Qt override
        if self.board.game_over:
            return
        key = event.key()
        # If a key is held down, the operating system sends repeated
        # keyPressEvent calls on its own (this is what makes holding an
        # arrow key in a text editor scroll continuously, for example).
        # `event.isAutoRepeat()` tells us whether *this particular* event is
        # one of those repeats rather than the original press.
        # `key in (Qt.Key.Key_P, Qt.Key.Key_Space)` checks whether `key`
        # matches either value in that parenthesized tuple — a compact
        # alternative to writing two separate `or`-ed comparisons.
        if event.isAutoRepeat() and key in (Qt.Key.Key_P, Qt.Key.Key_Space):
            return  # pause/hard-drop are one-shot; don't retrigger on a held key
        if key == Qt.Key.Key_P:
            # `not self.paused` flips a boolean: True becomes False and
            # vice versa. This is the standard way to "toggle" a switch.
            self.paused = not self.paused
            # Another one-line if/else (conditional expression, explained in
            # BoardWidget.paintEvent above): show "Paused" while paused,
            # otherwise clear the message to an empty string.
            self.status_label.setText("Paused" if self.paused else "")
            return
        if self.paused:
            return

        # A chain of `if` / `elif` ("else if") / `else`: Python checks each
        # condition in order and runs the first one that matches, skipping
        # the rest. Exactly one branch below runs per key press.
        if key == Qt.Key.Key_Left:
            self.board.move(-1, 0)
        elif key == Qt.Key.Key_Right:
            self.board.move(1, 0)
        elif key == Qt.Key.Key_Down:
            self.board.soft_drop()
        elif key == Qt.Key.Key_Up:
            self.board.rotate()
        elif key == Qt.Key.Key_Space:
            self.board.hard_drop()
        else:
            # Some other, unhandled key was pressed — there's nothing to
            # redraw or update, so bail out early instead of falling
            # through to the refresh/redraw calls below.
            return

        self._refresh_labels()
        self.board_widget.update()

    # Called automatically by Qt when the window is about to close (the
    # player clicked the X button, or the OS is shutting the app down).
    def closeEvent(self, event):  # noqa: N802 - Qt override
        # Stop the timer explicitly before the window disappears — if left
        # running, it could keep trying to fire events against a window
        # that no longer exists.
        self.timer.stop()
        # Tell Qt the close is allowed to proceed. A close handler *could*
        # call `event.ignore()` instead, to cancel the close (e.g. to pop up
        # an "are you sure?" prompt first) — this demo doesn't need that.
        event.accept()
