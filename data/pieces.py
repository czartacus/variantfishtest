"""
Canonical piece definitions for the RPG.

Standard chess pieces use their conventional FEN letters.
Fairy pieces use the letters established in chess_rpg_config.py.

Import individual pieces by name:
    from data.pieces import CHANCELLOR, AMAZON, WAZIR

Or look up by char:
    from data.pieces import BY_CHAR
    piece = BY_CHAR["c"]  # -> CHANCELLOR
"""

from game.piece_definition import PieceDefinition

# ---------------------------------------------------------------------------
# Standard chess pieces (inherited from base="chess" — no INI declaration
# needed unless overriding their char or values)
# ---------------------------------------------------------------------------
PAWN     = PieceDefinition("pawn",   "p", predefined="pawn")
KNIGHT   = PieceDefinition("knight", "n", predefined="knight")
BISHOP   = PieceDefinition("bishop", "b", predefined="bishop")
ROOK     = PieceDefinition("rook",   "r", predefined="rook")
QUEEN    = PieceDefinition("queen",  "q", predefined="queen")
KING     = PieceDefinition("king",   "k", predefined="king")

# ---------------------------------------------------------------------------
# Fairy pieces (must be declared in the INI when used)
# Letters match chess_rpg_config.py for consistency with existing assets.
# ---------------------------------------------------------------------------

# Commoner (s) — moves like a king but is not royal
COMMONER   = PieceDefinition("commoner",   "s", predefined="commoner")

# Chancellor (c) — rook + knight
CHANCELLOR = PieceDefinition("chancellor", "c", predefined="chancellor")

# Archbishop (m) — bishop + knight
ARCHBISHOP = PieceDefinition("archbishop", "m", predefined="archbishop")

# Fers (f) — moves one square diagonally
FERS       = PieceDefinition("fers",       "f", predefined="fers")

# Wazir (w) — moves one square orthogonally
WAZIR      = PieceDefinition("wazir",      "w", predefined="wazir")

# Amazon (a) — queen + knight (most powerful standard fairy piece)
AMAZON     = PieceDefinition("amazon",     "a", predefined="amazon")

# Lance (l) — moves any number of squares forward only
LANCE      = PieceDefinition("lance",      "l", predefined="lance")

# Centaur (t) — king + knight
CENTAUR    = PieceDefinition("centaur",    "t", predefined="centaur")

# ---------------------------------------------------------------------------
# Lookup table: char -> PieceDefinition
# ---------------------------------------------------------------------------
BY_CHAR: dict = {
    p.char: p
    for p in [
        PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
        COMMONER, CHANCELLOR, ARCHBISHOP, FERS, WAZIR, AMAZON, LANCE, CENTAUR,
    ]
}
