from dataclasses import dataclass
from typing import Optional


@dataclass
class PieceDefinition:
    """
    Describes a single piece type for use in a VariantConfig.

    Either `predefined` (a Fairy-Stockfish built-in piece name) or `betza`
    (raw Betza notation) must be provided — not both.

    predefined examples: "chancellor", "amazon", "wazir", "commoner"
    betza examples:      "RN" (rook+knight), "KN" (king+knight), "BN" (bishop+knight)

    char is the single letter used to represent this piece in FEN strings and
    in the INI file. It must not collide with other pieces in the same variant.

    value_mg / value_eg override Fairy-Stockfish's internal piece values
    (midgame / endgame). Useful for RPG balance tuning.
    Reference: rook is approximately mg=1276, eg=1380.
    """

    name: str
    char: str
    predefined: Optional[str] = None
    betza: Optional[str] = None
    value_mg: Optional[int] = None
    value_eg: Optional[int] = None

    def __post_init__(self):
        if not self.predefined and not self.betza:
            raise ValueError(
                f"PieceDefinition '{self.name}' requires either 'predefined' or 'betza'."
            )
        if len(self.char) != 1 or not self.char.isalpha():
            raise ValueError(
                f"PieceDefinition '{self.name}' char must be a single letter, got '{self.char}'."
            )
