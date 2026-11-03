# main.py — the entry point.
#
# "Entry point" means: this is the file you actually run (`python main.py`) to start
# the program. Everything else in this project is a building block that this file
# wires together. If you've never read Python before, the comments in this file and
# in tetris/board.py and tetris/widget.py are written for you.

# `import` brings in code that already exists elsewhere, so we don't have to
# rewrite it ourselves. `sys` is part of Python's own standard toolkit ("the
# standard library") — it gives us access to things the operating system cares
# about, like command-line arguments and how to exit the program cleanly.
import sys

# This imports one specific tool, `QApplication`, from a much bigger external
# library called PyQt6 (a Python wrapper around Qt, a toolkit for building
# on-screen windows, buttons, and graphics — "Qt" is pronounced "cute"). Every
# PyQt6 program needs exactly one QApplication; it manages the event loop (more
# on that below) and talks to the operating system on the program's behalf.
from PyQt6.QtWidgets import QApplication

# This imports `GameWindow`, a class we wrote ourselves, from tetris/widget.py.
# A "class" is a blueprint for creating objects that bundle together both data
# and the functions that operate on that data. GameWindow is the blueprint for
# "the actual game window the player sees" — see tetris/widget.py for its
# full definition and a deeper explanation of what a class is.
from tetris.widget import GameWindow


# `def` defines a function: a named, reusable block of code. `main()` takes no
# inputs (nothing between the parentheses) and is the top-level routine that
# starts the whole program.
def main():
    # Create the one-and-only QApplication. `sys.argv` is the list of
    # command-line arguments the program was started with (e.g. if you ran
    # `python main.py --fullscreen`, sys.argv would contain "--fullscreen").
    # This demo doesn't use any, but PyQt6 expects the list to be passed in
    # regardless.
    app = QApplication(sys.argv)

    # Create an actual instance of the GameWindow blueprint — this is where
    # the window, the game board, and all its behavior actually come into
    # existence in memory.
    window = GameWindow()

    # Windows are invisible by default until you explicitly tell them to show.
    window.show()

    # app.exec() starts Qt's "event loop" and BLOCKS here — meaning the
    # program sits inside this one line, doing nothing else — until the
    # window is closed. While blocked, Qt is silently waiting for and
    # reacting to "events": a key press, a mouse click, a timer firing, the
    # window being resized, etc. Each event gets routed to the right piece of
    # code to handle it (see keyPressEvent and other *Event methods in
    # tetris/widget.py). This "wait for things to happen, then react" style is
    # called event-driven programming, and it's how almost all GUI (Graphical
    # User Interface) programs work.
    #
    # Once the window closes, app.exec() returns a number (0 normally means
    # "exited cleanly"), and sys.exit(...) hands that number back to the
    # operating system as the program's exit code.
    sys.exit(app.exec())


# This is a very common Python idiom (a standard, recognizable pattern). Every
# Python file has a built-in variable called __name__. When you run a file
# directly (`python main.py`), Python sets __name__ to the string "__main__".
# But if this file were instead imported from somewhere else (`import main`),
# __name__ would be set to "main" instead. This `if` check means: "only
# actually start the game if this file was run directly — don't start it just
# because something else imported it." It's a safety valve that makes a file
# usable both as a standalone program and as a reusable building block.
if __name__ == "__main__":
    main()
