# -*- coding: utf-8 -*-
"""
Created on Sat Mar 22 15:17:33 2025

@author: jackm
"""

import subprocess
import os
import time

start_time = time.time()

# Define variant
variant_name = "basic"
start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w kqKQ - 0 1"

# define engine options
e1_options = ""
e2_options = e1_options

# Define paths 
varini_path = r"variants.ini"
engine_path = r"fairy-stockfish_x86-64-bmi2.exe"
script_path = r"variantfishtest.py"
output_path = r"output.txt"

# create variants.ini file
varini_text = f"[{variant_name}:chess]\nchancellor = w\nstartFen = {start_fen}"
with open(varini_path, 'w') as file:
    file.write(varini_text)

# create engine option strings
e1_options = " ".join(["--e1-options "+option for option in e1_options.split(" ")])
e2_options = " ".join(["--e2-options "+option for option in e2_options.split(" ")])

if e1_options=='--e1-options ':
    e1_options = ""
  
if e2_options=='--e2-options ':
    e2_options = ""

# remove outputs file
if os.path.exists(output_path):
    os.remove(output_path)

# Construct command
cmd = f'python "{script_path}" "{engine_path}" "{engine_path}" {e1_options} {e2_options} -t 10000 -n 10 -c {varini_path} -v "{variant_name}" -l output.txt --verbosity 2 -d 8'
# Run command and capture output
# result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
result = subprocess.run(cmd, shell=True)

# read output file
with open(output_path) as f:
    output = f.readlines()
    
result  = output[-1]

# time to complete
print(time.time() - start_time)