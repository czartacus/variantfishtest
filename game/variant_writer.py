import os
import tempfile
from typing import Optional

from .variant_config import VariantConfig


# All piece type names recognised by Fairy-Stockfish as built-ins.
# These are written as `<name> = <char>` in the INI.
# Anything not in this set must use a customPiece slot with Betza notation.
PREDEFINED_PIECES = {
    "pawn", "knight", "bishop", "rook", "queen", "king",
    "fers", "alfil", "fersAlfil", "silver", "aiwok", "bers",
    "archbishop", "chancellor", "amazon",
    "knibis", "biskni", "kniroo", "rookni",
    "shogiPawn", "lance", "shogiKnight", "gold", "dragonHorse",
    "clobber", "breakthrough", "immobile",
    "cannon", "janggiCannon", "soldier",
    "horse", "elephant", "janggiElephant", "banner",
    "wazir", "commoner", "centaur",
}


class VariantWriter:
    """
    Converts a VariantConfig into a Fairy-Stockfish variants.ini file.

    Usage:
        writer = VariantWriter()
        path = writer.write(config)               # temp file
        path = writer.write(config, "my.ini")     # specific path
    """

    def write(self, config: VariantConfig, path: Optional[str] = None) -> str:
        """
        Serialise config to an INI file and return the absolute path written to.
        If path is None a temporary file is created and its path returned.
        """
        content = self._build(config)
        if path is None:
            fd, path = tempfile.mkstemp(suffix=".ini", prefix="variant_")
            os.close(fd)
        path = os.path.abspath(path)
        with open(path, "w") as f:
            f.write(content)
        return path

    def _build(self, config: VariantConfig) -> str:
        lines = [f"[{config.name}:{config.base}]"]

        # --- Piece declarations ---
        custom_slot = 1
        for piece in config.pieces:
            if piece.predefined and piece.predefined in PREDEFINED_PIECES:
                lines.append(f"{piece.predefined} = {piece.char}")
            else:
                if custom_slot > 25:
                    raise ValueError("Exceeded maximum of 25 custom piece slots.")
                lines.append(f"customPiece{custom_slot} = {piece.char}:{piece.betza}")
                custom_slot += 1

        # --- Promotion rules ---
        if config.promotions:
            lines.append("promotionPieceTypes = -")
            promo_str = " ".join(f"{k}:{v}" for k, v in config.promotions.items())
            lines.append(f"promotedPieceType = {promo_str}")

        # --- Win condition ---
        if config.win_condition == "extinction" and config.extinction_piece:
            lines.append("extinctionValue = loss")
            lines.append(f"extinctionPieceTypes = {config.extinction_piece}")

        # --- Starting position ---
        if config.start_fen:
            lines.append(f"startFen = {config.start_fen}")

        # --- Piece value overrides ---
        mg_parts = [
            f"{p.char}:{p.value_mg}"
            for p in config.pieces
            if p.value_mg is not None
        ]
        eg_parts = [
            f"{p.char}:{p.value_eg}"
            for p in config.pieces
            if p.value_eg is not None
        ]
        if mg_parts:
            lines.append(f"pieceValueMg = {' '.join(mg_parts)}")
        if eg_parts:
            lines.append(f"pieceValueEg = {' '.join(eg_parts)}")

        return "\n".join(lines) + "\n"
