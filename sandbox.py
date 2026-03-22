"""
sandbox.py — interactive playground for testing the battle system.

Run with:  python sandbox.py
"""

from engine import EngineWrapper
from ai import BattleRunner
from game import PieceDefinition, VariantConfig, VariantWriter
from data.pieces import (
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    COMMONER, CHANCELLOR, ARCHBISHOP, FERS, WAZIR, AMAZON, LANCE, CENTAUR,
)
from data.variants import STANDARD_CHESS, ONE_CENTAUR, CHANCELLOR_CHESS, CAPABLANCA_8

ENGINE = "fairy-stockfish_x86-64-bmi2.exe"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_game(variant_name, ini_path=None, depth=4, wtime=None, btime=None, winc=100, binc=100):
    """Run one game and print a summary."""
    kwargs = {"depth": depth} if wtime is None else {"wtime": wtime, "btime": btime, "winc": winc, "binc": binc}
    with EngineWrapper(ENGINE, variant=variant_name, variant_path=ini_path) as white, \
         EngineWrapper(ENGINE, variant=variant_name, variant_path=ini_path) as black:
        result = BattleRunner(white, black, variant=variant_name).run(**kwargs)

    print(f"Result      : {result.result}")
    print(f"Termination : {result.termination}")
    print(f"Moves       : {len(result.moves)}")
    print(f"Move list   : {' '.join(result.moves)}")
    print()
    return result


# ---------------------------------------------------------------------------
# Example 1 — standard chess at depth 4
# ---------------------------------------------------------------------------
def example_standard():
    print("=== Standard Chess ===")
    run_game("chess", depth=4)


# ---------------------------------------------------------------------------
# Example 2 — pre-built variant from data/variants.py
# ---------------------------------------------------------------------------
def example_prebuilt():
    print("=== Chancellor Chess ===")
    ini = VariantWriter().write(CHANCELLOR_CHESS)
    run_game("chancellorchess", ini_path=ini, depth=4)


# ---------------------------------------------------------------------------
# Example 3 — define your own piece and variant from scratch
# ---------------------------------------------------------------------------
def example_custom_piece():
    print("=== Custom Piece: Supernight (NF) ===")

    # Define a piece using Betza notation
    # NF = knight leaps + one-square diagonal (fers)
    supernight = PieceDefinition("supernight", "x", betza="NF")

    config = VariantConfig(
        name="supernight_test",
        base="chess",
        pieces=[supernight],
        start_fen="rxbqkbxr/pppppppp/8/8/8/8/PPPPPPPP/RXBQKBXR w KQkq - 0 1",
    )

    ini = VariantWriter().write(config)
    print("Generated INI:\n" + open(ini).read())

    run_game("supernight_test", ini_path=ini, depth=4)


# ---------------------------------------------------------------------------
# Example 4 — override piece values (balance tuning)
# ---------------------------------------------------------------------------
def example_piece_values():
    print("=== Chancellor with custom value ===")

    strong_chancellor = PieceDefinition(
        "chancellor", "c",
        predefined="chancellor",
        value_mg=1500,  # default is ~1270 (same as rook)
        value_eg=1600,
    )

    config = VariantConfig(
        name="strong_chancellor",
        base="chess",
        pieces=[strong_chancellor],
        start_fen="rnbckcbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBCKCBNR w KQkq - 0 1",
    )

    ini = VariantWriter().write(config)
    print("Generated INI:\n" + open(ini).read())

    run_game("strong_chancellor", ini_path=ini, depth=4)


# ---------------------------------------------------------------------------
# Run whichever examples you want
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example_standard()
    example_prebuilt()
    example_custom_piece()
    example_piece_values()
