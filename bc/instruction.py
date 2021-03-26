import copy

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Union


class Op(Enum):
    # Memory ops
    LOAD    = 0x00
    STORE   = 0x01
    GLOAD   = 0x02
    GSTORE  = 0x03
    # Arithmetic ops
    CONST   = 0x04
    ADD     = 0x05
    SUB     = 0x06
    MUL     = 0x07
    DIV     = 0x08
    MOD     = 0x09
    # Logic ops
    AND     = 0x0A
    OR      = 0x0B
    LT      = 0x0C
    LE      = 0x0D
    GT      = 0x0E
    GE      = 0x0F
    EQ      = 0x10
    NE      = 0x11
    # Jumps
    JMP     = 0x12
    JZ      = 0x13
    JNZ     = 0x14
    CALL    = 0x15
    SYSCALL = 0x16
    RET     = 0x17
    # Function boundaries
    ENTER   = 0x18
    LEAVE   = 0x19

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

    def bytecode(self):
        opcode = self.op.value
        if self.op is Op.ENTER:
            _, n_args, n_locals = self.args
            arg = n_locals << 32 | n_args
        elif len(self.args) != 0:
            assert len(self.args) == 1
            arg = self.args[0]
        else:
            arg = 0
        pad = b'\0' * 7
        return int.to_bytes(opcode, 1, 'little') + pad  + int.to_bytes(arg, 8, 'little')


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

    def serialize(self):
        magic = b'.noxbc--'
        entry = int.to_bytes(self.entry, 4, 'little')
        n_globals = int.to_bytes(len(self.globals), 4, 'little')
        program = magic + n_globals + entry
        for instruction in self.instructions:
            program += instruction.bytecode()
        return program

    def __str__(self):
        return '\n'.join(
            '    ' + str(i) if type(i) is Instruction else str(i) + ':'
            for i in self.source
        )
