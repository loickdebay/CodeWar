from unittest import TestCase

from cpu import CPU, MemoryType, PC
from game import Game


class TestJxx(TestCase):
    def setUp(self) -> None:
        self.cpu = CPU(Game())

    def create_instruction(self, instruction: int) -> bytearray:
        memory_type = MemoryType.register.value  # Rn
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        byte2 = source
        return bytearray([byte1, byte2])

    def test_jump_carry_clear(self):
        instruction = 0x14  # jcc
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 10)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_c(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)

    def test_jump_carry_set(self):
        instruction = 0x15  # jcs
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_c(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)

    def test_jump_equal(self):
        instruction = 0x16  # jeq
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_z(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)

    def test_jump_not_equal(self):
        instruction = 0x17  # jne
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_z(0)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)

    def test_jump_less_or_equal(self):
        instruction = 0x18  # jle
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_z(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)
        self.cpu.flags.set_z(0)
        self.cpu.flags.set_c(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)

    def test_jump_greater_or_equal(self):
        instruction = 0x19  # jge
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_z(1)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)
        self.cpu.flags.set_z(1)
        self.cpu.flags.set_c(0)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)

    def test_jump_always(self):
        instruction = 0x1A  # jmp
        instruction = self.create_instruction(instruction)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.flags.set_z(16)
        self.cpu.flags.set_c(-5)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 0)


class TestBxx(TestCase):

    def setUp(self) -> None:
        self.cpu = CPU(Game())

    def create_instruction(self, instruction: int) -> bytearray:
        memory_type = MemoryType.register.value  # Rn
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        byte2 = source
        return bytearray([byte1, byte2])

    def test_branch_carry_clear(self):
        instruction = 0x0C  # bcc
        memory_type = MemoryType.register.value  # Rn
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        self.cpu.memory[0] = byte1
        byte2 = source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)

    def test_branch_carry_set(self):
        instruction = 0x0D  # and
        memory_type = MemoryType.register.value  # Rn
        source = 0b000  # R0
        byte1 = instruction << 3 | memory_type
        self.cpu.memory[0] = byte1
        byte2 = source
        self.cpu.memory[1] = byte2
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_c(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)

    def test_branch_equal(self):
        instruction = self.create_instruction(0x0E)  # beq
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_z(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)

    def test_branch_not_equal(self):
        instruction = self.create_instruction(0x0F)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_z(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)

    def test_branch_less_or_equal(self):
        instruction = self.create_instruction(0x10)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_c(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)
        self.cpu.registers[PC] = 0
        self.cpu.flags.reset()
        self.cpu.flags.set_z(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)

    def test_branch_greater_or_equal(self):
        instruction = self.create_instruction(0x11)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)
        self.cpu.registers[PC] = 0
        self.cpu.flags.set_c(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 2)
        self.cpu.registers[PC] = 0
        self.cpu.flags.reset()
        self.cpu.flags.set_z(True)
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)

    def test_branch_always(self):
        instruction = self.create_instruction(0x12)
        self.cpu.memory[0] = instruction[0]
        self.cpu.memory[1] = instruction[1]
        self.cpu.registers[0] = 10
        self.cpu.execute()
        self.assertEqual(self.cpu.registers[PC], 12)
