# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 17:37:07 2025

@author: jackm
"""

import chess
import chess.uci
import numpy as np
import pygame as pg
from chess_rpg_functions import *
from chess_rpg_config import SQ_SIZE, WIDTH, HEIGHT, FEN
  
# path of engines
engine1_path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-bmi2.exe"
engine2_path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-bmi2-player2.exe"

pg.init()

# set up display
screen = pg.display.set_mode((WIDTH, HEIGHT))

# define variant
variant_name = "khans"
base_game = "chess"
start_fen = "rnbqkbnr/lppppppl/8/8/8/8/PPPLLPPP/RNBQKBNR w - - 0 1"
promotion_table = {"l":"s","p":"q"}
bongcloud = False

custom_pieces = [
    "commoner = s",
    "chancellor = c",
    "fers = f",
    "wazir = w",
    "amazon = a",
    "lance = l"
    ]

custom_piece_values = {"s":400}

define_variant(
        variant_name,base_game,
        start_fen,
        custom_pieces,
        promotion_table,
        custom_piece_values
        )

piece_img = load_assets(start_fen)

# initialise engine1
engine1 = chess.uci.popen_engine(engine1_path)
engine1.uci()
engine1.ucinewgame()
engine1.setoption({"VariantPath": "variants1.ini","UCI_Variant": variant_name})
info_handler1 = chess.uci.InfoHandler()
engine1.info_handlers.append(info_handler1)

# initialise engine2
engine2 = chess.uci.popen_engine(engine2_path)
engine2.uci()
engine2.ucinewgame()
engine2.setoption({"VariantPath": "variants2.ini","UCI_Variant": variant_name})
info_handler2 = chess.uci.InfoHandler()
engine2.info_handlers.append(info_handler2)

board = fen_to_array(start_fen)
moves = []

ply_depth = 12

# initialise game loop
turn = 1
running = True
while running:
    
    draw_board(screen)
    draw_pieces(board, screen, piece_img)
    piece_count = np.count_nonzero(board)
    
    if piece_count <= 8:
        ply_depth = 18
    elif piece_count <= 4:
        ply_depth = 1000
    
    # handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
    
    # do engine1 moves and animate
    line_to_send = f"position startpos moves " + " ".join(moves)
    engine1.send_line(line_to_send)
    engine1_move, ponder = engine1.go(depth=ply_depth)
    if engine1_move == '(none)':
        draw_checkmate(screen, board, piece_img)
        break
    
    moves.append(engine1_move)
    animate_move(engine1_move, board, screen, piece_img, pg.time.Clock())
    board, captured_piece = apply_move(board, engine1_move, promotion_table)
    
    # do engine2 moves and animate
    line_to_send = f"position startpos moves " + " ".join(moves)
    engine2.send_line(line_to_send)
    engine2_move, ponder = engine2.go(depth=ply_depth)
    if engine2_move == '(none)':
        draw_checkmate(screen, board, piece_img)
        break
    
    if bongcloud:
        if turn == 1:
            engine2_move = "e7e5"
        if turn == 2:
            engine2_move = "e8e7"
        
    moves.append(engine2_move)
    animate_move(engine2_move, board, screen, piece_img, pg.time.Clock())
    board, captured_piece = apply_move(board, engine2_move, promotion_table)
        
    turn += 1
    
    pg.display.flip()

running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False    

pg.quit()