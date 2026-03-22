# -*- coding: utf-8 -*-
"""
Created on Wed Apr  9 12:59:41 2025

@author: jackm
"""

import pygame as pg
import chess
import chess.uci
import threading
import queue
import time
import numpy as np
from chess_rpg_functions import *
from chess_rpg_config import SQ_SIZE, WIDTH, HEIGHT, FEN

# Initialize Pygame
pg.init()

# Initialize screen and board
screen = pg.display.set_mode((WIDTH, HEIGHT))

# Path for your engine (adjust as needed)
engine1_path = r"fairy-stockfish_x86-64-bmi2.exe"
engine2_path = r"fairy-stockfish_x86-64-bmi2-player2.exe"

# Your setup code (adjust as needed)
variant_name = "khans"
start_fen = "rnbqkbnr/lppppppl/8/8/8/8/PPPLLPPP/RNBQKBNR w - - 0 1"
custom_pieces = ["commoner = s", "chancellor = c", "fers = f", "wazir = w", "amazon = a", "lance = l"]
promotion_table = {"l": "s", "p": "q"}
custom_piece_values = {"s": 400}

# Define the variant
define_variant(variant_name, "chess", start_fen, custom_pieces, promotion_table, custom_piece_values)

# Load pieces
piece_img = load_assets(start_fen)

# Initialize engines
engine1 = chess.uci.popen_engine(engine1_path)
engine1.uci()
engine1.ucinewgame()
engine1.setoption({"VariantPath": "variants1.ini", "UCI_Variant": variant_name})

engine2 = chess.uci.popen_engine(engine2_path)
engine2.uci()
engine2.ucinewgame()
engine2.setoption({"VariantPath": "variants2.ini", "UCI_Variant": variant_name})

# Initialize variables
board = fen_to_array(start_fen)
moves = []
ply_depth = 12

# Thread-safe queue to hold generated moves
move_queue = queue.Queue()

# Function to generate moves and put them in the queue
def generate_moves(engine, depth, move_queue):
    while True:
        # Send the position to the engine
        line_to_send = f"position startpos moves {' '.join(moves)}"
        engine.send_line(line_to_send)
        move, ponder = engine.go(depth=depth)
        print(move)
        if move == '(none)':
            move_queue.put("gameover")  # Indicate the game is over
            break

        # Put the generated move into the queue
        move_queue.put(move)

        # Small delay to simulate engine thinking time
        time.sleep(0.1)

# The main loop that handles Pygame events and animation
def main_loop():
    global board, moves

    clock = pg.time.Clock()

    running = True
    turn = 1

    while running:
        # Process Pygame events
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        # Always draw the board and pieces
        draw_board(screen)
        draw_pieces(board, screen, piece_img)

        # Check if there are moves in the queue
        try:
            move = move_queue.get_nowait()

            if move == 'gameover':
                draw_checkmate(screen, board, piece_img)
                pg.display.flip()
                time.sleep(2)  # Wait before closing
                running = False
                continue

            # Check if the move is valid (i.e., moving a piece, not an empty square)
            from_square, to_square = move[:2], move[2:4]  # Assuming the move format is "from_square to_square"
            from_x, from_y = algebraic_to_array(from_square)

            # If the move starts on an empty square, skip animation
            if board[from_x, from_y] == "":  # 0 means empty square
                continue

            # Animate the move
            animate_move(move, board, screen, piece_img, clock)
            board, _ = apply_move(board, move, promotion_table)

            moves.append(move)

        except queue.Empty:
            # If no move is ready, just continue to the next frame
            pass

        # Update the display
        pg.display.flip()

        # Control the frame rate
        clock.tick(30)  # 30 FPS

    # Final wait loop to close window
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
        time.sleep(0.05)


# Start the move generation in separate threads
engine1_thread = threading.Thread(target=generate_moves, args=(engine1, ply_depth, move_queue))
engine2_thread = threading.Thread(target=generate_moves, args=(engine2, ply_depth, move_queue))

engine1_thread.start()
engine2_thread.start()

# Start the main Pygame loop
main_loop()

# Join the threads before quitting
engine1_thread.join()
engine2_thread.join()

pg.quit()
