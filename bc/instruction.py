from enum import Enum
from dataclasses import dataclass
from typing import NewType


class Op(Enum):
    # Memory ops
    LOAD = 1
    STORE = 2
    # Arithmetic ops
    CONST = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7
    # Logic ops
    AND = 8
    OR = 9
    LT = 10
    LE = 11
    GT = 12
    GE = 13
    EQ = 14
    NE = 15
    # Jumps
    # TODO
    # JMP = 16
    # JZ = 17
    # JNZ = 18

    def __str__(self):
        return self.name

Label = NewType('Label', str)

@dataclass
class Instruction:
    op: Op
    args: tuple

    def __str__(self):
        return f'{self.op} {",".join(str(arg) for arg in self.args)}'