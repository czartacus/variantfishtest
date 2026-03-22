from .army import Army
from .board import Board, square_name
from .piece_definition import PieceDefinition
from .variant_config import VariantConfig

_DEFAULT_PAWN = PieceDefinition("pawn", "p", predefined="pawn")


class ArmyPlacer:
    """
    Places two Army objects onto a Board in standard formation and
    optionally builds a VariantConfig ready to be written to an INI file.

    White occupies ranks 1–2, black occupies ranks 7–8.
    """

    def place(self, white: Army, black: Army) -> Board:
        """
        Return a Board with both armies placed.

        White back rank → rank 1 (uppercase chars)
        White pawns     → rank 2
        Black pawns     → rank 7
        Black back rank → rank 8 (lowercase chars)
        """
        board = Board()

        white_pawn = white.pawn or _DEFAULT_PAWN
        black_pawn = black.pawn or _DEFAULT_PAWN

        for col in range(8):
            # White
            board.set(square_name(7, col), white.back_rank[col].char.upper())
            board.set(square_name(6, col), white_pawn.char.upper())
            # Black
            board.set(square_name(0, col), black.back_rank[col].char.lower())
            board.set(square_name(1, col), black_pawn.char.lower())

        return board

    def place_to_fen(
        self,
        white: Army,
        black: Army,
        side_to_move: str = "w",
        castling: str = "-",
    ) -> str:
        """Place both armies and return a complete FEN string."""
        board = self.place(white, black)
        return board.to_fen(side_to_move=side_to_move, castling=castling)

    def build_variant(
        self,
        name: str,
        white: Army,
        black: Army,
        base: str = "chess",
        side_to_move: str = "w",
        castling: str = "-",
    ) -> VariantConfig:
        """
        Build a complete VariantConfig from two armies.

        Collects all non-standard piece types from both armies,
        generates the start FEN, and returns a VariantConfig ready
        to be written with VariantWriter.

        Standard chess pieces (p n b r q k) inherited from base="chess"
        are excluded from the pieces list automatically — they don't need
        to be declared in the INI.

        Example:
            placer = ArmyPlacer()
            config = placer.build_variant("battle_001", white_army, black_army)
            ini_path = VariantWriter().write(config)
        """
        # Collect piece types that need explicit INI declaration.
        # Standard chess pieces are always available via base="chess".
        _STANDARD_CHARS = {"p", "n", "b", "r", "q", "k"}
        seen_chars = set()
        extra_pieces = []

        for army in (white, black):
            for piece in army.unique_piece_types():
                if piece.char.lower() not in _STANDARD_CHARS and piece.char.lower() not in seen_chars:
                    seen_chars.add(piece.char.lower())
                    extra_pieces.append(piece)

        fen = self.place_to_fen(white, black, side_to_move=side_to_move, castling=castling)

        return VariantConfig(
            name=name,
            base=base,
            pieces=extra_pieces,
            start_fen=fen,
        )
