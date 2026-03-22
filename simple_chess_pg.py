# -*- coding: utf-8 -*-
"""
Created on Sun Mar 30 17:00:15 2025

@author: jackm
"""

import pygame
import chess

# Initialize pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 512, 512
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
WHITE, BLACK = (238, 238, 210), (118, 150, 86)
SELECT_COLOR = (186, 202, 43)

# Load piece images
PIECE_IMAGES = {}
for piece in "pnbrqkPNBRQK":
    
    if piece.lower() == piece:
        piece_filename = 'b' + piece
    else:
        piece_filename = 'w' + piece
    
    PIECE_IMAGES[piece] = pygame.transform.scale(
        pygame.image.load(f"assets/{piece_filename}.png"), (SQUARE_SIZE, SQUARE_SIZE)
    )

# Initialize board
board = chess.Board()

# Pygame setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Chess")

selected_square = None  # Stores the selected piece's square

def draw_board():
    for row in range(ROWS):
        for col in range(COLS):
            color = WHITE if (row + col) % 2 == 0 else BLACK
            pygame.draw.rect(screen, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces():
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece:
            row, col = divmod(sq, 8)
            screen.blit(PIECE_IMAGES[piece.symbol()], (col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE))

def draw_selected():
    if selected_square is not None:
        row, col = divmod(selected_square, 8)
        pygame.draw.rect(screen, SELECT_COLOR, (col * SQUARE_SIZE, (7 - row) * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 5)

def get_square_from_mouse(pos):
    x, y = pos
    col, row = x // SQUARE_SIZE, 7 - (y // SQUARE_SIZE)
    print(f"Mouse Click: col={col}, row={row}")  # Debug statement
    return chess.square(int(col), int(row))  # Ensure col and row are integers

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            clicked_square = get_square_from_mouse(event.pos)
            if selected_square is None:
                # Select piece if it belongs to the correct player
                if board.piece_at(clicked_square) and board.piece_at(clicked_square).color == board.turn:
                    selected_square = clicked_square
            else:
                # Attempt to move
                move = chess.Move(selected_square, clicked_square)
                if move in board.legal_moves:
                    board.push(move)
                selected_square = None  # Deselect after move
    
    draw_board()
    draw_selected()
    draw_pieces()
    pygame.display.flip()

pygame.quit()
