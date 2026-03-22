from dataclasses import dataclass, field
from typing import List, Optional

from engine import EngineWrapper

# Result constants (from white's perspective)
WHITE_WINS = "white_wins"
BLACK_WINS = "black_wins"
DRAW = "draw"

# Variants where running out of pieces is a win for the mover
GIVEAWAY_VARIANTS = {"giveaway", "losers", "antichess"}


@dataclass
class MoveRecord:
    move: str
    score_cp: Optional[int]
    score_mate: Optional[int]
    time_ms: int


@dataclass
class BattleResult:
    result: str                      # WHITE_WINS, BLACK_WINS, or DRAW
    moves: List[str]                 # full move list in UCI notation
    records: List[MoveRecord]        # per-move scores and timing
    termination: str                 # 'checkmate', 'stalemate', 'draw_claim', 'time_forfeit'
    white_time_left: int             # ms remaining on white's clock
    black_time_left: int             # ms remaining on black's clock


class BattleRunner:
    """
    Runs a single engine-vs-engine game using two EngineWrapper instances.
    Engines must already be started before passing to BattleRunner.

    Usage:
        with EngineWrapper("engine.exe", variant="chess") as white, \
             EngineWrapper("engine.exe", variant="chess") as black:
            runner = BattleRunner(white, black, variant="chess")
            result = runner.run(wtime=10000, btime=10000, winc=100, binc=100)
            print(result.result, result.moves, result.termination)
    """

    def __init__(self, white: EngineWrapper, black: EngineWrapper, variant: str = "chess"):
        self.white = white
        self.black = black
        self.variant = variant

    def run(
        self,
        position: str = "startpos",
        wtime: int = 10000,
        btime: int = 10000,
        winc: int = 100,
        binc: int = 100,
        depth: Optional[int] = None,
    ) -> BattleResult:
        """
        Run a full game to completion and return a BattleResult.

        position: 'startpos' or 'fen <fen_string>'
        wtime/btime: starting time banks in ms (ignored when depth is set)
        winc/binc:   increment per move in ms
        depth:       fixed search depth per move; disables time-forfeit checks
        """
        self.white.new_game(self.variant)
        self.black.new_game(self.variant)

        engines = [self.white, self.black]
        moves: List[str] = []
        records: List[MoveRecord] = []

        # If the starting position has black to move, offset the turn counter
        offset = 1 if (position != "startpos" and " b " in position) else 0

        while True:
            turn = (len(moves) + offset) % 2  # 0 = white, 1 = black
            engine = engines[turn]

            bestmove, score, pv, time_used = engine.get_move(
                position, moves,
                wtime=wtime, btime=btime,
                winc=winc, binc=binc,
                depth=depth,
            )

            if score is None:
                raise RuntimeError(
                    "Engine returned no score. Moves so far: " + " ".join(moves)
                )

            record = MoveRecord(
                move=bestmove,
                score_cp=score.cp,
                score_mate=score.mate,
                time_ms=time_used,
            )

            # --- Terminal position (no legal moves) ---
            if not pv and bestmove == "(none)":
                if score.cp == 0:
                    return BattleResult(DRAW, moves, records, "stalemate", wtime, btime)
                elif score.mate == 0 and self.variant in GIVEAWAY_VARIANTS:
                    result = WHITE_WINS if turn == 0 else BLACK_WINS
                    return BattleResult(result, moves, records, "checkmate", wtime, btime)
                elif score.mate == 0:
                    result = BLACK_WINS if turn == 0 else WHITE_WINS
                    return BattleResult(result, moves, records, "checkmate", wtime, btime)
                else:
                    raise RuntimeError(
                        f"Unrecognised terminal position. Score: {score}. "
                        "Moves: " + " ".join(moves)
                    )

            # --- Draw claim (3-fold repetition or 50-move rule) ---
            if score.cp == 0 and pv and len(pv) == 1:
                return BattleResult(DRAW, moves, records, "draw_claim", wtime, btime)

            # --- Mate in 1: append the move then return ---
            if score.mate == 1:
                moves.append(bestmove)
                records.append(record)
                result = WHITE_WINS if turn == 0 else BLACK_WINS
                return BattleResult(result, moves, records, "checkmate", wtime, btime)

            # --- Normal move: update clocks and check for time forfeit ---
            if depth is None:
                if turn == 0:
                    wtime += winc - time_used
                    if wtime < 0:
                        moves.append(bestmove)
                        records.append(record)
                        return BattleResult(BLACK_WINS, moves, records, "time_forfeit", 0, btime)
                else:
                    btime += binc - time_used
                    if btime < 0:
                        moves.append(bestmove)
                        records.append(record)
                        return BattleResult(WHITE_WINS, moves, records, "time_forfeit", wtime, 0)

            moves.append(bestmove)
            records.append(record)
