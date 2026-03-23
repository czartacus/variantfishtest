"""
Piece pool for the RPG encounter and shop systems.

Each entry is a (PieceDefinition, power, tier) tuple:

  power — rough centipawn-equivalent strength used by the encounter
          generator's budget system (not the same as Fairy-SF internal
          values, which are ~8× larger).

  tier  — 1 = floors 1-3  (basic)
           2 = floors 4-6  (compound)
           3 = floors 7+   (powerful)

PieceDefinitions here include value_mg/value_eg overrides so that
PieceInstance level bonuses have a meaningful base to scale from.
Approximate Fairy-SF internal values: rook ≈ mg 1276, eg 1380.
"""

from game.piece_definition import PieceDefinition

# ---------------------------------------------------------------------------
# Tier 1 — basic pieces
# ---------------------------------------------------------------------------
POOL_KNIGHT = PieceDefinition("knight", "n", predefined="knight",
                              value_mg=781,  value_eg=854)
POOL_BISHOP = PieceDefinition("bishop", "b", predefined="bishop",
                              value_mg=825,  value_eg=915)
POOL_ROOK   = PieceDefinition("rook",   "r", predefined="rook",
                              value_mg=1276, value_eg=1380)
POOL_QUEEN  = PieceDefinition("queen",  "q", predefined="queen",
                              value_mg=2538, value_eg=2682)

# ---------------------------------------------------------------------------
# Tier 2 — compound pieces
# ---------------------------------------------------------------------------
POOL_CHANCELLOR = PieceDefinition("chancellor", "c", predefined="chancellor",
                                  value_mg=2000, value_eg=2150)
POOL_ARCHBISHOP = PieceDefinition("archbishop", "m", predefined="archbishop",
                                  value_mg=1850, value_eg=1960)
POOL_CENTAUR    = PieceDefinition("centaur",    "t", predefined="centaur",
                                  value_mg=1900, value_eg=2000)
POOL_COMMONER   = PieceDefinition("commoner",   "s", predefined="commoner",
                                  value_mg=700,  value_eg=800)

# ---------------------------------------------------------------------------
# Tier 3 — powerful pieces
# ---------------------------------------------------------------------------
POOL_AMAZON = PieceDefinition("amazon", "a", predefined="amazon",
                              value_mg=3000, value_eg=3100)

# ---------------------------------------------------------------------------
# Pool table: (definition, power_rating, tier)
# power_rating in rough centipawns for budget calculations
# ---------------------------------------------------------------------------
PIECE_POOL: list = [
    # tier 1
    (POOL_KNIGHT,     325, 1),
    (POOL_BISHOP,     350, 1),
    (POOL_ROOK,       500, 1),
    (POOL_QUEEN,      975, 1),
    # tier 2
    (POOL_CHANCELLOR, 850, 2),
    (POOL_ARCHBISHOP, 830, 2),
    (POOL_CENTAUR,    870, 2),
    (POOL_COMMONER,   280, 2),
    # tier 3
    (POOL_AMAZON,    1200, 3),
]

# Quick lookup: char -> (definition, power, tier)
BY_CHAR: dict = {entry[0].char: entry for entry in PIECE_POOL}
