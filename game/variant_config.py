from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .piece_definition import PieceDefinition


@dataclass
class VariantConfig:
    """
    Describes a complete chess variant for Fairy-Stockfish.

    `pieces` should list only the pieces that need to be explicitly declared
    in the INI section — i.e. pieces that are new or not present in the base
    variant. When base="chess", the standard pieces (p n b r q k) are already
    available without declaration.

    `promotions` maps the char of the piece that promotes to the char of what
    it promotes into, e.g. {"p": "q"}. If empty, the base variant's promotion
    rules apply unchanged. If non-empty, default promotions are disabled and
    only the specified mappings apply.

    `win_condition`:
      "checkmate"  — standard (default)
      "extinction" — a side loses when all of its `extinction_piece` are gone

    Example — adding a chancellor to standard chess:
        VariantConfig(
            name="battle_001",
            base="chess",
            pieces=[PieceDefinition("chancellor", "c", predefined="chancellor")],
            start_fen="rnbckcbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBCKCBNR w KQkq - 0 1",
        )
    """

    name: str
    base: str = "chess"
    pieces: List[PieceDefinition] = field(default_factory=list)
    start_fen: Optional[str] = None
    promotions: Dict[str, str] = field(default_factory=dict)
    win_condition: str = "checkmate"
    extinction_piece: Optional[str] = None  # char of the piece type that triggers extinction
