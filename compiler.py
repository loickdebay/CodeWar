import argparse
import pathlib

from data import INSTRUCTIONS, OPERANDS, OPERAND_TYPE
from cpu import MemoryType


def build_bin_instruction(name: str, args: list[str]) -> int:
    """Build an instruction in binary format from the instruction name and the operands

    Args:
        name (str): The name of the instruction
        args (list[str]): The operands

    Returns:
        int: 2 or 4 bytes representing the instruction
    """
    name = name.lower()
    for i, arg in enumerate(args):
        args[i] = arg.lower()
    if name.startswith("move"):
        return build_move_istruction_bin(name, args)
    instruction = get_instruction_bin(name)
    parameters = OPERANDS[name]
    match parameters:
        case 0:
            return build_zero_operand_instruction_bin(instruction)
        case 1:
            return build_one_operand_instruction_bin(instruction, args[0])
        case 2:
            return build_two_operand_instruction_bin(instruction, args[0], args[1])


def build_zero_operand_instruction_bin(instruction_bin: int) -> int:
    """Build a 2 bytes instruction with no operand

    Args:
        instruction_bin (int): the binary value of the instruction

    Returns:
        int: 2 bytes representing the instruction
    """
    return instruction_bin << 11
    return [byte >> 8, byte & 0xFF]


def build_one_operand_instruction_bin(instruction_bin: int, arg: str) -> int:
    """Build a 2 bytes instruction with one operand

    Args:
        instruction_bin (int): the binary value of the instruction
        arg (str): the operand

    Returns:
        int: 2 bytes representing the instruction
    """
    byte = instruction_bin << 11
    arg_type_bin = get_arg_type_bin(arg[0])
    if arg_type_bin == -1:
        arg_type_bin = get_inderect_arg_type_bin(arg)
    arg_type_bin <<= 8
    byte |= arg_type_bin
    byte |= get_arg_bin(arg)
    return [byte >> 8, byte & 0xFF]


def build_two_operand_instruction_bin(instruction_bin: int, source: str, destination: str) -> int:
    """Build a 2 bytes instruction with two operands

    Args:
        instruction_bin (int): the binary value of the instruction
        source (str): the first operand
        destination (str): the second operand, must be a register

    Returns:
        int: 2 bytes representing the instruction
    """
    byte = instruction_bin << 11
    destination = get_arg_bin(destination)
    byte |= (destination << 8)
    source_type_bin = get_arg_type_bin(source[0])
    if source_type_bin == -1:
        source_type_bin = get_inderect_arg_type_bin(source)
    byte |= (source_type_bin << 5)
    source_value = get_arg_bin(source)
    byte |= source_value
    return [byte >> 8, byte & 0xFF]


def build_move_istruction_bin(instruction_name: str, args: str) -> int:
    """Build a 4 bytes move instruction

    Args:
        instruction_name (str): the name of the instruction
        args (str): the operands

    Returns:
        int: 4 bytes representing the instruction
    """
    instruction = instruction_name.split(".")
    instruction_bin = get_instruction_bin(instruction[0])
    byte = instruction_bin << 27
    move_flags = get_special_move_bin(instruction[1])
    byte |= (move_flags << 25)

    source = args[0]
    destination = args[1]
    source_type_bin = get_arg_type_bin(source[0])
    if source_type_bin == -1:
        source_type_bin = get_inderect_arg_type_bin(source)
    byte |= (source_type_bin << 22)
    destination_type_bin = get_arg_type_bin(destination[0])
    if destination_type_bin == -1:
        destination_type_bin = get_inderect_arg_type_bin(destination)
    byte |= (destination_type_bin << 19)
    source_type = MemoryType(source_type_bin)
    if source_type == MemoryType.immediate_value or source_type == MemoryType.address:
        destination_bin = get_arg_bin(destination)
        byte |= (destination_bin << 16)
        source_bin = get_arg_bin(source)
        byte |= source_bin
    else:
        source_bin = get_arg_bin(source)
        byte |= (source_bin << 16)
        destination_bin = get_arg_bin(destination)
        byte |= destination_bin
    return byte


def get_special_move_bin(special: str) -> int:
    """Return the bits corresponding to the special move

    Args:
        special (str): the second part of the move instruction name (ie. "h" or "l")

    Returns:
        int: the binary value of the special move or 0b11 if no special move
    """
    if special == "h":
        return 0b10
    if special == "l":
        return 0b01
    return 0b11


def get_instruction_bin(instruction_name: str) -> int:
    return INSTRUCTIONS[instruction_name]


def get_arg_bin(arg: str) -> int:
    """Return the value of the operand ie the register number or the value of the constant or address

    Args:
        arg (str): the operand

    Returns:
        int: the binary value of the operand
    """
    match arg[0]:
        case "r":
            return int(arg[1], 16)
        case "-":
            return int(arg[3], 16)
        case "#":
            return int(arg[1:], 16)
        case "@":
            return int(arg[1:], 16)
        case "(":
            return int(arg[2], 16)


def get_inderect_arg_type_bin(arg: str) -> int:
    """If the argument is and inderect addressing or post increment, return the binary value of the argument type

    Args:
        arg (str): the operand

    Returns:
        int: the binary value of the argument type
    """
    if arg.endswith("+"):
        return 0b011
    return 0b010


def get_arg_type_bin(first_char: str) -> int:
    """Fetch the binary value of the operand type

    Args:
        first_char (str): first character of the operand

    Returns:
        int: the binary value of the operand type or -1 if the operand is an inderect addressing or post increment
    """
    binary = OPERAND_TYPE[first_char]
    return binary


parser = argparse.ArgumentParser("compiler", description="compile an assembly file for codewar. All numbers are considered hex")
parser.add_argument("file", help="A path to the assembly file to compile. No function authorized, only strict assembly instructions. Empty lines and comments starting with # authorized. Inline comments are not supported", type=str)
args = parser.parse_args()
file_path: pathlib.Path = pathlib.Path(args.file)

file = open(file_path, mode="r", encoding="UTF-8")

data = []

for line in file.readlines():
    if line == "" or line.startswith("#"):
        continue
    instruction = line.split(" ")
    name = instruction[0]
    args = instruction[1:]
    data.append(build_bin_instruction(name, args))

new_data = []
for byte_list in data:
    for byte in byte_list:
        new_data.append(byte)
to_write = bytes(new_data)

destination = open(file.name + ".bin", mode="wb")
destination.write(to_write)

destination.close()
file.close()
