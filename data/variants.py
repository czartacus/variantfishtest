"""
Pre-built VariantConfig objects.

These mirror the hand-written INI files in the repo root and serve as
the canonical Python representation of those variants.
"""

from game.variant_config import VariantConfig
from game.piece_definition import PieceDefinition

# Re-use chars from pieces.py but create separate instances so callers
# can freely modify copies without affecting the canonical definitions.
from data.pieces import (
    CENTAUR, CHANCELLOR, ARCHBISHOP, COMMONER, AMAZON,
)

# ---------------------------------------------------------------------------
# Standard chess — base reference, not written to INI (engine handles it)
# ---------------------------------------------------------------------------
STANDARD_CHESS = VariantConfig(
    name="chess",
    base="chess",
    pieces=[],
    start_fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
)

# ---------------------------------------------------------------------------
# One Centaur — mirrors variants.ini [onecentaur:chess]
# Black's two middle pawns are replaced by centaurs (char 't').
# ---------------------------------------------------------------------------
ONE_CENTAUR = VariantConfig(
    name="onecentaur",
    base="chess",
    pieces=[CENTAUR],
    start_fen="rnbqkbnr/ppptttppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1",
)

# ---------------------------------------------------------------------------
# Chancellor Chess — replaces queens with chancellors on both sides
# ---------------------------------------------------------------------------
CHANCELLOR_CHESS = VariantConfig(
    name="chancellorchess",
    base="chess",
    pieces=[CHANCELLOR],
    start_fen="rnbckcbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBCKCBNR w KQkq - 0 1",
)

# ---------------------------------------------------------------------------
# Capablanca-style — adds archbishop (bishop+knight) and chancellor (rook+knight)
# on a standard 8x8 board as queen replacements
# ---------------------------------------------------------------------------
CAPABLANCA_8 = VariantConfig(
    name="capablanca8",
    base="chess",
    pieces=[ARCHBISHOP, CHANCELLOR],
    start_fen="rmbqkcmnr/pppppppp/8/8/8/8/PPPPPPPP/RMBQKCMNR w KQkq - 0 1",
)
