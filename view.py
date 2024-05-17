from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game import Game


RESET = '\033[0m'


class View:
    def __init__(self, game: Game):
        self.game = game

    def initialize(self):
        self.print_board()
        self.print_player_colors()

    def update(self):
        self.print_board()
        self.print_player_colors()

    def print_board(self):
        print("Plateau de jeu:")
        print("+-----------------------------+")

        for array in self.game.board:
            for cpu in array:
                color = cpu.memory[0] << 8 | cpu.memory[1]
                print(f"|{self.get_color_escape(*self.convert_5bit_to_8bit(color))}  B  {RESET}", end="")
            print("|")

        print("+-----------------------------+")

    def print_player_colors(self):
        print(f"{self.get_color_escape(*self.convert_5bit_to_8bit(self.game.player1_color))}Joueur 1{RESET}")
        print(f"{self.get_color_escape(*self.convert_5bit_to_8bit(self.game.player2_color))}Joueur 2{RESET}")

    def get_color_escape(self, r, g, b, background=False):
        return '\033[{};2;{};{};{}m'.format(48 if background else 38, r, g, b)

    def convert_5bit_to_8bit(self, color_5bit):
        # Extracting individual color components
        red_5bit = (color_5bit >> 10) & 0b11111
        green_5bit = (color_5bit >> 5) & 0b11111
        blue_5bit = color_5bit & 0b11111

        # Expanding 5-bit components to 8-bit
        red_8bit = (red_5bit << 3) | (red_5bit >> 2)
        green_8bit = (green_5bit << 3) | (green_5bit >> 2)
        blue_8bit = (blue_5bit << 3) | (blue_5bit >> 2)

        return red_8bit, green_8bit, blue_8bit
