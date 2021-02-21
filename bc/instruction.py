from enum import Enum
from dataclasses import dataclass

class Op(Enum):
    CONST = 1
    LOAD = 2
    STORE = 3
    ADD = 4
    SUB = 5
    MUL = 6
    DIV = 7

    def __str__(self):
        return self.name

@dataclass
class Instruction:
    op: Op
    args: tuple

    def __str__(self):
        return f'{self.op} {",".join(str(arg) for arg in self.args)}'
