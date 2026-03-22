# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 15:17:33 2025

@author: jackm
"""

import subprocess
import os
import pandas as pd
import random

def rand_engine_battle(variant_name, start_fen, max_games, depth1, depth2):
    
    # Define paths 
    varini_path = r"variants.ini"
    engine1_path = r"fairy-stockfish_x86-64-bmi2.exe"
    engine2_path = r"fairy-stockfish_x86-64-bmi2-player2.exe"
    script_path = r"variantfishtestv2.py"
    output_path = r"output.txt"
    
    # create variants.ini file
    varini_text = f"[{variant_name}:chess]\nchancellor = w\nstartFen = {start_fen}"
    with open(varini_path, 'w') as file:
        file.write(varini_text)
  
    # remove outputs file
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Construct command
    cmd = f'python "{script_path}" "{engine1_path}" "{engine2_path}" -t 1000 -n {max_games} -c {varini_path} -v "{variant_name}" -l output.txt --verbosity 2 -d1 {depth1} -d2 {depth2}'
    # Run command and capture output
    # result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    result = subprocess.run(cmd, shell=True)
    
    # read output file
    with open(output_path) as f:
        output = f.readlines()
        
    result  = output[-1]
    
    return result


results = []
max_games = 1
max_i = 100
depth = 5
start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
min_depth = 3
max_depth = 13

for i in range(0, max_i):
    depth1 = random.randint(min_depth, max_depth)
    depth2 = random.randint(min_depth, max_depth)
    result = rand_engine_battle("chess", start_fen, max_games, depth1, depth2).split(" ")
    results.append([depth1,depth2] + result)
    

results_df = pd.DataFrame(results, columns=['depth1','depth2','w','l','d'])

results_df.to_excel("testing_results.xlsx")
