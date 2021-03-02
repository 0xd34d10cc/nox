import os
import sys

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict

import bc
from bc import Op, Instruction, Label, Program


def try_find(xs, val):
    try:
        return xs.index(val)
    except ValueError:
        return None

class Reg(Enum):
    RAX = auto()
    RCX = auto()
    RDX = auto()
    RBX = auto()
    RSP = auto()
    RBP = auto()
    RSI = auto()
    RDI = auto()
    R8  = auto()
    R9  = auto()
    R10 = auto()
    R11 = auto()
    R12 = auto()
    R13 = auto()
    R14 = auto()
    R15 = auto()

    def __str__(self):
        return self.name.lower()

    def r8(self):
        s = str(self)
        if s[1].isdigit():
            return s + 'b'
        elif s[1] in 'abcd':
            return s[1] + 'l'
        else:
            return s[1:] + 'l'

word_size = 8

tmp_reg = Reg.R10

special_regs = [
    Reg.RAX, # return value, also used in idiv
    Reg.RDX, # used in idiv
    Reg.RBP, # base pointer
    Reg.RSP, # stack pointer
    tmp_reg
]

if os.name == 'nt':
    # win64 calling convention
    # see https://docs.microsoft.com/en-us/cpp/build/x64-calling-convention
    args_regs = [Reg.RCX, Reg.RDX, Reg.R8, Reg.R9]
    volatile_regs = [Reg.RAX] + args_regs + [Reg.R10, Reg.R11]
    # stack_regs = set()
    stack_regs = set(Reg) - set(args_regs) - set(special_regs) - set(volatile_regs)
else:
    assert False, 'Compiler does not support target {os.name}'

@dataclass
class StackLocation:
    offset: int

    def __str__(self):
        sign = '+' if self.offset >= 0 else '-'
        offset = abs(self.offset) * word_size
        return f'qword [{Reg.RBP}{sign}{offset}]'

@dataclass
class Fn:
    name: str
    args: list
    locals: list
    returns_value: bool
    start: int
    end: int

syscalls = {
    0: Fn('sys_read',  args=[],       locals=set(), returns_value=True,  start=None, end=None),
    1: Fn('sys_write', args=['num'],  locals=set(), returns_value=False, start=None, end=None),
    2: Fn('sys_exit',  args=['code'], locals=set(), returns_value=False, start=None, end=None)
}

base_listing = 'global main\n\n' + \
                'extern sys_setup\n' + \
    '\n'.join(f'extern {syscall.name}' for syscall in syscalls.values()) + '\n\n'


def binop(op):
    def handler(self):
        r = self.pop()
        l = self.pop()
        if type(l) is not Reg:
            self.asm(f'mov {tmp_reg}, {l}')
        self.asm(f'{op} {l if type(l) is Reg else tmp_reg}, {r}')
        if type(l) is not Reg:
            self.asm(f'mov {l}, {tmp_reg}')
        self.push(l)

    return handler

def divmod_op(result):
    def handler(self):
        r = self.pop()
        l = self.pop()
        self.asm(f'mov {Reg.RAX}, {l}')
        self.asm(f'cqo')
        self.asm(f'idiv {r}')
        self.asm(f'mov {l}, {result}')
        self.push(l)
    return handler

def comparison(op):
    def handler(self):
        r = self.pop()
        l = self.pop()
        dst = l
        if type(l) is not Reg:
            self.asm(f'mov {tmp_reg}, {l}')
            dst = tmp_reg

        self.asm(f'cmp {dst}, {r}')
        self.asm(f'{op} {dst.r8()}')
        self.asm(f'and {dst}, 0x1')
        if type(l) is not Reg:
            self.asm(f'mov {l}, {tmp_reg}')
        self.push(l)
    return handler

def cjump(op):
    def handler(self, label):
        val = self.pop()
        if type(val) is not Reg:
            self.asm(f'mov {tmp_reg}, {val}')
            val = tmp_reg
        self.asm(f'test {val}, {val}')
        self.asm(f'{op} {label}')
    return handler

def logical_binop(op):
    def handler(self):
        r = self.pop()
        l = self.pop()
        for val in r, l:
            if type(val) is not Reg:
                self.asm(f'mov {tmp_reg}, {val}')
                reg = tmp_reg
            else:
                reg = val
            self.asm(f'test {reg}, {reg}')
            self.asm(f'setne {reg.r8()}')
            if type(val) is not Reg:
                self.asm(f'mov {val}, {tmp_reg}')

        dst = l
        if type(l) is not Reg:
            dst = tmp_reg

        self.asm(f'{op} {dst}, {r}')
        self.asm(f'and {dst}, 0x1')
        if type(l) is not Reg:
            self.asm(f'mov {l}, {tmp_reg}')

        self.push(l)
    return handler

@dataclass
class Compiler:
    program: Program
    globals: set
    functions: Dict[str, Fn]
    max_stack_depth: int = field(default=None)
    current: str = field(default=None)

    regs: list = field(default_factory=lambda: sorted(stack_regs, key=lambda x: x.value, reverse=True))
    stack: list = field(default_factory=list)
    listing: str = field(default=base_listing)

    def compile(self):
        if len(self.globals):
            self.line('section .data')
            for var in self.globals:
                self.asm(f'{var:<8} dq 0')
            self.line('')

        fns = sorted(self.functions.values(), key=lambda f: f.start)
        self.line('section .text')
        for f in fns:
            self.compile_function(f)
        return self.listing

    def compile_function(self, fn):
        self.current = fn.name
        self.max_stack_depth = len(fn.locals)
        self.line(fn.name + ':')
        for i in range(fn.start, fn.end):
            instruction = self.program.source[i]
            if type(instruction) is Label:
                self.line(instruction.name + ':')
            else:
                assert type(instruction) is Instruction
                n = str(instruction.op)
                handler = getattr(self, n, None) or getattr(self, n + '_')
                handler(*instruction.args)

    def compile_call(self, fn):
        arg_regs_in_use = len(self.functions[self.current].args)
        n_args = len(fn.args)
        assert n_args <= len(args_regs), 'Too many args (pass through stack is not implemented yet)'

        regs_to_save = [r for r in self.stack[:-n_args] if type(r) is Reg] + args_regs[:arg_regs_in_use]
        for reg in regs_to_save:
            self.asm(f'push {reg}')

        args = [self.pop() for _ in range(n_args)]
        for dst, src in zip(args_regs, args):
            self.asm(f'mov {dst}, {src}')

        self.asm(f'call {fn.name}')
        if fn.returns_value:
            dst = self.allocate()
            self.asm(f'mov {dst}, {Reg.RAX}')

        for reg in reversed(regs_to_save):
            self.asm(f'pop {reg}')

    def call(self, label):
        self.compile_call(self.functions[label.name])

    def syscall(self, n):
        self.compile_call(syscalls[n])

    def enter(self, fn_tag, *args):
        fn = self.functions[self.current]
        if fn.name == 'main':
            # setup the runtime at the start of program
            self.asm('call sys_setup')

        # prologue
        self.asm(f'push {Reg.RBP}')
        self.asm(f'mov {Reg.RBP}, {Reg.RSP}')
        self.asm(f'sub {Reg.RSP}, {fn.name}_stackframe')

    def leave(self):
        fn = self.functions[self.current]
        n_locals = len(fn.locals)
        self.line(f'{fn.name}_epilogue:')
        self.asm(f'add {Reg.RSP}, {fn.name}_stackframe')
        self.asm(f'pop {Reg.RBP}')
        self.asm(f'ret')
        self.line(f'{fn.name}_stackframe EQU {self.max_stack_depth * word_size}')

    def load(self, var):
        loc = self.location(var)
        dst = self.allocate()
        if type(loc) is Reg or type(dst) is Reg:
            self.asm(f'mov {dst}, {loc}')
        else:
            self.asm(f'mov {tmp_reg}, {loc}')
            self.asm(f'mov {dst}, {tmp_reg}')

    def store(self, var):
        top = self.pop()
        loc = self.location(var)
        if type(loc) is Reg or type(top) is Reg:
            self.asm(f'mov {loc}, {top}')
        else:
            self.asm(f'mov {tmp_reg}, {top}')
            self.asm(f'mov {loc}, {tmp_reg}')

    def gload(self, var):
        dst = self.allocate()
        if type(dst) is Reg:
            self.asm(f'mov {dst}, [rel {var}]')
        else:
            self.asm(f'mov {tmp_reg}, [rel {var}]')
            self.asm(f'mov {dst}, {tmp_reg}')

    def gstore(self, var):
        top = self.pop()
        if type(top) is Reg:
            self.asm(f'mov [rel {var}], {top}')
        else:
            self.asm(f'mov {tmp_reg}, {top}')
            self.asm(f'mov [rel {var}], {tmp_reg}')

    def const(self, val):
        loc = self.allocate()
        self.asm(f'mov {loc}, {val}')

    add = binop('add')
    sub = binop('sub')
    mul = binop('imul')
    div = divmod_op(result=Reg.RAX)
    mod = divmod_op(result=Reg.RDX)

    and_ = logical_binop('and')
    or_  = logical_binop('or')

    lt = comparison('setl')
    le = comparison('setle')
    gt = comparison('setg')
    ge = comparison('setge')
    eq = comparison('sete')
    ne = comparison('setne')

    def jmp(self, label):
        self.asm(f'jmp {label}')

    jz  = cjump('jz')
    jnz = cjump('jnz')

    def ret(self):
        fn = self.functions[self.current]
        if fn.returns_value:
            ret = self.pop()
            self.asm(f'mov {Reg.RAX}, {ret}')
        self.asm(f'jmp {fn.name}_epilogue')

    def allocate(self):
        if self.regs:
            operand = self.regs.pop()
        else:
            if self.stack and type(self.stack[-1]) is StackLocation:
                offset = self.stack[-1].offset
            else:
                offset = -1 - len(self.functions[self.current].locals)
            offset -= 1
            self.max_stack_depth = max(abs(offset), self.max_stack_depth)
            operand = StackLocation(offset)

        self.push(operand)
        return operand

    def push(self, operand):
        if type(operand) is Reg:
            assert operand in stack_regs
            i = try_find(self.regs, operand)
            if i is not None:
                self.regs.pop(i)
        self.stack.append(operand)

    def pop(self):
        operand = self.stack.pop()
        if type(operand) is Reg:
            assert operand in stack_regs
            self.regs.append(operand)
        return operand

    def line(self, line):
        self.listing += line + '\n'

    def asm(self, line):
        instruction, *ops = line.split()
        self.line(f'    {instruction:<7} {" ".join(ops)}')

    def location(self, var):
        fn = self.functions[self.current]
        i = try_find(fn.args, var)
        if i is not None:
            if i < len(args_regs):
                return args_regs[i]
            else:
                offset = i - len(args_regs)
                # TODO: figure out what offset we should actually use
                return StackLocation(i + 2) # 1 for rbp, 1 for rip

        i = try_find(fn.locals, var)
        if i is not None:
            return StackLocation(-1 - i)

        assert False, f'Unknown variable: {var}'


def functions(program):
    funcs = {}
    name = None
    args = None
    locals = None
    returns_value = None
    start = None
    for i, instruction in enumerate(program.source):
        if type(instruction) is Label:
            continue
        assert type(instruction) is Instruction

        if instruction.op is Op.ENTER:
            name = program.source[i - 1].name
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

def list_globals(program):
    globals = set()
    for instruction in program.source:
        if type(instruction) is Label:
            continue
        if instruction.op in (Op.GLOAD, Op.GSTORE):
            globals.add(instruction.args[0])
    return globals

def compile(program):
    compiler = Compiler(program, list_globals(program), functions(program))
    return compiler.compile()


if __name__ == '__main__':
    print(compile(
        bc.parse(
            open(sys.argv[1], 'rt', encoding='utf-8').read()
        )
    ))