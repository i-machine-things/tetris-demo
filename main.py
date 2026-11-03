import sys

from PyQt6.QtWidgets import QApplication

from tetris.widget import GameWindow


def main():
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()

    exit_code = app.exec()

    window.deleteLater()
    app.processEvents()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
