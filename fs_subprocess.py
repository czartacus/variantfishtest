import subprocess
import time

class UCIEngine:
    def __init__(self, engine_path, variant=None, variants_ini_path=None):
        self.engine = subprocess.Popen(
            engine_path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        self._initialize_engine(variant, variants_ini_path)

    def send_command(self, command):
        print(f">>> {command}")
        self.engine.stdin.write(command + "\n")
        self.engine.stdin.flush()

    def wait_for(self, keyword, timeout=5):
        start = time.time()
        while True:
            if time.time() - start > timeout:
                raise TimeoutError(f"Timeout waiting for '{keyword}'")
            output = self.engine.stdout.readline().strip()
            if output:
                print(f"<<< {output}")
            if keyword in output:
                break

    def _initialize_engine(self, variant, variants_ini_path):
        self.send_command("uci")
        self.wait_for("uciok")
        self.send_command("isready")
        self.wait_for("readyok")

        if variants_ini_path:
            self.send_command(f'setoption name VariantPath value {variants_ini_path}')
        if variant:
            self.send_command(f'setoption name UCI_Variant value {variant}')

        self.send_command("ucinewgame")
        self.send_command("isready")
        self.wait_for("readyok")

    def get_best_move(self, moves=[]):
        if moves:
            self.send_command(f"position startpos moves {' '.join(moves)}")
        else:
            self.send_command("position startpos")
        self.send_command("go movetime 1000")
        while True:
            line = self.engine.stdout.readline().strip()
            if line:
                print(f"<<< {line}")
            if line.startswith("bestmove"):
                return line.split()[1]

    def close(self):
        self.send_command("quit")
        self.engine.terminate()

if __name__ == "__main__":
    engine_path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\fairy-stockfish_x86-64-modern.exe"
    variant_name = "sneakypawn"  # Defined in variants.ini
    variants_ini_path = r"C:\Users\jackm\Downloads\variantfishtest-master\variantfishtest-master\variants1.ini"

    engine = UCIEngine(engine_path, variant=variant_name, variants_ini_path=variants_ini_path)

    moves = []
    for turn in range(10):
        move = engine.get_best_move(moves)
        print(f"Engine move: {move}")
        moves.append(move)
        # Insert your move here if needed

    engine.close()
