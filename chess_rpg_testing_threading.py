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

# initialise engines
engine1, info_handler1 = initialise_engine(engine1_path,"variants1.ini","orda")
engine2, info_handler2 = initialise_engine(engine2_path,"variants2.ini","orda")

moves = []
board = fen_to_array(start_fen)
last_board = board.copy()
promotion_table = {"p":"q","s":"c"}
piece_img = load_assets(start_fen)
depth_control = {}

# Create queues for communication
move_queue = queue.Queue()
stop_event = threading.Event()
# Producer thread puts items into the queue
def producer(engine1, engine2,depth_control):
    while not stop_event.is_set():
        for engine in [engine1, engine2]:
            line_to_send = f"position startpos moves " + " ".join(moves)
            engine.send_line(line_to_send)
            engine_move, ponder = engine.go(depth=12)
            if engine_move == '(none)':
                move_queue.put(None)
                break
            moves.append(engine_move)
            move_queue.put(engine_move)   


# Start the thread
threading.Thread(target=producer, args=(engine1,engine2,depth_control)).start()

# start game loop to animate
running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            stop_event.set() 
    
    try:
        move = move_queue.get_nowait()
        if move is None:
            running = False
        else:
            animate_move(move, board, screen, piece_img, pg.time.Clock())
            board, _ = apply_move(board, move, promotion_table)
    except queue.Empty:
        pass
    
    draw_board(screen)
    draw_pieces(board, screen, piece_img)
    pg.display.flip()

stop_event.set() 

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
            stop_event.set()

pg.quit()