from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Callable, Union
    from pathlib import Path
    from game import Game

from inspect import signature

from enum import Enum

from random import randint

from exception import OutOfBoundsError, Interruption

PC = 6
SP = 7
ILLEGAL = 2
TIMER = 3
TRAP = 4


class MoveType(Enum):
    default = 0b11
    move_h = 0b10
    move_l = 0b01


class MemoryType(Enum):
    register = 0b000
    pre_decremented_register = 0b001
    inderect_addressing = 0b010
    post_incremented_register = 0b011
    immediate_value = 0b100
    address = 0b101


class Flags:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def reset(self):
        self.value = 0

    def set_c(self, value: bool):
        self.value |= value

    def set_z(self, value: bool):
        value = value << 1
        self.value |= value

    def set_n(self, value: bool):
        value = value << 2
        self.value |= value

    def get_c(self) -> int:
        return self.value & 0b1

    def get_z(self) -> int:
        return (self.value >> 1) & 0b1

    def get_n(self) -> int:
        return (self.value >> 2) & 0b1

    def get(self) -> int:
        return self.value & 0xffff


class CPU:
    memory: bytearray
    registers: List[int]
    instructions: dict[str, Callable]
    flags: Flags
    game: Game
    pos_x: int
    pos_y: int
    current_cycle: int
    NON_INSTRUCTION_FUNC = ["execute", "decode", "run"]
    instruction_names = {
        0x00: "move",
        0x01: "push",
        0x02: "pop",
        0x03: "add",
        0x04: "cmp",
        0x05: "sub",
        0x06: "lsl",
        0x07: "lsr",
        0x08: "i_and",
        0x09: "i_or",
        0x0A: "xor",
        0x0B: "i_not",
        0x0C: "branch_carry_clear",
        0x0D: "branch_carry_set",
        0x0E: "branch_equal",
        0x0F: "branch_not_equal",
        0x10: "branch_less_or_equal",
        0x11: "branch_greater_or_equal",
        0x12: "branch_always",
        0x13: "bsr",
        0x14: "jump_carry_clear",
        0x15: "jump_carry_set",
        0x16: "jump_equal",
        0x17: "jump_not_equal",
        0x18: "jump_less_or_equal",
        0x19: "jump_greater_or_equal",
        0x1A: "jump_always",
        0x1B: "jsr",
        0x1C: "rts",
        0x1D: "trap",
        0x1E: "rte",
    }

    def __init__(self, game: Game, memory=bytearray(256)):
        self.game = game
        self.memory = memory
        self.registers = [0, 0, 0, 0, 0, 0, 0, 0]
        self.flags = Flags()
        self.instructions = {name: getattr(self, name) for name in dir(self)}
        self.current_cycle = 0

    def run(self):
        while True:
            self.execute()

    def execute(self):
        """
        execute the instruction at the current PC
        Because of the way the full move instruction is encoded
        we need to check if the instruction is move or not for the PC incrementation
        """
        instruction = self.memory[self.registers[PC]: self.registers[PC] + 2]
        try:
            values = self.decode(instruction)
        except Exception:
            self.interruption(ILLEGAL)
            return
        if values[0] == "move":
            instruction = self.memory[self.registers[PC]: self.registers[PC] + 4]
            values = self.decode(instruction)
            self.registers[PC] += 4
        else:
            self.registers[PC] += 2
        try:
            self.instructions[values[0]](*values[1:])
        except Exception:
            pass
        self.__timer()

    def decode(self, instruction: bytearray) -> tuple:
        """Decode an instruction to retrieve the instruction name and operands

        Args:
            instruction (bytearray): The 2 or 4 bytes instruction to decode

        Returns:
            tuple: Instruction name and operands
        """
        instruction_value = (instruction[0] & 0b11111000) >> 3
        instruction_name = self.__get_instruction_name(instruction_value)
        parameters = self.__get_number_of_parameters(instruction_name)

        if instruction_name == "move" and len(instruction) < 4:
            # Move instruction is encoded on 4 bytes
            # And first try of decode is done with 2 bytes
            return ["move"]

        if parameters == 0:
            return (instruction_name,)
        else:
            if parameters == 1:
                source_type = MemoryType(instruction[0] & 0b00000111)
                return (instruction_name, source_type, instruction[1])
            elif parameters == 2:
                register = instruction[0] & 0b00000111
                source_type = MemoryType((instruction[1] & 0b11100000) >> 5)
                value = instruction[1] & 0b00011111
                return (instruction_name, source_type, value, register)
            else:  # move instruction
                move_type = self.__get_move_type(instruction)
                source_type = MemoryType((instruction[0] & 0b1) << 2 | (instruction[1] & 0b11000000) >> 6)
                destination_type = MemoryType((instruction[1] & 0b00111000) >> 3)
                source = instruction[1] & 0b00000111
                destination = instruction[2] << 8 | instruction[3]
                return (instruction_name, move_type, source_type, destination_type, source, destination)

    def interruption(self, interruption_vector: int):
        """Branch to the interruption vector"""
        self.push(MemoryType.register, PC)
        self.registers[PC] = self.memory[interruption_vector]
        self.push(MemoryType.immediate_value, self.flags.get())

    def __timer(self):
        """Check if the timer interruption should be triggered"""
        enabled = self.memory[0xD]
        if enabled == 1 or enabled == 2:
            self.current_cycle += 1
            cycle_increment = self.memory[0xC]
            if self.current_cycle == cycle_increment:
                self.current_cycle = 0
                self.memory[0xB] += 1
                if self.memory[0xB] == self.memory[0xA]:
                    self.memory[0xD] = 0 if enabled == 1 else 2
                    self.interruption(TIMER)

    def __get_number_of_parameters(self, instruction_name: str) -> int:
        return len(signature(self.instructions[instruction_name]).parameters) - 1

    def __get_instruction_name(self, instruction_name: int) -> str:
        return self.instruction_names[instruction_name]

    def __get_move_type(self, instruction: bytearray) -> MoveType:
        flags = (instruction[0] & 0b00000110) >> 1
        return MoveType(flags)

    @classmethod
    def load(cls, game: Game) -> CPU:
        file_path = input("Enter the path of the assembly file: ")
        blue = randint(0, 0b11111)
        red = randint(0, 0b11111)
        green = randint(0, 0b11111)
        color = (red << 10) | (green << 5) | blue
        return cls.load_from_file(file_path, game, color)

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path], game: Game, color=0x0000) -> CPU:
        file = open(file_path, "rb")
        data = bytearray(256)
        for i, byte in enumerate(file.read()):
            data[i + 0x10] = byte
        file.close()
        data[0] = color >> 8
        data[1] = color & 0xff
        cpu = cls(game, data)
        cpu.registers[PC] = 0x10
        return cpu

    def move(self, move_type: MoveType, source_type: MemoryType, destination_type: MemoryType, first_word_value: int, second_word_value: int):

        if move_type == MoveType.move_h:
            flag_n, flag_z = self.__move_h(source_type, destination_type, first_word_value, second_word_value)
        elif move_type == MoveType.move_l:
            flag_n, flag_z = self.__move_l(source_type, destination_type, first_word_value, second_word_value)
        else:
            flag_n, flag_z = self.__move(source_type, destination_type, first_word_value, second_word_value)

        self.flags.set_c(False)
        self.flags.set_n(flag_n)
        self.flags.set_z(flag_z)

    def __move(self, source_type: MemoryType, destination_type: MemoryType, first_word_value: int, second_word_value: int):
        if source_type == MemoryType.address or source_type == MemoryType.immediate_value:
            if source_type == MemoryType.immediate_value:
                value = second_word_value
            if source_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                value = cpu.memory[second_word_value & 0xff]

            if destination_type == MemoryType.register:
                self.registers[first_word_value] = value

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[first_word_value] -= 2
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[first_word_value]] = value
                self.registers[first_word_value] += 2
        else:
            value = self.__get_source_value(source_type, first_word_value)

            if destination_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                cpu.memory[second_word_value & 0xff] = value & 0xff

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[second_word_value] -= 2
                self.memory[self.registers[second_word_value]] = value & 0xff

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[second_word_value]] = value & 0xff

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[second_word_value]] = value & 0xff
                self.registers[second_word_value] += 2

            elif destination_type == MemoryType.register:
                self.registers[second_word_value] = value
        flag_n = value >> 15
        flag_z = value == 0
        return flag_n, flag_z

    def __move_h(self, source_type: MemoryType, destination_type: MemoryType, first_word_value: int, second_word_value: int):
        if source_type == MemoryType.address or source_type == MemoryType.immediate_value:
            if source_type == MemoryType.immediate_value:
                value = second_word_value >> 8
            if source_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                value = cpu.memory[second_word_value & 0xff]

            if destination_type == MemoryType.register:
                self.registers[first_word_value] |= value

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[first_word_value] -= 1
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[first_word_value]] = value
                self.registers[first_word_value] += 1
        else:
            value = self.__get_source_value(source_type, first_word_value, special_move=True) >> 8

            if destination_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                cpu.memory[second_word_value & 0xff] = value

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[second_word_value] -= 1
                self.memory[self.registers[second_word_value]] = value

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[second_word_value]] = value

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[second_word_value]] = value
                self.registers[second_word_value] += 1

            elif destination_type == MemoryType.register:
                self.registers[second_word_value] |= value
        flag_n = value >> 7
        flag_z = value == 0
        return flag_n, flag_z

    def __move_l(self, source_type: MemoryType, destination_type: MemoryType, first_word_value: int, second_word_value: int):
        if source_type == MemoryType.address or source_type == MemoryType.immediate_value:
            if source_type == MemoryType.immediate_value:
                value = second_word_value & 0xff
            if source_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                value = cpu.memory[second_word_value & 0xff]

            if destination_type == MemoryType.register:
                self.registers[first_word_value] |= value

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[first_word_value] -= 1
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[first_word_value]] = value

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[first_word_value]] = value
                self.registers[first_word_value] += 1
        else:
            value = self.__get_source_value(source_type, first_word_value, special_move=True) & 0xff

            if destination_type == MemoryType.address:
                cpu_address = second_word_value >> 8
                cpu = self.__get_relative_cpu(cpu_address)
                cpu.memory[second_word_value & 0xff] = value

            elif destination_type == MemoryType.pre_decremented_register:
                self.registers[second_word_value] -= 1
                self.memory[self.registers[second_word_value]] = value

            elif destination_type == MemoryType.inderect_addressing:
                self.memory[self.registers[second_word_value]] = value

            elif destination_type == MemoryType.post_incremented_register:
                self.memory[self.registers[second_word_value]] = value
                self.registers[second_word_value] += 1

            elif destination_type == MemoryType.register:
                self.registers[second_word_value] |= value
        flag_n = value >> 7
        flag_z = value == 0
        return flag_n, flag_z

    def __get_relative_cpu(self, cpu_address: int) -> CPU:
        """Get the target cpu relative to the current cpu

        Args:
            cpu_address (int): the relative address of the cpu,
            the first 4 bits are the delta x and the last 4 bits are the delta y

        Raises:
            OutOfBoundsError: if the address point to a cpu outside of the game board

        Returns:
            CPU: the target cpu
        """
        """
        Valeur décimale Valeur Binaire Valeur Hexadécimale
        0               0000           0x0
        1               0001           0x1
        2               0010           0x2
        3               0011           0x3
        4               0100           0x4
        5               0101           0x5
        6               0110           0x6
        7               0111           0x7
        -1              1111           0xF
        -2              1110           0xE
        -3              1101           0xD
        -4              1100           0xC
        -5              1011           0xB
        -6              1010           0xA
        -7              1001           0x9
        -8              1000           0x8
        """
        delta_x = cpu_address >> 4
        delta_x = 0 - (delta_x - 7) if delta_x > 7 else delta_x
        delta_y = cpu_address & 0xf
        delta_y = 0 - (delta_y - 7) if delta_y > 7 else delta_y
        try:
            cpu = self.game.board[self.pos_y + delta_y][self.pos_x + delta_x]
        except IndexError:
            raise OutOfBoundsError("delta x or delta y is out of the game board")

        return cpu

    def single_operand_instruction(self, source_type: MemoryType, source: int):
        pass

    def double_operand_instruction(self, source_type: MemoryType, source: int, destination: int):
        pass

    # Put instruction methods here

    def lsl(self, source_type: MemoryType, source: int, destination: int) -> None:
        """Shift the destination with in argument source

        Args:
            source (int): max 5 Bits (int 31)
            destination (int): max 3 bit (register)
        """

        source_value = self.__get_source_value(source_type, source)
        self.registers[destination] = self.registers[destination] << source_value
        res = self.registers[destination]

        self.flags.reset()

        # ??? FLAG C
        lastbit = self.registers[destination] & 0x8000
        self.flags.set_c(lastbit >> 15)

        # Flag N
        self.flags.set_n(res >> 15)

        # Flag Z
        self.flags.set_z(res == 0)

    def i_not(self, source_type: MemoryType, source: int):
        """Do the not operation on the source

        Args:
            source_type (MemoryType):
            source (int):
        """
        source_value = bin(self.__get_source_value(source_type, source))
        res = ''.join('1' if bit == '0' else '0' for bit in source_value)[2:]
        res = int(res, 2)
        self.registers[source] = res
        self.flags.reset()
        self.flags.set_n(res >> 15)
        self.flags.set_z(res == 0)

    def lsr(self, source_type: MemoryType, source: int, destination: int) -> None:
        """Shift the destination with in argument source

        Args:
            source (int): max 5 Bits (int 31)
            destination (int): max 3 bit (register)
        """

        source_value = self.__get_source_value(source_type, source)
        self.registers[destination] = self.registers[destination] >> source_value
        res = self.registers[destination]

        self.flags.reset()

        # ??? FLAG C
        lastbit = res & 0b1
        self.flags.set_c(lastbit)

        # Flag N
        self.flags.set_n(res >> 15)

        # Flag Z
        self.flags.set_z(res == 0)

    def sub(self, source_type: MemoryType, source: int, destination: int) -> None:
        """Subtraction source to destination

        Args:
            source (int): max 5 Bits (int 31)
            destination (int): max 3 bit (register)
        """

        destValue = self.registers[destination]
        sourceValue = self.__get_source_value(source_type, source)
        self.registers[destination] = destValue - sourceValue

        # Reset
        self.flags.reset()

        # Flag N
        self.flags.set_n(self.registers[destination] >> 15)

        # Flag Z
        self.flags.set_z(self.registers[destination] == 0)

        # Flag C
        self.flags.set_c(self.registers[destination] > self.registers[source])

    def cmp(self, source_type: MemoryType, source: int, destination: int) -> None:
        """Change flags for informations on a compare

        Args:
            source (_type_): max 5 Bits (int 31)
            destination (_type_): max 3 bit (register)
        """

        sourceValue = self.__get_source_value(source_type, source)
        observableResult: int = self.registers[destination] - sourceValue
        self.flags.reset()
        # Flag N
        self.flags.set_n(observableResult < 0)
        # Flag Z
        self.flags.set_z(observableResult == 0)
        # Flag C
        self.flags.set_c(self.registers[destination] < self.registers[source])

    def jump_carry_clear(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if carry flag is 0

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        c = self.flags.get_c()
        source_value = self.__get_source_value(source_type, source)
        if c == 0:
            self.registers[PC] = source_value

    def jump_carry_set(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if carry flag is 1

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        c = self.flags.get_c()
        source_value = self.__get_source_value(source_type, source)
        if c == 1:
            self.registers[PC] = source_value

    def jump_equal(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if zero flag is 1

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        source_value = self.__get_source_value(source_type, source)
        if z == 1:
            self.registers[PC] = source_value

    def jump_not_equal(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if zero flag is 0
        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        source_value = self.__get_source_value(source_type, source)
        if z == 0:
            self.registers[PC] = source_value

    def jump_less_or_equal(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if zero flag is 1 or carry flag is 1
        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        c = self.flags.get_c()
        source_value = self.__get_source_value(source_type, source)
        if z == 1 or c == 1:
            self.registers[PC] = source_value

    def jump_greater_or_equal(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination if zero flag is 1 or carry flag is 0
        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        c = self.flags.get_c()
        source_value = self.__get_source_value(source_type, source)
        if z == 1 or c == 0:
            self.registers[PC] = source_value

    def jump_always(self, source_type: MemoryType, source: int):
        """Sets PC to the value of the destination no matter what
        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        source_value = self.__get_source_value(source_type, source)
        self.registers[PC] = source_value

    def add(self, source_type: MemoryType, source: int, destination: int) -> None:
        """
        add from source to destination

        Args:
            source (int): Can handle a maximum of 5 bits (31 in int)
            destination (int): Register Number max on 3 bits (7 in int)
            source_type (MemomryType):
        """

        destValue = self.registers[destination]
        sourceValue = self.__get_source_value(source_type, source)
        self.registers[destination] = sourceValue + destValue

        self.flags.reset()
        # Flag N
        self.flags.set_n(self.registers[destination] >> 15)

        # Flag Z
        self.flags.set_z(self.registers[destination] == 0)

        # Flag C
        self.flags.set_c(self.registers[destination] > 0xFFFF)

        self.registers[destination] &= 0xFFFF

    def bsr(self, source_type: MemoryType, source: int):
        """Push the PC into the stack and branch to the source

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value.
        """
        value = self.__get_source_value(source_type, source)
        self.push(MemoryType.register, PC)
        self.registers[PC] += value

    def jsr(self, source_type: MemoryType, source: int):
        """Push the PC into the stack and jump to the source

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value.
        """
        value = self.__get_source_value(source_type, source)
        self.push(MemoryType.register, PC)
        self.registers[PC] = value

    def rts(self):
        """Returns from a subroutine by poping the PC from the stack"""
        self.registers[PC] = self.pop(MemoryType.register, PC)

    def push(self, source_type: MemoryType, source: int):
        """Push the value of the source into de stack and decrement stack by 2

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number.
        """
        self.registers[SP] -= 2
        value = self.__get_source_value(source_type, source)
        bit1 = value >> 8
        bit2 = value & 0xff
        self.memory[self.registers[SP]] = bit1
        self.memory[self.registers[SP] + 1] = bit2
        self.flags.set_c(False)
        self.flags.set_n(value >> 15)
        self.flags.set_z(value == 0)

    def pop(self, source_type: MemoryType, source: int):
        """Pop the value of the source from de stack and increment stack by 2

        Args:
            source_type (MemoryType): The memory type of where to store the value
            source (int): The destination integer, can be a register number.
        """
        bit1 = self.memory[self.registers[SP]]
        bit2 = self.memory[self.registers[SP] + 1]
        value = (bit1 << 8) | bit2
        self.registers[SP] += 2
        destination = self.__get_source_value(source_type, source)
        if source_type == MemoryType.register:
            self.registers[source] = value
        else:
            self.memory[destination] = bit1
            self.memory[destination + 1] = bit2
        self.flags.set_c(False)
        self.flags.set_n(value >> 15)
        self.flags.set_z(value == 0)

    def branch_always(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_greater_or_equal(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the zero flag is set or the carry flag is clear

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        c = self.flags.get_c()
        if z == 1 or c == 0:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_less_or_equal(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the zero flag or the carry flag is set

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        c = self.flags.get_c()
        if z == 1 or c == 1:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_not_equal(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the zero flag is clear

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        if z == 0:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_equal(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the zero flag is set

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        z = self.flags.get_z()
        if z == 1:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_carry_set(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the carry flag is set

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        c = self.flags.get_c()
        if c == 1:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def branch_carry_clear(self, source_type: MemoryType, source: int):
        """Add to the PC the value of the source if the carry flag is clear

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            It's the value which will be added to the PC
        """
        c = self.flags.get_c()
        if c == 0:
            self.registers[PC] += self.__get_source_value(source_type, source)

    def i_and(self, source_type: MemoryType, source: int, destination: int):
        """Makes the logical and between the source and the destination and stores the result in the destination

        Args:
            source_type (MemoryType): the memory type of the source
            source (int): the source integer, can be a register number, an immediate value or a memory address
            destination (int): the destination register
        """
        source_value = self.__get_source_value(source_type, source)
        res = self.registers[destination] & source_value
        self.registers[destination] = res
        self.flags.reset()
        self.flags.set_z(res == 0)
        self.flags.set_n(res >> 15)

    def i_or(self, source_type: MemoryType, source: int, destination: int):
        """Makes the logical or between the source and the destination and stores the result in the destination

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address
            destination (int): The destination register
        """
        source_value = self.__get_source_value(source_type, source)
        res = self.registers[destination] | source_value
        self.registers[destination] = res
        self.flags.reset()
        self.flags.set_z(res == 0)
        self.flags.set_n(res >> 15)

    def xor(self, source_type: MemoryType, source: int, destination: int):
        """Makes the logical xor between the source and the destination and stores the result in the destination

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address
            destination (int): The destination register
        """
        source_value = self.__get_source_value(source_type, source)
        res = self.registers[destination] ^ source_value
        self.registers[destination] = res
        self.flags.reset()
        self.flags.set_n(res >> 15)
        self.flags.set_z(res == 0)

    def rte(self):
        """Return from an interruption"""
        r0 = self.registers[0]
        self.pop(MemoryType.register, 0)
        self.flags.reset()
        flags = self.registers[0]
        self.registers[0] = r0
        self.flags.value = flags
        self.pop(MemoryType.register, PC)

    def trap(self, source_type: MemoryType, source: int):
        """Trigger an interruption

        Args:
            source_type (MemoryType): The memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address.
            Represent the address of the processor which will handle the interruption
        """
        address = self.__get_source_value(source_type, source)
        cpu = self.__get_relative_cpu(address)
        cpu.interruption(TRAP)

    def __get_source_value(self, source_type: MemoryType, source: int, special_move=False) -> int:
        """Retrieve the value of the source acording to the momory type

        Args:
            source_type (MemoryType): the memory type of the source
            source (int): The source integer, can be a register number, an immediate value or a memory address
            special_move (bool, optional): whenever it is a move.l or a move.h. Defaults to False.

        Raises:
            Exception: If one of the memory type is not supported

        Returns:
            int: The value of the source
        """
        match source_type:
            case MemoryType.register:
                return self.registers[source]
            case MemoryType.pre_decremented_register:
                self.registers[source] -= 1 if special_move else 2
                return self.memory[self.registers[source]]
            case MemoryType.inderect_addressing:
                return self.memory[self.registers[source]]
            case MemoryType.post_incremented_register:
                value = self.memory[self.registers[source]]
                self.registers[source] += 1 if special_move else 2
                return value
            case MemoryType.immediate_value:
                return source
            case MemoryType.address:
                return self.memory[source]
            case _:
                raise Exception("Invalid source type")


if __name__ == "__main__":
    memory = bytearray(256)
    instruction = 0x08  # and
    memory_type = 0b000  # Rn
    destination = 0b010  # R2
    source = 0b001  # R1
    byte1 = instruction << 3 | destination
    memory[0] = byte1
    byte2 = memory_type << 5 | source
    memory[1] = byte2
    cpu = CPU(memory)

    cpu.registers[1] = 0b11
    cpu.registers[2] = 0b10
    cpu.execute()
    print(bin(cpu.registers[2]))
