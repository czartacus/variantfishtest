# -*- coding: utf-8 -*-
"""
Created on Sat Mar 29 10:48:20 2025

@author: jackm
"""

import random
import subprocess
import os
import pandas as pd
import numpy as np
import time


def rand_skill_battle(variant_name, start_fen, max_games, skill1, skill2):

    # Define paths
    varini_path = r"variants.ini"
    engine1_path = r"fairy-stockfish_x86-64-bmi2.exe"
    engine2_path = r"fairy-stockfish_x86-64-bmi2-player2.exe"
    script_path = r"variantfishtestv3.py"
    output_path = r"output.txt"

    # create variants.ini file
    varini_text = f"[{variant_name}:chess]\nchancellor = w\nstartFen = {start_fen}"
    with open(varini_path, 'w') as file:
        file.write(varini_text)

    # remove outputs file
    if os.path.exists(output_path):
        os.remove(output_path)

    # Construct command
    cmd = f'python "{script_path}" "{engine1_path}" "{engine2_path}" -t 1000 -n {max_games} -c {varini_path} -v "{variant_name}" -l output.txt --verbosity 2 -sl1 {skill1} -sl2 {skill2} -d 6'
    # Run command and capture output
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result = subprocess.run(cmd, shell=True)

    # read output file
    with open(output_path) as f:
        output = f.readlines()

    result = output[-1]

    return result


# basic fen
basic_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"

# piece values
pieces = ['p', 'n', 'b', 'r', 'q']

    # create useful ranges
black_first_rank = [x for x in range(0, 4)]+[x for x in range(5, 8)]
white_first_rank = [x for x in range(26, 34)]+[x for x in range(35, 39)]
black_pawn_rank = [x for x in range(9, 17)]
white_pawn_rank = [x for x in range(26, 34)]
black_range = black_first_rank + black_pawn_rank
white_range = white_pawn_rank + white_first_rank

results = []
counter = 0
max_value = 11
max_combinations = 100

for value in range(0,max_value):

    pawn_rank_mult = 1 + value/10
    
    piece_values_dict = {
        "p": 1/pawn_rank_mult,
        "n": 3,
        "b": 3,
        "r": 5,
        "q": 9,
        "P": 1/pawn_rank_mult,
        "N": 3,
        "B": 3,
        "R": 5,
        "Q": 9
    }
    
    # calculate value of starting pieces
    start_value = 39
    
    fen_list = []
    
    for j in range(0, max_combinations):
    
        # initialise the basic fen and available ranges for this iteration
        fen = basic_fen
        black_available_range = black_range.copy()
    
        # replace 8 random pieces on black side
        for i in range(0, 8):
    
            # select a random position
            pos = black_available_range.pop(
                random.randint(0, len(black_available_range)-1))
            # select a random piece
            piece = random.choice(pieces)
            # add piece into fen at the position
            fen = fen[:pos] + piece + fen[pos+1:]
    
        # calculate value
        black_pawn_pieces = ""
        black_pawn_pieces = [black_pawn_pieces + fen[pos]
                             for pos in black_pawn_rank]
        black_pawn_values = [piece_values_dict[piece]
                             for piece in black_pawn_pieces]
        black_first_pieces = ""
        black_first_pieces = [black_first_pieces + fen[pos]
                              for pos in black_first_rank]
        black_first_values = [piece_values_dict[piece]
                              for piece in black_first_pieces]
        black_value = sum(black_first_values) + \
            sum(black_pawn_values) * pawn_rank_mult
    
        # now create an equal value board for white
        equal_values = False
        white_value = start_value
        while not equal_values:
    
            # select a random position
            pos = random.choice(white_range)
            # select a random piece
            piece = random.choice(pieces).upper()
    
            if pos in white_pawn_rank:
                mult = pawn_rank_mult
            else:
                mult = 1
    
            white_value = white_value + (
                piece_values_dict[piece] - piece_values_dict[fen[pos]]
            ) * mult
    
            fen = fen[:pos] + piece + fen[pos+1:]
    
            equal_values = abs(white_value - black_value)<1
    
        fen_list.append(fen)
    
    
    max_games = 10
    skill1 = 19
    skill2 = 19
    
    for fen in fen_list:
        result = rand_skill_battle(
            "variant1", fen, max_games, skill1, skill2).split(" ")
        results.append([pawn_rank_mult, fen, fen.count("p"), fen.count("P")] + result)
        
        counter = counter+1
        print(round(counter/(max_value*max_combinations),ndigits=2))


# create results_df
results_df = pd.DataFrame(results, columns=['pawn_rank_mult','fen', 'b_pawns', 'w_pawns', 'w', 'l', 'd'])

# count p in pawn row and P
results_df['pawn_diff'] = results_df.apply(
    lambda x: x['fen'][9:17].count('p') - x['fen'][26:35].count('P'), axis=1)

results_df['w'] = results_df['w'].astype(int)
results_df['l'] = results_df['l'].astype(int)
results_df['d'] = results_df['d'].astype(int)

# analyse results
results_df_equal = results_df[results_df['pawn_diff'] == 0]
result_df_w_pawns = results_df[results_df['pawn_diff'] < 0]
result_df_b_pawns = results_df[results_df['pawn_diff'] > 0]

for i in range(0, max_value):
    df = results_df[results_df['pawn_rank_mult']==1+i/10]
