# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 15:17:33 2025

@author: jackm
"""

import subprocess
import os
import pandas as pd
import random
import time

def rand_skill_battle(variant_name, start_fen, max_games, fairy_piece):
    
    # Define paths 
    varini_path = r"variants.ini"
    engine1_path = r"fairy-stockfish_x86-64-bmi2.exe"
    engine2_path = r"fairy-stockfish_x86-64-bmi2-player2.exe"
    script_path = r"variantfishtestv3.py"
    output_path = r"output.txt"
    skill1 = 19
    skill2 = 19
    
    # create variants.ini file
    varini_text = f"[{variant_name}:chess]\n{fairy_piece} = w\nstartFen = {start_fen}"
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
        
    result  = output[-1]
    
    return result

start = time.time()

results = []
max_games = 100
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"
possible_pieces = ['w']
possible_positions = [0,1,2]
# [x for x in range(0,4)]+[x for x in range(5,8)] + [
#     x for x in range(9,17)]+[x for x in range(26,34)]+[
#         x for x in range(35,39)] + [x for x in range(40,43)]

skill1 = 19
skill2 = 19      

for new_piece in possible_pieces:
    for pos in possible_positions:
        
        # pick random position and assign a random piece there
        # pos = random.choice(possible_positions)
        # new_piece = random.choice(possible_pieces)
        
        new_piece = new_piece if pos < 25 else new_piece.upper()
        old_piece = fen[pos]
        start_fen = fen[:pos] + new_piece + fen[pos+1:]
        result = rand_skill_battle("variant1", start_fen, max_games, "chancellor").split(" ")
        results.append([pos, old_piece, new_piece] + result)
    

results_df = pd.DataFrame(results, columns=['pos','old_piece','new_piece','w','l','d'])

results_df.to_excel("testing_results.xlsx")

print(time.time()-start)
