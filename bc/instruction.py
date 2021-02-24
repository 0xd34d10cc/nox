import copy

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Union


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
    MOD = 8
    # Logic ops
    AND = 9
    OR = 10
    LT = 11
    LE = 12
    GT = 13
    GE = 14
    EQ = 15
    NE = 16
    # Jumps
    JMP = 17
    JZ = 18
    JNZ = 19
    CALL = 20
    CALL_NATIVE = 21

    def __str__(self):
        return self.name

@dataclass
class Label:
    __slots__ = ('name')

    name: str
    ID = 0

    def gen(name):
        n = f'{name}_{Label.ID}'
        Label.ID += 1
        return Label(n)

    def __str__(self):
        return self.name

@dataclass
class Instruction:
    __slots__ = ('op', 'args')

    op: Op
    args: tuple

    def __init__(self, op, *args):
        self.op = op
        self.args = args

    def __str__(self):
        return f'{self.op} {",".join(str(arg) for arg in self.args)}'

@dataclass
class Program:
    __slots__ = ('source', 'instructions')

    source: List[Union[Instruction, Label]]
    instructions: List[Instruction]

    def build(instructions):
        source = copy.deepcopy(instructions)

        labels = {}
        for i, instruction in enumerate(instructions):
            if type(instruction) is Label:
                labels[instruction.name] = i - len(labels)

        instructions = [i for i in instructions if type(i) is not Label]
        for instruction in instructions:
            if instruction.op in (Op.JZ, Op.JNZ, Op.JMP):
                assert len(instruction.args) == 1
                target = labels[instruction.args[0].name]
                instruction.args = (target,)

        return Program(source, instructions)

    def __str__(self):
        return '\n'.join(
            '    ' + str(i) if type(i) is Instruction else str(i) + ':'
            for i in self.source
        )