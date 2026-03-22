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
# Black's two middle pawns (d7, e7) are replaced by centaurs (char 't').
# ---------------------------------------------------------------------------
ONE_CENTAUR = VariantConfig(
    name="onecentaur",
    base="chess",
    pieces=[CENTAUR],
    start_fen="rnbqkbnr/pppttppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1",
)

# ---------------------------------------------------------------------------
# Chancellor Chess — replaces queens with chancellors on both sides.
# Back rank: r n b c k b n r  (chancellor on d-file, 8 pieces total)
# ---------------------------------------------------------------------------
CHANCELLOR_CHESS = VariantConfig(
    name="chancellorchess",
    base="chess",
    pieces=[CHANCELLOR],
    start_fen="rnbckbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBCKBNR w KQkq - 0 1",
)

# ---------------------------------------------------------------------------
# Capablanca 8x8 — knights replaced by archbishop (m) and chancellor (c).
# Back rank: r m b q k b c r  (archbishop on b-file, chancellor on g-file)
# ---------------------------------------------------------------------------
CAPABLANCA_8 = VariantConfig(
    name="capablanca8",
    base="chess",
    pieces=[ARCHBISHOP, CHANCELLOR],
    start_fen="rmbqkbcr/pppppppp/8/8/8/8/PPPPPPPP/RMBQKBCR w KQkq - 0 1",
)
