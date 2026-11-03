"""PyQt6 rendering and input handling for the Tetris demo."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QKeyEvent, QPainter
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from tetris.board import COLORS, Board

CELL_SIZE = 24
EMPTY_COLOR = QColor(20, 20, 20)
GRID_LINE_COLOR = QColor(40, 40, 40)
BASE_TICK_MS = 600
MIN_TICK_MS = 100


class BoardWidget(QWidget):
    def __init__(self, board: Board, parent=None):
        super().__init__(parent)
        self.board = board
        self.setFixedSize(board.width * CELL_SIZE, board.height * CELL_SIZE)

    def paintEvent(self, event):  # noqa: N802 - Qt override
        painter = QPainter(self)
        for y, row in enumerate(self.board.grid):
            for x, kind in enumerate(row):
                self._paint_cell(painter, x, y, COLORS[kind] if kind else None)

        if not self.board.game_over:
            kind = self.board.current.kind
            for x, y in self.board.current.occupied_cells():
                if y >= 0:
                    self._paint_cell(painter, x, y, COLORS[kind])

        painter.end()

    def _paint_cell(self, painter: QPainter, x: int, y: int, rgb):
        rect_x, rect_y = x * CELL_SIZE, y * CELL_SIZE
        painter.fillRect(rect_x, rect_y, CELL_SIZE, CELL_SIZE, QColor(*rgb) if rgb else EMPTY_COLOR)
        painter.setPen(GRID_LINE_COLOR)
        painter.drawRect(rect_x, rect_y, CELL_SIZE, CELL_SIZE)


class GameWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tetris Demo")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.board = Board()
        self.board_widget = BoardWidget(self.board)

        self.score_label = QLabel()
        self.level_label = QLabel()
        self.status_label = QLabel("Arrows move/rotate, Space hard-drops, P pauses")

        side_panel = QVBoxLayout()
        side_panel.addWidget(self.score_label)
        side_panel.addWidget(self.level_label)
        side_panel.addStretch()
        side_panel.addWidget(self.status_label)

        layout = QHBoxLayout()
        layout.addWidget(self.board_widget)
        layout.addLayout(side_panel)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.paused = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self._restart_timer()

        self._refresh_labels()

    def _restart_timer(self):
        interval = max(MIN_TICK_MS, BASE_TICK_MS - (self.board.level - 1) * 50)
        self.timer.start(interval)

    def _tick(self):
        if self.paused or self.board.game_over:
            return
        self.board.soft_drop()
        self._restart_timer()
        self._refresh_labels()
        self.board_widget.update()

    def _refresh_labels(self):
        self.score_label.setText(f"Score: {self.board.score}")
        self.level_label.setText(f"Level: {self.board.level}")
        if self.board.game_over:
            self.status_label.setText("Game over")

    def showEvent(self, event):  # noqa: N802 - Qt override
        super().showEvent(event)
        self.setFocus()

    def keyPressEvent(self, event: QKeyEvent):  # noqa: N802 - Qt override
        if self.board.game_over:
            return
        key = event.key()
        if event.isAutoRepeat() and key in (Qt.Key.Key_P, Qt.Key.Key_Space):
            return  # pause/hard-drop are one-shot; don't retrigger on a held key
        if key == Qt.Key.Key_P:
            self.paused = not self.paused
            self.status_label.setText("Paused" if self.paused else "")
            return
        if self.paused:
            return

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
            return

        self._refresh_labels()
        self.board_widget.update()

    def closeEvent(self, event):  # noqa: N802 - Qt override
        self.timer.stop()
        event.accept()
