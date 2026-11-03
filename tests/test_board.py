from tetris.board import Board, Piece


def test_new_board_spawns_piece_in_bounds():
    board = Board()
    for x, y in board.current.occupied_cells():
        assert 0 <= x < board.width
        assert y < board.height


def test_move_blocked_by_left_wall():
    board = Board()
    board.current = Piece("O", x=-1, y=0)  # O's cells start at local column 1
    assert board.move(-1, 0) is False
    assert board.current.x == -1


def test_move_within_bounds_succeeds():
    board = Board()
    board.current = Piece("O", x=3, y=0)
    assert board.move(1, 0) is True
    assert board.current.x == 4


def test_rotate_changes_rotation_state():
    board = Board()
    board.current = Piece("T", rotation=0, x=4, y=5)
    assert board.rotate() is True
    assert board.current.rotation == 1


def test_hard_drop_locks_piece_onto_grid():
    board = Board()
    board.current = Piece("O", x=0, y=0)
    board.hard_drop()
    assert board.grid[board.height - 1][1] == "O"
    assert board.grid[board.height - 1][2] == "O"


def test_full_row_clears_and_scores():
    board = Board(width=4, height=5)
    board.grid[4] = ["I", "I", "I", None]
    board.current = Piece("O", x=1, y=3)  # settles at columns 2-3, rows 3-4
    board.lock()
    assert board.lines_cleared == 1
    assert board.score > 0
    assert len(board.grid) == board.height


def test_game_over_when_spawn_blocked():
    board = Board(width=6, height=6)
    for y in (0, 1):
        for x in range(board.width - 1):
            board.grid[y][x] = "I"

    board.current = Piece("O", x=-1, y=board.height - 2)  # locks harmlessly at the bottom
    board.next_piece = Piece("O", x=2, y=0)  # collides with the blocked spawn area

    board.lock()

    assert board.game_over is True
