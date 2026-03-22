"""
dev_ui.py — Development sandbox for the chess variant battle system.

  - Drag pieces from the library onto the board to set up a position.
  - Toggle W / B to choose which colour to place.
  - Right-click a board square to remove the piece on it.
  - Click PLAY to run an engine match in the background.
  - Watch auto-playback, then use < PREV / NEXT > (or arrow keys) to review.
  - Click NEW MATCH to return to setup.
"""

import os
import copy
import threading
import time

import pygame

from game import Board, VariantConfig, VariantWriter
from game.board import square_name
from data.pieces import BY_CHAR
from engine import EngineWrapper
from ai import BattleRunner

# ---------------------------------------------------------------------------
# User-configurable
# ---------------------------------------------------------------------------
MOVE_DELAY = 0.25                           # seconds between auto-playback moves
ENGINE     = "fairy-stockfish_x86-64-bmi2.exe"
DEPTH      = 4

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
SQ_SIZE  = 64
BOARD_W  = SQ_SIZE * 8   # 512
BOARD_H  = SQ_SIZE * 8   # 512
PANEL_X  = BOARD_W
PANEL_W  = 290
WIN_W    = BOARD_W + PANEL_W
WIN_H    = BOARD_H

# Piece library  — 14 pieces, rendered as 2 columns × 7 rows
# Each row: (left_char, left_name, right_char, right_name)
PIECE_ROWS = [
    ("p", "Pawn",      "c", "Chancellor"),
    ("n", "Knight",    "m", "Archbishop"),
    ("b", "Bishop",    "f", "Fers"),
    ("r", "Rook",      "w", "Wazir"),
    ("q", "Queen",     "a", "Amazon"),
    ("k", "King",      "l", "Lance"),
    ("s", "Commoner",  "t", "Centaur"),
]
# Flat list of (char, name) for indexing
PIECE_LIST = [(c, n) for row in PIECE_ROWS for (c, n) in ((row[0], row[1]), (row[2], row[3]))]

TILE_W       = 133
TILE_H       = 40
LIB_START_Y  = 28    # y of first tile row in the panel

# Derived panel element positions
_LIB_H     = len(PIECE_ROWS) * TILE_H
TOGGLE_Y   = LIB_START_Y + _LIB_H + 12
PLAY_Y     = TOGGLE_Y + 44
STATUS_Y   = PLAY_Y + 50
NAV_Y      = STATUS_Y + 56
NEW_BTN_Y  = NAV_Y + 48

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
C_LIGHT       = (240, 217, 181)
C_DARK        = (181, 136, 99)
C_PANEL       = (42, 42, 46)
C_TILE_NORM   = (58, 58, 64)
C_TILE_HOV    = (78, 78, 88)
C_TEXT        = (215, 215, 215)
C_DIM         = (130, 130, 135)
C_BTN_GREEN   = (55, 125, 65)
C_BTN_GREEN_H = (75, 155, 85)
C_BTN_GREY    = (72, 72, 80)
C_BTN_GREY_H  = (95, 95, 105)
C_BTN_BLUE    = (50, 90, 150)
C_BTN_BLUE_H  = (70, 115, 180)
C_COMPUTING   = (200, 165, 55)
C_LAST_MOVE   = (80, 160, 80)    # tint on last-move squares

# ---------------------------------------------------------------------------
# App states
# ---------------------------------------------------------------------------
SETUP     = "setup"
COMPUTING = "computing"
PLAYING   = "playing"
REVIEW    = "review"

# Chars that ship with PNG assets in assets/
ASSET_CHARS   = {"p", "n", "b", "r", "q", "k", "s", "m"}
STANDARD_CHARS = {"p", "n", "b", "r", "q", "k"}

# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------

def _load_piece_images(sq_size: int) -> dict:
    """Return {('w'|'b', char): Surface} at sq_size × sq_size."""
    font = pygame.font.SysFont("Arial", sq_size // 2, bold=True)
    images = {}
    all_chars = {c for (c, _) in PIECE_LIST}
    for char in all_chars:
        for color in ("w", "b"):
            key = (color, char)
            if char in ASSET_CHARS:
                path = os.path.join("assets", f"{color}{char}.png")
                if os.path.exists(path):
                    img = pygame.image.load(path).convert_alpha()
                    images[key] = pygame.transform.smoothscale(img, (sq_size, sq_size))
                    continue
            # Fallback: coloured rounded rect + letter
            surf = pygame.Surface((sq_size, sq_size), pygame.SRCALPHA)
            bg  = (210, 210, 210, 235) if color == "w" else (55, 55, 55, 235)
            bdr = (100, 100, 100)      if color == "w" else (170, 170, 170)
            tc  = (30,  30,  30)       if color == "w" else (210, 210, 210)
            pygame.draw.rect(surf, bg,  (3, 3, sq_size - 6, sq_size - 6), border_radius=6)
            pygame.draw.rect(surf, bdr, (3, 3, sq_size - 6, sq_size - 6), 2, border_radius=6)
            label = font.render(char.upper(), True, tc)
            surf.blit(label, label.get_rect(center=(sq_size // 2, sq_size // 2)))
            images[key] = surf
    return images

# ---------------------------------------------------------------------------
# Move application
# ---------------------------------------------------------------------------

def _apply_uci_move(board: Board, move: str) -> Board:
    """Return a new Board with the UCI move applied (handles castling & en passant)."""
    board = copy.deepcopy(board)
    src, dst = move[:2], move[2:4]
    promo = move[4].lower() if len(move) == 5 else None
    piece = board.get(src)
    if not piece:
        return board
    captured = board.get(dst)
    board.set(dst, piece)
    board.clear(src)
    # Promotion
    if promo:
        board.set(dst, promo.upper() if piece.isupper() else promo)
    # Castling — king moves two files
    if piece.lower() == "k":
        sc = ord(src[0]) - ord("a")
        dc = ord(dst[0]) - ord("a")
        rank = src[1]
        if dc - sc == 2:    # kingside
            board.set(f"f{rank}", board.get(f"h{rank}"))
            board.clear(f"h{rank}")
        elif dc - sc == -2:  # queenside
            board.set(f"d{rank}", board.get(f"a{rank}"))
            board.clear(f"a{rank}")
    # En passant — pawn moves diagonally onto empty square
    if piece.lower() == "p":
        sc = ord(src[0]) - ord("a")
        dc = ord(dst[0]) - ord("a")
        if sc != dc and not captured:
            board.clear(f"{dst[0]}{src[1]}")
    return board

# ---------------------------------------------------------------------------
# Variant inference from board
# ---------------------------------------------------------------------------

def _build_variant_for_board(board: Board) -> str:
    """
    Scan board, collect non-standard piece chars, build a VariantConfig,
    write to sandbox_variant.ini, return ini path.
    """
    seen, extra = set(), []
    for row in range(8):
        for col in range(8):
            piece = board.get(square_name(row, col))
            if not piece:
                continue
            char = piece.lower()
            if char not in STANDARD_CHARS and char not in seen:
                seen.add(char)
                if char in BY_CHAR:
                    extra.append(BY_CHAR[char])
    config   = VariantConfig(name="sandbox", base="chess", pieces=extra)
    ini_path = VariantWriter().write(config, "sandbox_variant.ini")
    return ini_path

# ---------------------------------------------------------------------------
# Match thread
# ---------------------------------------------------------------------------

def _run_match(board: Board, result_box: dict):
    try:
        ini  = _build_variant_for_board(board)
        fen  = board.to_fen()
        with EngineWrapper(ENGINE, variant="sandbox", variant_path=ini) as white, \
             EngineWrapper(ENGINE, variant="sandbox", variant_path=ini) as black:
            result = BattleRunner(white, black, variant="sandbox").run(
                position=f"fen {fen}", depth=DEPTH
            )
        result_box["result"] = result
    except Exception as e:
        result_box["error"] = str(e)
    finally:
        result_box["done"] = True

# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def _pixel_to_square(mx: int, my: int):
    """Return algebraic square or None."""
    if 0 <= mx < BOARD_W and 0 <= my < BOARD_H:
        return square_name(my // SQ_SIZE, mx // SQ_SIZE)
    return None


def _pixel_to_lib_idx(mx: int, my: int):
    """Return PIECE_LIST index or None."""
    px = mx - PANEL_X
    for i, _ in enumerate(PIECE_LIST):
        row_i, col_i = divmod(i, 2)
        tx = 5 + col_i * TILE_W
        ty = LIB_START_Y + row_i * TILE_H
        if tx <= px < tx + TILE_W and ty <= my < ty + TILE_H:
            return i
    return None

# ---------------------------------------------------------------------------
# DevUI
# ---------------------------------------------------------------------------

class DevUI:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Chess Variant Sandbox")
        self.clock = pygame.time.Clock()

        self.font_sm  = pygame.font.SysFont("Arial", 13)
        self.font_med = pygame.font.SysFont("Arial", 15, bold=True)
        self.font_lg  = pygame.font.SysFont("Arial", 18, bold=True)

        self.imgs    = _load_piece_images(SQ_SIZE)
        self.imgs_sm = {k: pygame.transform.smoothscale(v, (32, 32)) for k, v in self.imgs.items()}

        self._reset_to_setup()

    # ------------------------------------------------------------------
    # State initialisation
    # ------------------------------------------------------------------

    def _reset_to_setup(self, board: Board = None):
        self.state        = SETUP
        self.setup_board  = board if board is not None else Board()
        self.display_board = Board()
        self.place_color  = "w"
        self.drag         = None   # {'char', 'source'('library'|'board'), 'from_sq'}
        self.mouse_pos    = (0, 0)
        self.status       = "Set up the board, then click PLAY."
        self.status2      = ""
        self.result_box   = {}
        self.board_history = []
        self.history_idx  = 0
        self.last_move    = None
        self.match_result = None
        self.last_advance = 0.0

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self):
        running = True
        while running:
            self.mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self._on_leftdown(event.pos)
                    elif event.button == 3:
                        self._on_rightclick(event.pos)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self._on_leftup(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self._prev_move()
                    elif event.key == pygame.K_RIGHT:
                        self._next_move()

            if self.state == COMPUTING:
                self._check_match_done()
            elif self.state == PLAYING:
                self._tick_playback()

            self._draw()
            self.clock.tick(60)

        pygame.quit()

    # ------------------------------------------------------------------
    # Input handlers
    # ------------------------------------------------------------------

    def _on_leftdown(self, pos):
        mx, my = pos

        # --- Setup interactions ---
        if self.state == SETUP:
            # Pick from piece library
            idx = _pixel_to_lib_idx(mx, my)
            if idx is not None:
                char, _ = PIECE_LIST[idx]
                colored = char.upper() if self.place_color == "w" else char
                self.drag = {"char": colored, "source": "library", "from_sq": None}
                return
            # Pick up piece already on board
            sq = _pixel_to_square(mx, my)
            if sq and self.setup_board.get(sq):
                self.drag = {"char": self.setup_board.get(sq), "source": "board", "from_sq": sq}
                self.setup_board.clear(sq)
                return

        # --- W / B toggle ---
        if self._btn_rect("toggle_w").collidepoint(pos):
            self.place_color = "w"
        elif self._btn_rect("toggle_b").collidepoint(pos):
            self.place_color = "b"

        # --- PLAY button ---
        if self._btn_rect("play").collidepoint(pos) and self.state == SETUP:
            self._start_match()

        # --- NAV buttons (PLAYING or REVIEW) ---
        if self.state in (PLAYING, REVIEW):
            if self._btn_rect("prev").collidepoint(pos):
                self._prev_move()
            elif self._btn_rect("next").collidepoint(pos):
                self._next_move()

        # --- NEW MATCH button ---
        if self.state == REVIEW and self._btn_rect("new").collidepoint(pos):
            self._reset_to_setup(copy.deepcopy(self.setup_board))

    def _on_leftup(self, pos):
        if self.drag is None:
            return
        sq = _pixel_to_square(*pos)
        if sq and self.state == SETUP:
            self.setup_board.set(sq, self.drag["char"])
        elif self.drag["source"] == "board" and self.drag["from_sq"]:
            # Dropped outside board — return to original square
            self.setup_board.set(self.drag["from_sq"], self.drag["char"])
        self.drag = None

    def _on_rightclick(self, pos):
        if self.state != SETUP:
            return
        sq = _pixel_to_square(*pos)
        if sq:
            self.setup_board.clear(sq)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _prev_move(self):
        if self.state in (PLAYING, REVIEW) and self.history_idx > 0:
            self.history_idx -= 1
            self._sync_display()

    def _next_move(self):
        if self.state in (PLAYING, REVIEW) and self.history_idx < len(self.board_history) - 1:
            self.history_idx += 1
            self._sync_display()

    def _sync_display(self):
        self.display_board = copy.deepcopy(self.board_history[self.history_idx])
        moves = self.match_result.moves
        if self.history_idx > 0:
            m = moves[self.history_idx - 1]
            self.last_move = (m[:2], m[2:4])
        else:
            self.last_move = None
        total = len(moves)
        res   = self.match_result.result.replace("_", " ")
        term  = self.match_result.termination
        self.status  = f"Move {self.history_idx} / {total}   [{res}]"
        self.status2 = f"({term})"

    # ------------------------------------------------------------------
    # Match management
    # ------------------------------------------------------------------

    def _start_match(self):
        self.result_box = {"done": False, "result": None, "error": None}
        self.state   = COMPUTING
        self.status  = "Computing match..."
        self.status2 = ""
        threading.Thread(
            target=_run_match,
            args=(copy.deepcopy(self.setup_board), self.result_box),
            daemon=True,
        ).start()

    def _check_match_done(self):
        if not self.result_box.get("done"):
            return
        if self.result_box.get("error"):
            self.state   = SETUP
            self.status  = "Error: " + self.result_box["error"][:55]
            self.status2 = "Check the board setup and try again."
            return
        result = self.result_box["result"]
        self.match_result = result
        # Build board history (one entry per ply, including start)
        self.board_history = [copy.deepcopy(self.setup_board)]
        b = copy.deepcopy(self.setup_board)
        for move in result.moves:
            b = _apply_uci_move(b, move)
            self.board_history.append(copy.deepcopy(b))
        self.history_idx  = 0
        self.last_advance = time.time()
        self.state        = PLAYING
        self._sync_display()

    def _tick_playback(self):
        if time.time() - self.last_advance >= MOVE_DELAY:
            if self.history_idx < len(self.board_history) - 1:
                self.history_idx  += 1
                self.last_advance  = time.time()
                self._sync_display()
            else:
                self.state = REVIEW

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self):
        self.screen.fill((28, 28, 30))
        self._draw_board()
        self._draw_board_pieces()
        self._draw_panel()
        if self.drag:
            self._blit_piece(self.drag["char"],
                             self.mouse_pos[0] - SQ_SIZE // 2,
                             self.mouse_pos[1] - SQ_SIZE // 2,
                             SQ_SIZE)
        pygame.display.flip()

    def _draw_board(self):
        last_src = last_dst = None
        if self.last_move:
            last_src, last_dst = self.last_move
        for row in range(8):
            for col in range(8):
                sq    = square_name(row, col)
                base  = C_LIGHT if (row + col) % 2 == 0 else C_DARK
                if last_src and sq in (last_src, last_dst):
                    color = tuple(min(255, c + 35) for c in base[:2]) + (min(255, base[2]),)
                    color = (min(255, base[0] + 20), min(255, base[1] + 60), min(255, base[2] + 20))
                else:
                    color = base
                pygame.draw.rect(self.screen, color,
                                 (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        # Rank / file labels
        for i in range(8):
            lbl = self.font_sm.render(str(8 - i), True, C_DIM)
            self.screen.blit(lbl, (2, i * SQ_SIZE + 2))
            lbl = self.font_sm.render(chr(ord("a") + i), True, C_DIM)
            self.screen.blit(lbl, (i * SQ_SIZE + SQ_SIZE - 14, BOARD_H - 16))

    def _draw_board_pieces(self):
        board = self.setup_board if self.state == SETUP else self.display_board
        dragging_from = (self.drag["from_sq"]
                         if self.drag and self.drag["source"] == "board" else None)
        for row in range(8):
            for col in range(8):
                sq    = square_name(row, col)
                piece = board.get(sq)
                if piece and sq != dragging_from:
                    self._blit_piece(piece, col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE)

    def _draw_panel(self):
        pygame.draw.rect(self.screen, C_PANEL, (PANEL_X, 0, PANEL_W, WIN_H))
        mx, my = self.mouse_pos
        hover  = _pixel_to_lib_idx(mx, my)

        # Header
        hdr = self.font_med.render("PIECES", True, C_TEXT)
        self.screen.blit(hdr, (PANEL_X + 8, 8))

        # --- Piece tiles ---
        for i, (char, name) in enumerate(PIECE_LIST):
            row_i, col_i = divmod(i, 2)
            tx = PANEL_X + 5 + col_i * TILE_W
            ty = LIB_START_Y + row_i * TILE_H
            rect = pygame.Rect(tx, ty, TILE_W - 4, TILE_H - 3)
            bg = C_TILE_HOV if hover == i and self.state == SETUP else C_TILE_NORM
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            img = self.imgs_sm.get((self.place_color, char))
            if img:
                self.screen.blit(img, (tx + 4, ty + 4))
            lbl = self.font_sm.render(name, True, C_TEXT)
            self.screen.blit(lbl, (tx + 38, ty + 13))

        # --- W / B toggle ---
        wr = self._btn_rect("toggle_w")
        br = self._btn_rect("toggle_b")
        lbl = self.font_sm.render("Place as:", True, C_DIM)
        self.screen.blit(lbl, (PANEL_X + 8, TOGGLE_Y + 5))
        for rect, color_id, bg_sel, bg_unsel, tc_sel, tc_unsel, text in [
            (wr, "w", (200, 200, 200), (90, 90, 90), (30, 30, 30), (160, 160, 160), "W"),
            (br, "b", (50, 50, 50),   (80, 80, 80), (200, 200, 200), (100, 100, 100), "B"),
        ]:
            selected = self.place_color == color_id
            pygame.draw.rect(self.screen, bg_sel if selected else bg_unsel, rect, border_radius=4)
            bdr_col = (255, 215, 0) if selected else (70, 70, 75)
            pygame.draw.rect(self.screen, bdr_col, rect, 2, border_radius=4)
            t = self.font_med.render(text, True, tc_sel if selected else tc_unsel)
            self.screen.blit(t, t.get_rect(center=rect.center))

        # --- PLAY button ---
        pb = self._btn_rect("play")
        active = self.state == SETUP
        if active:
            pb_col = C_BTN_GREEN_H if pb.collidepoint(mx, my) else C_BTN_GREEN
        else:
            pb_col = C_BTN_GREY
        pygame.draw.rect(self.screen, pb_col, pb, border_radius=6)
        pt = self.font_lg.render(">> PLAY", True, C_TEXT if active else C_DIM)
        self.screen.blit(pt, pt.get_rect(center=pb.center))

        # --- Status ---
        if self.state == COMPUTING:
            lbl = self.font_med.render("Computing...", True, C_COMPUTING)
        else:
            lbl = self.font_sm.render(self.status, True, C_TEXT)
        self.screen.blit(lbl, (PANEL_X + 8, STATUS_Y))
        if self.status2:
            lbl2 = self.font_sm.render(self.status2, True, C_DIM)
            self.screen.blit(lbl2, (PANEL_X + 8, STATUS_Y + 18))

        # --- Nav buttons + NEW MATCH (non-setup states) ---
        if self.state in (PLAYING, REVIEW):
            prev_r = self._btn_rect("prev")
            next_r = self._btn_rect("next")
            can_prev = self.history_idx > 0
            can_next = self.history_idx < len(self.board_history) - 1
            for btn, label, enabled in [
                (prev_r, "< PREV", can_prev),
                (next_r, "NEXT >", can_next),
            ]:
                if enabled:
                    bg = C_BTN_GREY_H if btn.collidepoint(mx, my) else C_BTN_GREY
                else:
                    bg = (45, 45, 50)
                pygame.draw.rect(self.screen, bg, btn, border_radius=5)
                t = self.font_med.render(label, True, C_TEXT if enabled else C_DIM)
                self.screen.blit(t, t.get_rect(center=btn.center))

            # Move counter
            if self.match_result:
                counter = f"Move {self.history_idx} / {len(self.match_result.moves)}"
                ct = self.font_sm.render(counter, True, C_DIM)
                self.screen.blit(ct, (PANEL_X + 8, NAV_Y + 42))

        if self.state == REVIEW:
            nb = self._btn_rect("new")
            nb_col = C_BTN_BLUE_H if nb.collidepoint(mx, my) else C_BTN_BLUE
            pygame.draw.rect(self.screen, nb_col, nb, border_radius=6)
            nt = self.font_med.render("NEW MATCH", True, C_TEXT)
            self.screen.blit(nt, nt.get_rect(center=nb.center))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blit_piece(self, piece: str, x: int, y: int, size: int):
        color = "w" if piece.isupper() else "b"
        char  = piece.lower()
        img   = (self.imgs if size == SQ_SIZE else self.imgs_sm).get((color, char))
        if img:
            if size not in (SQ_SIZE, 32):
                img = pygame.transform.smoothscale(img, (size, size))
            self.screen.blit(img, (x, y))

    def _btn_rect(self, name: str) -> pygame.Rect:
        cx = PANEL_X
        match name:
            case "toggle_w": return pygame.Rect(cx + 86,  TOGGLE_Y,     44, 28)
            case "toggle_b": return pygame.Rect(cx + 134, TOGGLE_Y,     44, 28)
            case "play":     return pygame.Rect(cx + 20,  PLAY_Y,  PANEL_W - 40, 40)
            case "prev":     return pygame.Rect(cx + 8,   NAV_Y,        118, 36)
            case "next":     return pygame.Rect(cx + 154, NAV_Y,        118, 36)
            case "new":      return pygame.Rect(cx + 20,  NEW_BTN_Y, PANEL_W - 40, 36)
            case _:          return pygame.Rect(0, 0, 0, 0)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    DevUI().run()
