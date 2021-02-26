import copy

from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Dict, Union


class Op(Enum):
    # Memory ops
    LOAD = auto()
    STORE = auto()
    GLOAD = auto()
    GSTORE = auto()
    # Arithmetic ops
    CONST = auto()
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    # Logic ops
    AND = auto()
    OR = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()
    EQ = auto()
    NE = auto()
    # Jumps
    JMP = auto()
    JZ = auto()
    JNZ = auto()
    CALL = auto()
    SYSCALL = auto()
    RET = auto()

    def __str__(self):
        return self.name.lower()

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
    __slots__ = ('source', 'instructions', 'entry')

    source: List[Union[Instruction, Label]]
    instructions: List[Instruction]
    entry: int

    def build(instructions, entrypoint='main'):
        source = copy.deepcopy(instructions)

        labels = {}
        for i, instruction in enumerate(instructions):
            if type(instruction) is Label:
                assert instruction.name not in labels, f'Label {instruction.name} defined twice'
                labels[instruction.name] = i - len(labels)

        instructions = [i for i in instructions if type(i) is not Label]
        for instruction in instructions:
            if instruction.op in (Op.JZ, Op.JNZ, Op.JMP, Op.CALL):
                assert len(instruction.args) == 1
                target = labels[instruction.args[0].name]
                instruction.args = (target,)

        entry = labels[entrypoint]
        return Program(source, instructions, entry)

    def __str__(self):
        return '\n'.join(
            '    ' + str(i) if type(i) is Instruction else str(i) + ':'
            for i in self.source
        )
