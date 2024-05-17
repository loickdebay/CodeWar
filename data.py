INSTRUCTIONS = {
    "move": 0x00,
    "push": 0x01,
    "pop": 0x02,
    "add": 0x03,
    "cmp": 0x04,
    "sub": 0x05,
    "lsl": 0x06,
    "lsr": 0x07,
    "and": 0x08,
    "or": 0x09,
    "xor": 0x0A,
    "not": 0x0B,
    "bcc": 0x0C,
    "bcs": 0x0d,
    "beq": 0x0e,
    "bne": 0x0f,
    "ble": 0x10,
    "bge": 0x11,
    "bra": 0x12,
    "bsr": 0x13,
    "jcc": 0x14,
    "jcs": 0x15,
    "jeq": 0x16,
    "jne": 0x17,
    "jle": 0x18,
    "jge": 0x19,
    "jmp": 0x1a,
    "jsr": 0x1b,
    "rts": 0x1c,
    "trap": 0x1d,
    "rte": 0x1e,
}

OPERANDS = {
    "move": 2,
    "push": 1,
    "pop": 1,
    "add": 2,
    "cmp": 2,
    "sub": 2,
    "lsl": 2,
    "lsr": 2,
    "and": 2,
    "or": 2,
    "xor": 2,
    "not": 1,
    "bcc": 1,
    "bcs": 1,
    "beq": 1,
    "bne": 1,
    "ble": 1,
    "bge": 1,
    "bra": 1,
    "bsr": 1,
    "jcc": 1,
    "jcs": 1,
    "jeq": 1,
    "jne": 1,
    "jle": 1,
    "jge": 1,
    "jmp": 1,
    "jsr": 1,
    "rts": 0,
    "trap": 1,
    "rte": 0,
}

OPERAND_TYPE = {
    "r": 0,
    "-": 1,
    "(": -1,
    "#": 0b100,
    "@": 0b101
    
}