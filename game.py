from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List

import random
import pathlib
import sys
import argparse

from cpu import CPU
from view import View

DEFAULT_FILE = pathlib.Path(__file__).parent / "res" / "default.bin"

"""
used for the test of the view

def convert_24bit_to_5bit(color_24bit):
    # Extracting individual color components
    red_8bit = (color_24bit >> 16) & 0xFF
    green_8bit = (color_24bit >> 8) & 0xFF
    blue_8bit = color_24bit & 0xFF

    # Compressing 8-bit components to 5-bit
    red_5bit = (red_8bit >> 3) & 0b11111
    green_5bit = (green_8bit >> 3) & 0b11111
    blue_5bit = (blue_8bit >> 3) & 0b11111

    # Combining the 5-bit components into a 2-byte color
    color_5bit = (red_5bit << 10) | (green_5bit << 5) | blue_5bit

    return color_5bit


COLOR = convert_24bit_to_5bit(0xFFC0CB)
MEMORY = bytearray(256)

MEMORY[0] = COLOR >> 8
MEMORY[1] = COLOR & 0xFF
"""


class Game:
    board: List[List[CPU]]
    view: View
    player1_color: int
    player2_color: int
    max_cycles: int

    def __init__(self, max_cycles: int) -> None:
        self.max_cycles = max_cycles
        self.view = View(self)
        # self.board = [[CPU(self, MEMORY.copy()) for _ in range(16)] for _ in range(16)] used for the test of the view
        board = []
        for y in range(16):
            array = []
            for x in range(16):
                cpu = CPU.load_from_file(DEFAULT_FILE.resolve(), self)
                cpu.pos_x = x
                cpu.pos_y = y
                array.append(cpu)
            board.append(array)
        self.board = board
        # self.board = [[CPU.load_from_file(DEFAULT_FILE.resolve(), self) for _ in range(16)] for _ in range(16)]

    def start(self):
        try:
            print("Joueur 1")
            try:
                player1_cpu = CPU.load(self)
            except FileNotFoundError:
                print("Fichier non trouvé")
                return self.start()
            while True:
                try:
                    print("Joueur 2")
                    player2_cpu = CPU.load(self)
                    break
                except FileNotFoundError:
                    print("Fichier non trouvé")
        except EOFError:
            print("A une prochaine fois !")
            return
        player1_x = random.randint(0, 15)
        player1_y = random.randint(0, 15)
        player1_cpu.pos_x = player1_x
        player1_cpu.pos_y = player1_y
        player2_x = random.randint(0, 15)
        player2_y = random.randint(0, 15)
        player2_cpu.pos_x = player2_x
        player2_cpu.pos_y = player2_y
        self.board[player1_x][player1_y] = player1_cpu
        self.player1_color = player1_cpu.memory[0] << 8 | player1_cpu.memory[1]
        self.board[player2_x][player2_y] = player2_cpu
        self.player2_color = player2_cpu.memory[0] << 8 | player2_cpu.memory[1]

    def game(self):
        try:
            self.start()
            self.view.initialize()
            input("Adaptez la taille de la fenêtre et appuyez sur entrée pour commencer")
            current_cycle = 0
            while current_cycle < self.max_cycles:
                current_cycle += 1
                for array in self.board:
                    for cpu in array:
                        cpu.execute()
                self.view.update()
                winner = self.__check_if_winner_exists()
                if winner:
                    if winner == self.player1_color:
                        print("Le gagnant est le joueur 1")
                    else:
                        print("Le gagnant est le joueur 2")
                    return
            self.__show_winner()
        except KeyboardInterrupt:
            print("A une prochaine fois !")
            sys.exit(1)

    def __show_winner(self):
        player1_count = 0
        player2_count = 0
        for array in self.board:
            for cpu in array:
                if (cpu.memory[0] << 8 | cpu.memory[1]) == self.player1_color:
                    player1_count += 1
                elif (cpu.memory[0] << 8 | cpu.memory[1]) == self.player2_color:
                    player2_count += 1
        if player1_count > player2_count:
            print("Le gagnant est le joueur 1")
        elif player1_count < player2_count:
            print("Le gagnant est le joueur 2")
        else:
            print("Égalité")

    def __check_if_winner_exists(self):
        first_color = self.board[0][0].memory[0] << 8 | self.board[0][0].memory[1]
        for array in self.board:
            for cpu in array:
                if (cpu.memory[0] << 8 | cpu.memory[1]) != first_color:
                    return False
        return first_color


if __name__ == "__main__":
    parser = argparse.ArgumentParser("codeWar", description="Start a game of codeWar")
    parser.add_argument(
        "-c"
        "--cycles",
        help="number of cycle to run through, default goes to 1000",
        type=int,
        default=1000,
        required=False,
    )
    args = parser.parse_args()
    cycles = args.c__cycles
    Game(cycles).game()
