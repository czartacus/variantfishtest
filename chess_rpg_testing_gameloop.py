import pygame as pg
import chess
import chess.uci
import threading
import queue
import time
import numpy as np
from chess_rpg_functions import *
from chess_rpg_config import SQ_SIZE, WIDTH, HEIGHT, FEN, custom_pieces

# init pygame and screen
pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))

# engine paths
engine1_path = r"fairy-stockfish_x86-64-bmi2.exe"
engine2_path = r"fairy-stockfish_x86-64-bmi2-player2.exe"

# define variant
start_fen = "wcfakfcw/8/ssssssss/8/8/8/PPPPPPPP/RNBQKBNR w KQ - 0 1"
# start_fen = FEN

define_variant(
    "orda","chess",
    start_fen,
    ["flagPiece = k",
     "flagRegionWhite = *8",
     "flagRegionBlack = *1",
     "centaur = c",
     "knibis = f",
     "kniroo = w",
     "silver = a",
     "customPiece1 = s:mfWcfF"], # a list of custom pieces
    {"p":"q","s":"c"}, # dictionary of promotions
    False #  modified piece values
    )

board = fen_to_array(start_fen)
promotion_table = {"p":"q","s":"c"}
piece_img = load_assets(start_fen)
depth_control = {}

def autochess(engine1, engine2, depth_control):
    moves = []
    
    while not stop_event.is_set():
        for engine in [engine1, engine2]:
            line_to_send = f"position startpos moves " + " ".join(moves)
            engine.send_line(line_to_send)
            engine_move, ponder = engine.go(depth=12)
            if engine_move == '(none)':
                move_queue.put(None)
                stop_event.set()
                break
            moves.append(engine_move)
            move_queue.put(engine_move)   


# track game state
paused = False
move_start = ""
move_end = ""
map_fen = "r3k3/7q/8/p4b2/5n2/2p5/C7/8 - - 0 1"
map_turn = 0
moves = []
main_state = "map"
legal_move_squares = None
turn = 0
stop_event = threading.Event()

# start game loop to animate
running = True
while running: 
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            stop_event.set()
        elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
            paused = not paused 
        elif event.type == pg.MOUSEBUTTONDOWN and main_state == "map":
            row, col = get_square_from_mouse(pg.mouse.get_pos())
            if move_start == "":
                move_start = array_to_algebraic(row, col)
            else:
                move_end = array_to_algebraic(row, col)
    
    if paused: continue
    
    # for the main autobattler loop
    if main_state == "game":   
        if turn == 0:
            turn = 1
            engine1, info_handler1 = initialise_engine(engine1_path,"variants1.ini","orda")
            engine2, info_handler2 = initialise_engine(engine2_path,"variants2.ini","orda")
            move_queue = queue.Queue()
            stop_event = threading.Event()
            threading.Thread(target=autochess, args=(engine1,engine2,depth_control)).start()

        try:
            move = move_queue.get_nowait()
            if move is None:
                engine1.quit()
                engine2.quit()
                turn = 0
            else:
                animate_move(move, board, screen, piece_img, pg.time.Clock())
                board, _ = apply_move(board, move, promotion_table)
                turn += 1
                
        except queue.Empty:
            pass
        
    if main_state == "map":
        if map_turn == 0:
            engine, info_handler = initialise_engine(engine1_path,"variants_map.ini", "map")
            legal_move, lm_info_handler = initialise_engine(engine2_path,"variants_map.ini", "map")
            legal_move.setoption({"MultiPV":215})
            board = fen_to_array(map_fen)
            map_turn = 1
        else:
            if move_start != "" and move_end == "":
                legal_moves, legal_move_squares = get_legal_moves(
                    legal_move, 
                    lm_info_handler, 
                    map_fen, 
                    moves, 
                    move_start
                    )
                
            elif move_start != "" and move_end != "":
                player_move = move_start + move_end
                if move_start == move_end or player_move not in legal_moves:
                    move_start = ""
                    move_end = ""
                    continue
            
                # handle player moves
                moves.append(player_move)
                animate_move(player_move, board, screen, piece_img, pg.time.Clock())
                board, captured_piece = apply_move(board, player_move, None)
                engine.send_line("position fen " + map_fen + " moves " + " ".join(moves))
                player_move = ""
                move_start = ""
                move_end = ""
                legal_move_squares = None
                
                # handle bot moves
                engine_move, ponder = engine.go(depth=12)
                moves.append(engine_move)
                animate_move(engine_move, board, screen, piece_img, pg.time.Clock())
                board, captured_piece = apply_move(board, engine_move, None)
                   
    draw_board(screen, legal_move_squares)
    draw_pieces(board, screen, piece_img)
    pg.display.flip()


pg.quit()