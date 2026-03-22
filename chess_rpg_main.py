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
from chess_rpg_config import SQ_SIZE, WIDTH, HEIGHT

pg.init()

# set up display
screen = pg.display.set_mode((WIDTH, HEIGHT))

# define pieces and colours
pieces = ['p','n','b','r','q','k']
colours = ['b','w']

# load assets
piece_img = {}
for colour in colours:
    for piece in pieces:
        if colour == 'w':
            piece_img[piece.upper()] = pg.transform.scale(pg.image.load(f"assets/{colour}{piece}.png"),(SQ_SIZE,SQ_SIZE))
        else:
            piece_img[piece.lower()] = pg.transform.scale(pg.image.load(f"assets/{colour}{piece}.png"),(SQ_SIZE,SQ_SIZE))
        
        
# path of engines
path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-bmi2.exe"
legal_move_path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-bmi2-player2.exe"


# initialise engine
engine = chess.uci.popen_engine(path)
engine.uci()
info_handler = chess.uci.InfoHandler()
engine.info_handlers.append(info_handler)

# a second engine that checks legal moves
legal_move = chess.uci.popen_engine(legal_move_path)
legal_move.uci()
legal_move.setoption({"MultiPV":215})
lm_info_handler = chess.uci.InfoHandler()
legal_move.info_handlers.append(lm_info_handler)

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
board = fen_to_array(fen)
moves = []
move_start = ""
move_end = ""
clicked = 0
promotion_table = None

# initialise game loop
running = True
while running:
    
    draw_board(screen)
    draw_pieces(board, screen, piece_img)
        
    # handle events
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        elif event.type == pg.MOUSEBUTTONDOWN:
            row, col = get_square_from_mouse(pg.mouse.get_pos())
            clicked += 1
            if clicked == 1:
                move_start = array_to_algebraic(row, col)
            elif clicked == 2:
                move_end = array_to_algebraic(row, col)
        
    
    # draw legal moves when a piece is selected
    if move_start != "" and move_end == "":
        
        # generate legal move
        legal_move.send_line("position fen " + fen + " moves " + " ".join(moves))
        legal_move.go(depth=1)
        legal_moves = [move[0] for move in list(lm_info_handler.info['pv'].values())]
        
        # find legal moves starting at selected square
        legal_move_squares = []
        for move in legal_moves:
            if move[:2] == move_start:
                 legal_move_squares.append(move[2:])
        
        legal_move_squares = [algebraic_to_array(pos) for pos in legal_move_squares]
        draw_board(screen, legal_move_squares)
        draw_pieces(board,screen,piece_img)
        
        
    
    # reset moves
    if move_start == move_end:
        move_start = ""
        move_end = ""
        clicked = 0
    
    elif move_start!="" and move_end!= "":
            
        # generate legal move
        legal_move.send_line("position fen " + fen + " moves " + " ".join(moves))
        legal_move.go(depth=1)
        legal_moves = [move[0] for move in list(lm_info_handler.info['pv'].values())]
        
        # get player move
        player_move = move_start+move_end
        
        # check that move is legal, loop until a legal move is input
        if player_move not in legal_moves:
            player_move = ""
            move_start = ""
            move_end = ""
            clicked = 0
            continue
                
       
        moves.append(player_move)
        animate_move(player_move, board, screen, piece_img, pg.time.Clock())
        board, captured_piece = apply_move(board, player_move, None)
        player_move = ""
        move_start = ""
        move_end = ""
        clicked = 0
        
        # send move to engine
        engine.send_line("position fen " + fen + " moves " + " ".join(moves))
        
        # get engine move
        engine_move, ponder = engine.go(depth=12)
        
        # wait and check info handler
        if "mate" in str(info_handler.info):
            mate_score = info_handler.info["score"][1].mate
            if mate_score == 0:
                draw_checkmate(screen, board, piece_img)
                pg.time.wait(5000)
                break
        
        # get engine move and send
        engine_move, ponder = engine.go(depth=12)
        moves.append(engine_move)
        animate_move(engine_move, board, screen, piece_img, pg.time.Clock())
        board, captured_piece = apply_move(board, engine_move, None)
        engine.send_line("position fen " + fen + " moves " + " ".join(moves))
        
        # get engine move again - this will allow a correct check for mate
        engine_move, ponder = engine.go(depth=12)
        
        if "mate" in str(info_handler.info):
            mate_score = info_handler.info["score"][1].mate
            if mate_score == 0:
                draw_checkmate(screen, board, piece_img)
                pg.time.wait(5000)
                break
        
    pg.display.flip()

    
pg.quit()