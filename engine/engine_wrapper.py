import os
import chess.uci


class EngineWrapper:
    """
    Wraps a single UCI engine process (Fairy-Stockfish or compatible).
    Handles spawn, option setting, position sending, and move retrieval.

    Usage:
        with EngineWrapper("fairy-stockfish.exe", variant="chess") as engine:
            engine.new_game()
            bestmove, score, pv, time_used = engine.get_move("startpos", [])

    Or manually:
        engine = EngineWrapper("fairy-stockfish.exe", variant="xiangqi", variant_path="variants.ini")
        engine.start()
        engine.new_game()
        bestmove, score, pv, time_used = engine.get_move("startpos", [], depth=13)
        engine.quit()
    """

    def __init__(self, path, variant=None, variant_path=None, options=None):
        """
        path:         path to engine executable
        variant:      UCI_Variant string (e.g. 'chess', 'xiangqi', 'crazyhouse')
        variant_path: path to variants.ini for custom variants
        options:      dict of additional UCI options, e.g. {'EvalFile': 'net.nnue'}
        """
        self.path = os.path.abspath(path)
        self.variant = variant
        self.variant_path = variant_path
        self.options = options or {}
        self._engine = None
        self._info_handler = None

    def start(self):
        """Spawn the engine process and apply all options."""
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Engine not found: {self.path}")
        self._engine = chess.uci.popen_engine(self.path)
        self._engine.uci()
        self._info_handler = chess.uci.InfoHandler()
        self._engine.info_handlers.append(self._info_handler)
        self._apply_options()

    def _apply_options(self):
        if self.variant_path:
            self._engine.setoption({"VariantPath": self.variant_path})
        if self.variant:
            self._engine.setoption({"UCI_Variant": self.variant})
        if self.options:
            self._engine.setoption(self.options)

    def new_game(self, variant=None):
        """
        Signal the start of a new game and reset engine state.
        Optionally switch to a different variant.
        """
        if variant:
            self.variant = variant
            self._engine.setoption({"UCI_Variant": self.variant})
        self._engine.ucinewgame()

    def get_move(self, position, moves, wtime=None, btime=None, winc=0, binc=0, depth=None):
        """
        Send a position and retrieve the best move.

        position:  'startpos' or 'fen <fen_string>'
        moves:     list of moves played so far in UCI notation (e.g. ['e2e4', 'e7e5'])
        wtime:     white time remaining in ms
        btime:     black time remaining in ms
        winc:      white increment in ms
        binc:      black increment in ms
        depth:     max search depth in plies

        Returns: (bestmove, score, pv, time_used)
            bestmove:  str UCI move e.g. 'e2e4', or '(none)' at terminal position
            score:     chess.uci.Score(cp, mate, lowerbound, upperbound) or None
            pv:        list of moves in the principal variation, or []
            time_used: int ms the engine spent on this move
        """
        self._engine.send_line("position {} moves {}".format(position, " ".join(moves)))

        go_kwargs = {"winc": winc, "binc": binc}
        if wtime is not None:
            go_kwargs["wtime"] = wtime
        if btime is not None:
            go_kwargs["btime"] = btime
        if depth is not None:
            go_kwargs["depth"] = depth

        bestmove, _ = self._engine.go(**go_kwargs)

        with self._info_handler:
            score = self._info_handler.info.get("score", {}).get(1)
            pv = self._info_handler.info.get("pv", {}).get(1, [])
            time_used = self._info_handler.info.get("time", 0)

        return bestmove, score, pv, time_used

    def quit(self):
        """Terminate the engine process."""
        if self._engine:
            self._engine.quit()
            self._engine = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.quit()
