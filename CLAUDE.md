# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

`variantfishtest.py` runs automated matches between two UCI chess variant engines (primarily Fairy-Stockfish) and outputs ELO statistics and SPRT results. It is variant-agnostic and relies entirely on the engines' own rule implementation — no built-in legality checking.

## Running matches

```bash
# Basic match
python variantfishtest.py engine1_path engine2_path [options]

# Example from README (Xiangqi with NNUE eval files)
python variantfishtest.py stockfish1 --e1-options EvalFile=xiangqi-28d6221e2440.nnue stockfish2 --e2-options EvalFile=xiangqi-83f16c17fe26.nnue -t 10000 -i 100 -v xiangqi -b

# Full options
python variantfishtest.py -h
```

Key arguments:
- `-v` / `--variant`: Chess variant name (e.g. `chess`, `xiangqi`, `crazyhouse`). Comma-separate for multiple variants rotated randomly.
- `-c` / `--config`: Path to a `variants.ini` file for custom variant definitions.
- `-t` / `--time`: Base time per side in milliseconds (default 10000).
- `-i` / `--inc`: Time increment in milliseconds (default 100).
- `-n` / `--max_games`: Stop after this many games (default 5000).
- `-b` / `--book`: Use EPD opening book. Without a path, looks for `books/<variant>.epd`.
- `-s` / `--sprt`: Enable SPRT stopping criterion with `--elo0` / `--elo1` bounds.
- `-d1` / `-d2`: Depth limit per engine (default 13 plies each).
- `--verbosity`: 0=final only, 1=per-game stats, 2=moves, 3=debug.
- `-l` / `--log`: Append output to a file instead of stdout.

## Running the interactive GUI

```bash
python chess_rpg_main.py       # Human vs Fairy-Stockfish with Pygame GUI
python chess_rpg_autogame.py   # Engine vs engine with Pygame visualization
```

These require `pygame` and spawn Fairy-Stockfish processes directly.

## Statistical utilities

`stat_util.py` can be run standalone to verify SPRT logic:

```bash
python stat_util.py   # runs built-in unit tests
```

## Architecture

### Core match loop (`variantfishtest.py`)
`EngineMatch` parses CLI args, spawns two engines via `chess.uci.popen_engine()`, then loops:
1. `init_game()` — resets clocks and calls `ucinewgame`
2. `process_game()` → `play_game()` — alternates engine turns, tracks time banks, detects terminal positions from engine score/pv info
3. Accumulates W/L/D; optionally stops early via SPRT

Game result detection is score-based (not rule-based): the engine's reported score and PV length determine checkmate, stalemate, draw-by-repetition, and time forfeit.

### Statistics (`stat_util.py`)
Standalone math module. `get_elo(WLD)` returns ELO ± 95% CI and LOS. `SPRT(R, elo0, alpha, elo1, beta, drawelo)` returns `{'finished', 'state', 'llr', 'lower_bound', 'upper_bound'}`.

### Variant configuration (`variants*.ini`)
INI files passed to Fairy-Stockfish via the `VariantPath` UCI option. Define custom pieces, start FEN, promotion rules, and win conditions. `variants.ini` is the working config; `variants_orig.ini` is the upstream reference.

### Chess library (`chess/`)
A local fork of python-chess providing `chess.uci` (UCI protocol wrapper). Not pip-installed — imported directly from the `chess/` subdirectory.

### GUI components (`chess_rpg_*.py`)
- `chess_rpg_config.py`: Window/board constants and custom piece names.
- `chess_rpg_functions.py`: FEN ↔ numpy array conversion, Pygame rendering, move animation, engine init helpers.
- `chess_rpg_main.py`: Interactive player vs engine game loop.
- `chess_rpg_autogame.py`: Fully automated engine vs engine with visualization.

### Engine binaries
Six Fairy-Stockfish `.exe` files are included in the repo root, distinguished by architecture (`x86-64-bmi2` vs `x86-64-modern`) and purpose (`-legal_moves` variant used for querying legal moves in the GUI, `-player2` for the second engine).

### Experimental test scripts
`engine_test.py`, `fairy_piece_test.py`, `function_test.py`, `skill_level_test.py` invoke `variantfishtest.py` as a subprocess with varying parameters, collect results into pandas DataFrames, and export to `.xlsx`.

## Dependencies

- `chess` (local fork in `chess/` — do not `pip install chess`)
- `pygame` (for GUI scripts)
- `numpy` (for board array representation in GUI)
- `pandas` (for experimental test scripts)
- Fairy-Stockfish binaries (included as `.exe` files)

## Project Direction (Important)

This repository is evolving into a **roguelike chess autobattler RPG**, not just a testing harness.

The existing codebase (variantfishtest, test scripts, GUI prototypes) should be treated as:
- Experimental scaffolding
- Reference implementations for engine interaction
- Tools for balancing and simulation

### Long-term goals

- Automated AI vs AI battles driven by Fairy-Stockfish
- Custom chess pieces defined via Betza notation and variants.ini
- A progression system where players:
  - Build teams / armies (custom piece sets)
  - Upgrade pieces over time
  - Unlock new mechanics and variants
- Procedural or semi-procedural battle setups
- Visualisation via Pygame (or similar)

### Architectural direction

The project should gradually move toward a modular structure:

- `engine/` → communication with Fairy-Stockfish (UCI layer)
- `game/` → rules, board state, piece definitions
- `ai/` → orchestration of battles (engine vs engine logic)
- `ui/` → rendering, animation, interaction
- `data/` → variants.ini, piece definitions, configs

### Guidance for modifications

- Do NOT tightly couple new features to `variantfishtest.py`
- Prefer extracting reusable components (engine wrapper, game loop)
- Treat current scripts as prototypes to refactor, not final architecture
- Prioritise building reusable systems over one-off experiments

### Current priority

Focus on building a **clean engine-vs-engine battle loop** that can:
- Load a FEN or variant
- Run a full game deterministically
- Output a move list and result
- Be reused later by the RPG layer
