from unittest import TestCase

from cpu import CPU, MemoryType, PC
from game import Game


class TestCPU(TestCase):

    def setUp(self) -> None:
        self.cpu = CPU(Game())

    def test_add(self):
        instruction = 0x03
        memory_type = MemoryType.register.value

        source = 0b000
        destination = 0b001

        valeur1 = 0b1
        valeur2 = 0b1

        self.cpu.memory[0] = instruction << 3 | destination
        self.cpu.memory[1] = memory_type << 5 | source

        self.cpu.registers[0] = valeur1
        self.cpu.registers[1] = valeur2

        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 2)
        self.assertEqual(self.cpu.flags.get_c(), 0)
        self.assertEqual(self.cpu.flags.get_z(), 0)
        self.assertEqual(self.cpu.flags.get_n(), 0)

    def test_cmp(self):
        instruction = 0x04
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b11
        self.cpu.registers[1] = 0b10
        self.cpu.execute()
        self.assertEqual(self.cpu.flags.get_c(), 1)
        self.assertEqual(self.cpu.flags.get_z(), 0)
        self.assertEqual(self.cpu.flags.get_n(), 1)
        self.assertEqual(self.cpu.registers[1], 0b10)

    def test_sub(self):
        instruction = 0x05
        memory_type = MemoryType.register.value

        source = 0b000
        destination = 0b001

        valeur1 = 0b0001
        valeur2 = 0b0001

        self.cpu.memory[0] = instruction << 3 | destination
        self.cpu.memory[1] = memory_type << 5 | source

        self.cpu.registers[0] = valeur1
        self.cpu.registers[1] = valeur2

        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0)
        self.assertEqual(self.cpu.flags.get_c(), 0)
        self.assertEqual(self.cpu.flags.get_z(), 1)
        self.assertEqual(self.cpu.flags.get_n(), 0)

    def test_lsl(self):
        instruction = 0x06
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b01
        self.cpu.registers[1] = 0b01
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b10)
        self.assertEqual(self.cpu.flags.get_c(), 0)
        self.assertEqual(self.cpu.flags.get_z(), 0)
        self.assertEqual(self.cpu.flags.get_n(), 0)

    def test_lsr(self):
        instruction = 0x07
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b01
        self.cpu.registers[1] = 0b10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b01)
        self.assertEqual(self.cpu.flags.get_c(), 1)
        self.assertEqual(self.cpu.flags.get_z(), 0)
        self.assertEqual(self.cpu.flags.get_n(), 0)

    def test_and(self):
        instruction = 0x08  # and
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b11
        self.cpu.registers[1] = 0b10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b10)

    def test_or(self):
        instruction = 0x09  # or
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b11
        self.cpu.registers[1] = 0b10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b11)

    def test_xor(self):
        instruction = 0x0A  # xor
        memory_type = MemoryType.register.value  # Rn
        destination = 0b001  # R1
        source = 0b000  # R0
        byte1 = instruction << 3 | destination
        self.cpu.memory[0] = byte1
        byte2 = memory_type << 5 | source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 0b11
        self.cpu.registers[1] = 0b10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b1)
        self.cpu.registers[PC] -= 2
        self.cpu.registers[1] = 0b11
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[1], 0b00)

    def create_instruction(self, instruction: int) -> bytearray:
        memory_type = MemoryType.register.value
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        byte2 = source
        return bytearray([byte1, byte2])

    def test_not(self):
        instruction = self.create_instruction(0x0B)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 0b1000
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[0], 0b0111)
