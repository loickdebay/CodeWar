from cpu import CPU
from game import DEFAULT_FILE, Game

cpu = CPU.load_from_file(DEFAULT_FILE, Game())


cpu.run()