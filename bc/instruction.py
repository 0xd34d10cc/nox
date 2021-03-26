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
    # Function boundaries
    ENTER = auto()
    LEAVE = auto()

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
        if self.op is Op.ENTER:
            return f'{self.op} {self.args[0]}({", ".join(str(arg) for arg in self.args[1:])})'
        return f'{self.op} {", ".join(str(arg) for arg in self.args)}'


@dataclass
class Fn:
    name: str
    args: list
    locals: list
    returns_value: bool
    start: int
    end: int


def list_functions(instructions):
    funcs = {}
    name = None
    args = None
    locals = None
    returns_value = None
    start = None
    for i, instruction in enumerate(instructions):
        if type(instruction) is Label:
            continue
        assert type(instruction) is Instruction

        if instruction.op is Op.ENTER:
            name = instructions[i - 1].name
            args = instruction.args[1:]
            locals = {}
            returns_value = instruction.args[0] == 'fn'
            start = i
        elif instruction.op is Op.STORE:
            n = instruction.args[0]
            if n not in locals:
                locals[n] = i
        elif instruction.op is Op.LEAVE:
            locals = sorted(locals, key=lambda n: locals[n])
            funcs[name] = Fn(name, args, locals, returns_value, start, end=i+1)
    return funcs


def list_globals(instructions):
    globals = set()
    for instruction in instructions:
        if type(instruction) is Label:
            continue
        if instruction.op in (Op.GLOAD, Op.GSTORE):
            globals.add(instruction.args[0])
    return sorted(globals)


def resolve_labels(instructions):
    labels = {}
    for i, instruction in enumerate(instructions):
        if type(instruction) is Label:
            assert instruction.name not in labels, f'Label {instruction.name} defined twice'
            labels[instruction.name] = i - len(labels)

    instructions = [i for i in instructions if type(i) is not Label]
    for instruction in instructions:
        if type(instruction) is Label:
            continue

        if instruction.op in (Op.JZ, Op.JNZ, Op.JMP, Op.CALL):
            assert len(instruction.args) == 1
            target = labels[instruction.args[0].name]
            instruction.args = (target,)
    return instructions, labels


def resolve_memops(instructions, fns, globals):
    for _, fn in fns.items():
        assert instructions[fn.start].op is Op.ENTER
        instructions[fn.start].args = (fn.returns_value, len(fn.args), len(fn.locals))
        # resolve locals locations
        for i in range(fn.start, fn.end):
            if type(instructions[i]) is Label:
                continue

            if instructions[i].op in (Op.LOAD, Op.STORE):
                name = instructions[i].args[0]
                try:
                    index = fn.args.index(name)
                except ValueError:
                    index = len(fn.args) + fn.locals.index(name)
                instructions[i].args = (index,)
            elif instructions[i].op in (Op.GLOAD, Op.GSTORE):
                name = instructions[i].args[0]
                index = globals.index(name)
                instructions[i].args = (index,)

@dataclass
class Program:
    __slots__ = ('source', 'instructions', 'globals', 'functions', 'entry')

    source: List[Union[Instruction, Label]]
    instructions: List[Instruction]
    globals: list
    functions: Dict[str, Fn]
    entry: int

    def build(instructions, entrypoint='main'):
        source = copy.deepcopy(instructions)
        globals = list_globals(instructions)
        fns = list_functions(source)
        resolve_memops(instructions, fns, globals)
        instructions, labels = resolve_labels(instructions)
        entry = labels[entrypoint]
        return Program(source, instructions, globals, fns, entry)

    def __str__(self):
        return '\n'.join(
            '    ' + str(i) if type(i) is Instruction else str(i) + ':'
            for i in self.source
        )
