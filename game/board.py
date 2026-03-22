class Board:
    """
    An 8x8 board represented as a grid of piece chars.

    Squares are addressed in standard algebraic notation ("a1"–"h8").
    Uppercase chars = white pieces, lowercase = black, empty string = empty.

    Internal layout: grid[0][0] = a8 (top-left), grid[7][7] = h1 (bottom-right).
    This matches the FEN rank order (rank 8 first, rank 1 last).
    """

    def __init__(self):
        self._grid = [[""] * 8 for _ in range(8)]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        """Build a Board from the piece-placement field of a FEN string.
        Accepts either a full FEN or just the placement part."""
        board = cls()
        placement = fen.split()[0]
        for row_idx, row_str in enumerate(placement.split("/")):
            col_idx = 0
            for char in row_str:
                if char.isdigit():
                    col_idx += int(char)
                else:
                    board._grid[row_idx][col_idx] = char
                    col_idx += 1
        return board

    # ------------------------------------------------------------------
    # Square access
    # ------------------------------------------------------------------

    def set(self, square: str, piece: str) -> None:
        """Place a piece on a square. Use '' to clear."""
        row, col = _parse_square(square)
        self._grid[row][col] = piece

    def get(self, square: str) -> str:
        """Return the piece char on a square, or '' if empty."""
        row, col = _parse_square(square)
        return self._grid[row][col]

    def clear(self, square: str) -> None:
        self.set(square, "")

    # ------------------------------------------------------------------
    # FEN serialisation
    # ------------------------------------------------------------------

    def to_placement(self) -> str:
        """Return the piece-placement field of a FEN string (ranks 8→1)."""
        rows = []
        for row in self._grid:
            empty = 0
            row_str = ""
            for cell in row:
                if cell == "":
                    empty += 1
                else:
                    if empty:
                        row_str += str(empty)
                        empty = 0
                    row_str += cell
            if empty:
                row_str += str(empty)
            rows.append(row_str)
        return "/".join(rows)

    def to_fen(
        self,
        side_to_move: str = "w",
        castling: str = "-",
        en_passant: str = "-",
        halfmove: int = 0,
        fullmove: int = 1,
    ) -> str:
        """Return a complete FEN string for this board position."""
        return " ".join([
            self.to_placement(),
            side_to_move,
            castling,
            en_passant,
            str(halfmove),
            str(fullmove),
        ])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        lines = []
        for row_idx, row in enumerate(self._grid):
            rank = 8 - row_idx
            cells = [c if c else "." for c in row]
            lines.append(f"{rank}  {' '.join(cells)}")
        lines.append("   a b c d e f g h")
        return "\n".join(lines)


# ------------------------------------------------------------------
# Module-level square utilities (used by Board and ArmyPlacer)
# ------------------------------------------------------------------

def _parse_square(square: str):
    """'e4' -> (row=4, col=4) in grid coordinates."""
    col = ord(square[0].lower()) - ord("a")
    row = 8 - int(square[1])
    return row, col


def square_name(row: int, col: int) -> str:
    """(row=7, col=0) -> 'a1'"""
    return chr(ord("a") + col) + str(8 - row)
