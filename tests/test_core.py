from unittest import TestCase

from cpu import CPU, PC
from game import Game


class TestCPU(TestCase):
    cpu: CPU

    def setUp(self) -> None:
        self.cpu = CPU(Game())

    def test_timer(self):
        self.cpu.memory[0xd] = 1
        self.cpu.memory[0xc] = 4
        self.cpu._CPU__timer()
        self.assertEqual(self.cpu.current_cycle, 1)
        self.cpu.memory[0xa] = 4
        self.cpu._CPU__timer()
        self.cpu._CPU__timer()
        self.cpu._CPU__timer()
        self.assertEqual(self.cpu.current_cycle, 0)
        self.assertEqual(self.cpu.memory[0xb], 1)

        for _ in range(3):
            self.cpu._CPU__timer()
            self.cpu._CPU__timer()
            self.cpu._CPU__timer()
            self.cpu._CPU__timer()

        self.assertEqual(self.cpu.memory[0xD], 0)
        self.assertEqual(self.cpu.registers[PC], 0)
