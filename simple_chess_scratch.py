# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 17:37:07 2025

@author: jackm
"""

import chess
import chess.uci
import numpy as np
import pygame as pg

pg.init()

# set up display
WIDTH, HEIGHT = 400, 400
SQ_SIZE = WIDTH//8
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

# define functions

# function to convert a fen string to a numpy array
def fen_to_array(fen):
    # Split the FEN string into the board position
    board = fen.split(' ')[0]
    
    # Initialize an empty 8x8 numpy array
    board_array = np.full((8, 8), '', dtype=object)
    
    # Convert the board string into the numpy array
    rows = board.split('/')
    for row_idx, row in enumerate(rows):
        col_idx = 0
        for char in row:
            if char.isdigit():
                col_idx += int(char)  # Skip the number of empty squares
            else:
                board_array[row_idx, col_idx] = char  # Directly set the piece's initial
                col_idx += 1            

    return board_array
    

# function to convert algebraic position to an array position
def algebraic_to_array(position):
    col = ord(position[0]) - ord('a')
    row = 8 - int(position[1])
    return row, col


# and the reverse
def array_to_algebraic(row, col):
    file = chr(col + ord('a'))  # Convert column index to letter
    rank = str(8 - row)  # Convert row index to number
    return file + rank


# function to apply a move to the board array
def apply_move(board_array, move):
    # Convert move from long algebraic notation (e.g., 'f2f3') to array indices
    start_square = move[:2]
    end_square = move[2:]

    # Convert 'a1' -> (7, 0), 'h8' -> (0, 7), etc.
    start_row, start_col = algebraic_to_array(start_square)
    end_row, end_col = algebraic_to_array(end_square)

    # Get the piece to move
    piece = board_array[start_row, start_col]
    captured_piece = board_array[end_row,end_col]
    board_array[end_row, end_col] = piece
    
    # add capturing passed pawn for en passant logic 
    if piece.lower() == 'p':
        if start_col!=end_col and captured_piece == '':
            captured_piece = board_array[start_row,end_col]
            board_array[start_row,end_col] = ''
            
    # add castling logic for rook
    if piece.lower() == 'k':
        if end_col - start_col == 2:
            board_array[end_row, end_col-1] = board_array[end_row, 7]
            board_array[end_row, 7] = ''
        elif end_col - start_col == -2:
            board_array[end_row, end_col+1] = board_array[end_row, 0]
            board_array[end_row, 0] = ''
            
    # Clear the old position
    board_array[start_row, start_col] = ''
    
    print(board_array)

    return board_array, captured_piece

 
# function to convert an array back to a fen
def array_to_fen(board):
    fen_rows = []
    for row in board:
        empty_count = 0
        fen_row = ""
        for cell in row:
            if cell == "":  # Empty square
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += cell
        if empty_count > 0:
            fen_row += str(empty_count)
        fen_rows.append(fen_row)
    
    return "/".join(fen_rows)


# function to draw board
def draw_board():
    colors = [(240, 217, 181), (181, 136, 99)]
    for row in range(8):
        for col in range(8):
            color = colors[(row + col) % 2]
            pg.draw.rect(screen, color, (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


# function to draw pieces
def draw_pieces(board_array):
    for row in range(8):
        for col in range(8):
            piece = board_array[row][col]
            if piece:
                screen.blit(piece_img[piece], (col * SQ_SIZE, row * SQ_SIZE))
                

# function to get board position from mouse click
def get_square_from_mouse(pos):
    x, y = pos
    return y // SQ_SIZE, x // SQ_SIZE


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

# initialise game loop
running = True
while running:
    
    draw_board()
    draw_pieces(board)
        
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
        board, captured_piece = apply_move(board, player_move)
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
                print("Checkmate! Game over.")
                break
        
        # get engine move and send
        engine_move, ponder = engine.go(depth=12)
        moves.append(engine_move)
        board, captured_piece = apply_move(board, engine_move)
        engine.send_line("position fen " + fen + " moves " + " ".join(moves))
        
        # print_board = board
        # print_board[print_board==""] = " "
        # print(print_board)
        
        # get engine move again - this will allow a correct check for mate
        engine_move, ponder = engine.go(depth=12)
        
        if "mate" in str(info_handler.info):
            mate_score = info_handler.info["score"][1].mate
            if mate_score == 0:
                print("Checkmate! Game over.")
                break
        
    pg.display.flip()

    
pg.quit()