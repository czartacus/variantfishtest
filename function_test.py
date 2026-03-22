# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 15:17:33 2025

@author: jackm
"""

import subprocess
import os
import pandas as pd

def call_variantfishtest(variant_name, start_fen, max_games, depth):
    
    # Define paths 
    varini_path = r"variants.ini"
    engine_path = r"fairy-stockfish_x86-64-bmi2.exe"
    script_path = r"variantfishtest.py"
    output_path = r"output.txt"
    
    # create variants.ini file
    varini_text = f"[{variant_name}:chess]\nchancellor = w\nstartFen = {start_fen}"
    with open(varini_path, 'w') as file:
        file.write(varini_text)
  
    # remove outputs file
    if os.path.exists(output_path):
        os.remove(output_path)
    
    # Construct command
    cmd = f'python "{script_path}" "{engine_path}" "{engine_path}" -t 1000 -n {max_games} -c {varini_path} -v "{variant_name}" -l output.txt --verbosity 2 -d {depth}'
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
depth = 5
pieces = ['p','n','b','r','q'] # ['P','N','B','R','Q']
fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"

for depth in range(1,9):
    for piece in pieces:
        for pos in range(0,43):
            if fen[pos].lower() != "k" and fen[pos] != "/" and not fen[pos].isdigit():
                
                old_piece = fen[pos]
                color = 'b'
                
                if fen[pos].upper() == fen[pos]:
                    piece = piece.upper()
                    color = 'w'
                    
                start_fen = fen[:pos] + piece + fen[pos+1:]
                result = call_variantfishtest("testingfunction", start_fen, max_games, depth).split(" ")
                results.append([depth,color,old_piece,piece,pos] + result)
        

results_df = pd.DataFrame(results, columns=['depth','color','oldpiece','piece','pos','w','l','d'])

results_df.to_excel("testing_results.xlsx")
