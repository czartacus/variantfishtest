from dataclasses import dataclass, field
from typing import List, Optional

from .piece_definition import PieceDefinition


@dataclass
class Army:
    """
    The piece set for one side of a battle.

    back_rank: exactly 8 PieceDefinitions, ordered a-file to h-file.
               These fill rank 1 (white) or rank 8 (black).

    pawn:      the piece used to fill the pawn rank.
               Defaults to a standard pawn ('p') if None.

    name:      human-readable label used in logs and the RPG UI.

    Example — standard chess army:
        from data.pieces import PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING
        Army(
            name="Classical",
            back_rank=[ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK],
            pawn=PAWN,
        )

    Example — chancellor replaces queen:
        Army(
            name="Chancellor Army",
            back_rank=[ROOK, KNIGHT, BISHOP, CHANCELLOR, KING, BISHOP, KNIGHT, ROOK],
            pawn=PAWN,
        )
    """

    name: str
    back_rank: List[PieceDefinition]
    pawn: Optional[PieceDefinition] = None

    def __post_init__(self):
        if len(self.back_rank) != 8:
            raise ValueError(
                f"Army '{self.name}': back_rank must have exactly 8 pieces, "
                f"got {len(self.back_rank)}."
            )

    def unique_piece_types(self) -> List[PieceDefinition]:
        """
        Return deduplicated list of all piece types in this army
        (back rank + pawn). Used by VariantConfig to know which pieces
        need to be declared in the INI.
        """
        seen = set()
        result = []
        candidates = list(self.back_rank)
        if self.pawn:
            candidates.append(self.pawn)
        for piece in candidates:
            if piece.char not in seen:
                seen.add(piece.char)
                result.append(piece)
        return result
