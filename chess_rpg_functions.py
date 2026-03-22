# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 12:08:30 2025

@author: jackm
"""
import numpy as np
import pygame as pg
import chess
import chess.uci
from chess_rpg_config import SQ_SIZE, WIDTH, HEIGHT, FEN

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
def apply_move(board_array, move, promotion_table):
    # Convert move from long algebraic notation (e.g., 'f2f3') to array indices
    start_square = move[:2]
    end_square = move[2:4]
    
    if len(move) == 5:
        promoted_piece = move[4]
    else:
        promoted_piece = None

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
    
    if promotion_table:
        if promoted_piece:
            if promoted_piece == "+":
                promoted_piece = promotion_table[piece.lower()]
                
            if piece.isupper():
                promoted_piece = promoted_piece.upper()
                
            board_array[end_row, end_col] = promoted_piece
            
    # Clear the old position
    board_array[start_row, start_col] = ''

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
def draw_board(screen,legal_move_squares=None):
    colors = [(240, 217, 181), (181, 136, 99)]
    legal_colors = [(255, 255, 181), (246, 201, 99)]
    
    for row in range(8):
        for col in range(8):
            
            color = colors[(row + col) % 2]
            
            if legal_move_squares:
                if (row, col) in legal_move_squares:
                    color = legal_colors[(row + col) % 2]
                
            pg.draw.rect(screen, color, (col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        

# function to draw pieces
def draw_pieces(board_array, screen, piece_img):
    for row in range(8):
        for col in range(8):
            piece = board_array[row,col]
            if piece!='':
                screen.blit(piece_img[piece], (col * SQ_SIZE, row * SQ_SIZE))
                

# function to get board position from mouse click
def get_square_from_mouse(pos):
    x, y = pos
    return y // SQ_SIZE, x // SQ_SIZE


def animate_move(move, board_array, screen, piece_img, clock, fps=60, duration=0.2):
    start_row, start_col = algebraic_to_array(move[:2])
    end_row, end_col = algebraic_to_array(move[2:])

    dx = (end_col - start_col) * SQ_SIZE
    dy = (end_row - start_row) * SQ_SIZE

    frames = int(fps * duration)
    piece = board_array[start_row, start_col]
    board_array_temp = board_array.copy()
    board_array_temp[start_row, start_col] = ""

    for frame in range(frames + 1):
        # Clear screen and redraw everything
        screen.fill((255, 255, 255))  # or your background drawing logic

        draw_board(screen)           # your board drawing function
        draw_pieces(board_array_temp, screen, piece_img)  # draw all pieces

        # Calculate intermediate position
        x_offset = dx * (frame / frames)
        y_offset = dy * (frame / frames)

        piece_image = piece_img[piece]
        x = start_col * SQ_SIZE + x_offset
        y = start_row * SQ_SIZE + y_offset

        screen.blit(piece_image, (x, y))

        pg.display.flip()
        clock.tick(fps)


def draw_checkmate(screen, board_array, piece_img, duration=2):
    # Load image
    checkmate = pg.image.load(r"assets/checkmate.png")
    
    # Scale image to the screen width, maintaining aspect ratio
    aspect_ratio = checkmate.get_height() / checkmate.get_width()
    new_width = WIDTH
    new_height = int(new_width * aspect_ratio)
    checkmate = pg.transform.scale(checkmate, (new_width, new_height))
    
    # Get the rect to center the image
    checkmate_rect = checkmate.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    # Get the starting time for the animation
    start_ticks = pg.time.get_ticks()

    clock = pg.time.Clock()

    while True:
        # Calculate the elapsed time
        elapsed_time = (pg.time.get_ticks() - start_ticks) / 1000  # in seconds

        # Calculate the alpha based on elapsed time (fade-in effect)
        alpha = min(150, (elapsed_time / duration) * 255)
        
        # If the image has fully faded in, exit the loop
        if elapsed_time >= duration:
            break

        # Set the alpha of the image
        checkmate.set_alpha(alpha)

        # Fill the screen (optional: use your background color)
        draw_board(screen)  # Or your custom background
        draw_pieces(board_array,screen,piece_img)
        # Draw the image on the screen
        screen.blit(checkmate, checkmate_rect)
        
        # Update the display
        pg.display.flip()
        
        # Limit to 60 FPS
        clock.tick(60)


def define_variant(
        variant_name,base_game,
        start_fen,
        custom_pieces, # a list of custom pieces
        promotion_table, # dictionary of promotions
        piece_values #  modified piece values
        ):
    
    game_type_str = f"[{variant_name}:{base_game}]\n"
    
    custom_piece_str = ""
    if custom_pieces:
        for custom_piece in custom_pieces:
            custom_piece_str += custom_piece + "\n"
    
    promotion_table_str = ""
    if promotion_table:
        promoted_piece_str = "promotedPieceType = "
        promotion_types_str = "promotionPieceTypes = -"
        for orig_piece, new_piece in promotion_table.items():
            promoted_piece_str += f"{orig_piece}:{new_piece} "
        
        promotion_table_str = promotion_types_str + "\n" + promoted_piece_str + "\n"
    
    piece_values_str = ""
    piece_values_mg_str = ""
    piece_values_eg_str = ""
    if piece_values:
        piece_values_mg_str = "pieceValueMg = "
        piece_values_eg_str = "pieceValueEg = "
        for piece, value in piece_values.items():
            piece_values_mg_str += piece + ":" + str(value) + " "
            piece_values_eg_str += piece + ":" + str(value) + " "
            
        piece_values_mg_str += "\n"
        piece_values_eg_str += "\n"   
        piece_values_str = piece_values_mg_str + piece_values_eg_str
        
    start_fen_str = f"startFen = {start_fen}"
    variant1_str = game_type_str + custom_piece_str + promotion_table_str + start_fen_str
    variant2_str = variant1_str + piece_values_str
    
    # unmodified values
    with open("variants1.ini", 'w+') as file:
        file.write(variant1_str)
        
    # modified values
    with open("variants2.ini", 'w+') as file:
        file.write(variant2_str)
    
    
def load_assets(fen):
    pieces = {piece for piece in fen.split(" ")[0].lower() if piece.isalpha()}
    pieces = ['p','n','b','r','q','k']
    
    piece_img = {}
    for colour in ['b','w']:
        for piece in pieces:
            if colour == 'w':
                piece_img[piece.upper()] = pg.transform.scale(pg.image.load(f"assets/{colour}{piece}.png"),(SQ_SIZE,SQ_SIZE))
            else:
                piece_img[piece.lower()] = pg.transform.scale(pg.image.load(f"assets/{colour}{piece}.png"),(SQ_SIZE,SQ_SIZE))
    
    fairy_pieces = ['s','c','f','w','a','l']
    
    counter = 0
    for piece in fairy_pieces:
        for colour in ['b','w']:
            if colour == 'w':
                piece_img[piece.upper()] = pg.transform.rotate(piece_img[pieces[counter].upper()],180)
            else:
                piece_img[piece.lower()] = pg.transform.rotate(piece_img[pieces[counter].lower()],180)
                
        counter += 1
        
    return piece_img


def initialise_engine(engine_path, variant_path=None, variant_name=None):
    engine = chess.uci.popen_engine(engine_path)
    engine.uci()
    engine.ucinewgame()
    info_handler = chess.uci.InfoHandler()
    engine.info_handlers.append(info_handler)
    if variant_name:
        engine.setoption(
            {"VariantPath": variant_path,"UCI_Variant": variant_name}
            )
    return engine, info_handler


def get_legal_moves(legal_move, lm_info_handler, map_fen, moves, move_start):
    legal_move.send_line("position fen " + map_fen + " moves " + " ".join(moves))
    legal_move.go(depth=1)
    legal_moves = [move[0] for move in list(lm_info_handler.info['pv'].values())]
    legal_move_squares = []
    for move in legal_moves:
        if move[:2] == move_start:
             legal_move_squares.append(move[2:])
    
    legal_move_squares = [algebraic_to_array(pos) for pos in legal_move_squares]
    print(legal_moves)
    return legal_moves, legal_move_squares
    