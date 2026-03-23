"""
sandbox.py — interactive playground for testing the battle system.

Run with:  python sandbox.py
"""

from engine import EngineWrapper
from ai import BattleRunner
from game import (
    PieceDefinition, VariantConfig, VariantWriter,
    Army, ArmyPlacer, Player, PieceInstance, Run, RunConfig, RunPhase,
    generate_encounter, apply_rewards,
)
from data.pieces import (
    PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING,
    COMMONER, CHANCELLOR, ARCHBISHOP, FERS, WAZIR, AMAZON, LANCE, CENTAUR,
)
from data.variants import STANDARD_CHESS, ONE_CENTAUR, CHANCELLOR_CHESS, CAPABLANCA_8
from data.piece_pool import POOL_CHANCELLOR, POOL_ARCHBISHOP, POOL_ROOK

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
    print(ini)
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
        start_fen="qnbqkbnq/pppppppp/8/8/8/8/PPPPPPPP/RNBCKBNR w KQ - 0 1",
    )

    ini = VariantWriter().write(config)
    print("Generated INI:\n" + open(ini).read())

    run_game("strong_chancellor", ini_path=ini, depth=4)


# ---------------------------------------------------------------------------
# Example 5 — RPG: player, roster, and piece leveling (no engine needed)
# ---------------------------------------------------------------------------
def example_player():
    print("=== Player & Roster ===")
    player = Player(name="Hero", gold=200)

    rook_inst   = player.add_to_roster(POOL_ROOK)
    chanc_inst  = player.add_to_roster(POOL_CHANCELLOR)

    # Put chancellor on d-file (slot 3) and rook on a-file (slot 0)
    player.set_slot(3, 1)   # slot 3 → roster index 1 (chancellor)
    player.set_slot(0, 0)   # slot 0 → roster index 0 (rook)

    army = player.current_army()
    print("Back rank:", [p.name for p in army.back_rank])

    # Level up the rook by granting XP
    for _ in range(3):
        leveled = rook_inst.grant_xp()
        if leveled:
            print(f"  {rook_inst.display_name} leveled up!")

    print(f"Rook lv={rook_inst.level}, value_mg={rook_inst.to_definition().value_mg}")
    print(player)
    print()


# ---------------------------------------------------------------------------
# Example 6 — RPG: encounter generation
# ---------------------------------------------------------------------------
def example_encounter():
    print("=== Encounter Generation ===")
    for floor in [1, 4, 8]:
        enc = generate_encounter(floor, seed=42)
        names = [p.name for p in enc.enemy.back_rank]
        print(f"  Floor {floor}: {names}")
    print()


# ---------------------------------------------------------------------------
# Example 7 — RPG: full run loop (no engine — simulates results)
# ---------------------------------------------------------------------------
def example_run_no_engine():
    print("=== Simulated Run (no engine) ===")
    from ai import WHITE_WINS, BLACK_WINS, DRAW
    from ai.battle_runner import BattleResult, MoveRecord

    player = Player(name="Hero", gold=100, lives=3)
    player.add_to_roster(POOL_CHANCELLOR)
    player.set_slot(3, 0)

    run = Run.new(player, RunConfig(total_floors=6, shop_interval=3), seed=0)

    # Simulate outcomes: win, win, win, draw, loss, win
    fake_outcomes = [WHITE_WINS, WHITE_WINS, WHITE_WINS, DRAW, BLACK_WINS, WHITE_WINS]

    for outcome in fake_outcomes:
        if run.over:
            break

        if run.in_shop:
            print(f"  [Shop] offers: {[o.definition.name for o in run.shop_offers()]}")
            if run.shop_offers():
                bought = run.buy(0)
                print(f"  Bought {run.player.roster[-1].definition.name if bought else '(failed)'}")
            run.skip_shop()

        enc = run.current_encounter()
        fake_result = BattleResult(
            result=outcome, moves=["e2e4", "e7e5"], records=[],
            termination="checkmate", white_time_left=5000, black_time_left=5000,
        )
        summary = run.resolve(fake_result)
        print(
            f"  Floor {run.floor - 1}: {outcome}  "
            f"+{summary.gold_earned}g  xp/piece={summary.xp_per_piece}  "
            f"leveled={summary.leveled_up}  life_lost={summary.life_lost}"
        )

    print(run)
    print()


# ---------------------------------------------------------------------------
# Example 8 — RPG: run a real battle inside a run (requires engine)
# ---------------------------------------------------------------------------
def example_run_with_engine():
    print("=== Real Run — Floor 1 ===")

    player = Player(name="Hero", gold=100)
    run = Run.new(player, RunConfig(total_floors=3), seed=7)

    enc = run.current_encounter()
    placer = ArmyPlacer()

    player_army = player.current_army()
    enemy_army  = enc.enemy

    config = placer.build_variant("run_floor1", player_army, enemy_army)
    ini    = VariantWriter().write(config)

    with EngineWrapper(ENGINE, variant=config.name, variant_path=ini) as white, \
         EngineWrapper(ENGINE, variant=config.name, variant_path=ini) as black:
        result = BattleRunner(white, black, variant=config.name).run(depth=4)

    summary = run.resolve(result)

    print(f"  Result : {result.result}")
    print(f"  Reward : +{summary.gold_earned}g, leveled={summary.leveled_up}")
    print(run)
    print()


# ---------------------------------------------------------------------------
# Run whichever examples you want
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example_player()
    example_encounter()
    example_run_no_engine()
    # example_run_with_engine()   # uncomment to run a real engine battle
