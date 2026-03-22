# -*- coding: utf-8 -*-
"""
Created on Sat Apr  5 18:25:21 2025

@author: jackm
"""

import subprocess

def send_uci_commands():
    # Launch Fairy-Stockfish (adjust path if needed)
    engine = subprocess.Popen(
        [r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-bmi2.exe"],  # or full path to binary
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
        bufsize=1,
    )

    def send(cmd):
        engine.stdin.write(cmd + '\n')
        engine.stdin.flush()

    def read():
        lines = []
        while True:
            line = engine.stdout.readline()
            if line.strip() == "":
                break
            lines.append(line.strip())
        return lines

    # Initialize UCI mode
    send("uci")
    read()  # discard startup info

    send("ucinewgame")
    send("isready")
    read()

    # Set up a position (example with promotion possibility)
    send("position fen 8/P7/8/8/8/8/8/k6K w - - 0 1")

    # Send the "d" command to display board
    send("d")
    output = read()

    # Show board state
    print("\n".join(output))

    # Clean up
    send("quit")

send_uci_commands()