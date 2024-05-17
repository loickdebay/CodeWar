from unittest import TestCase

from cpu import CPU, MemoryType, SP
from game import Game


class TestData(TestCase):

    def setUp(self) -> None:
        self.cpu = CPU(Game())

    def create_instruction(self, instruction: int) -> bytearray:
        memory_type = MemoryType.register.value  # Rn
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        byte2 = source
        return bytearray([byte1, byte2])

    def test_push(self):
        instruction = self.create_instruction(0x01)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 150
        self.cpu.registers[SP] = 256
        self.cpu.execute()
        byte1 = self.cpu.memory[254]
        byte2 = self.cpu.memory[255]
        value = (byte1 << 8) | byte2
        self.assertEqual(value, 150)

    def test_pop(self):
        instruction = self.create_instruction(0x02)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[SP] = 254
        self.cpu.memory[254] = 0xff
        self.cpu.memory[255] = 0xff
        self.cpu.execute()
        value = self.cpu.registers[0]
        self.assertEqual(value, 0xffff)

    def test_move(self):
        instruction = 0x00
        h = 1
        l = 1
        source = MemoryType.register
        destination = MemoryType.address
        registre_source = 0
        word1 = instruction << 11 | h << 10 | l << 9 | source.value << 6 | destination.value << 3 | registre_source
        byte1 = word1 >> 8
        byte2 = word1 & 0xff
        word2 = 0x0100
        byte3 = word2 >> 8
        byte4 = word2 & 0xff
        self.cpu.memory[0] = byte1
        self.cpu.memory[1] = byte2
        self.cpu.memory[2] = byte3
        self.cpu.memory[3] = byte4
        self.cpu.registers[registre_source] = 0xffff
        self.cpu.pos_x = 0
        self.cpu.pos_y = 0
        game = Game()
        other = CPU(game)
        original = other.memory[1]
        other.pos_x = 1
        other.pos_y = 0
        game.board = [[self.cpu, other]]
        self.cpu.execute()
        self.assertEqual(other.memory[0], 0xff)
        self.assertEqual(other.memory[1], original)
