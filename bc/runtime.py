import operator
import sys

from typing import List, Dict
from dataclasses import dataclass, field
from .instruction import Instruction, Op

def binop(op):
    def handler(self):
        r = self.stack.pop()
        l = self.stack.pop()
        result = op(l, r)
        self.stack.append(int(result))
        self.ip += 1
    return handler

def and_(l, r):
    return operator.truth(l and r)

def or_(l, r):
    return operator.truth(l or r)

SYSCALL_ARGS = [
    0, # sys_read
    1  # sys_write
]

def sys_read(self):
    value = input('I: ') if sys.stdin.isatty() else input()
    self.stack.append(int(value))

def sys_write(self, value):
    if sys.stdout.isatty():
        print(f'O: {value}')
    else:
        print(value)

SYSCALLS = [
    sys_read,
    sys_write
]

@dataclass
class State:
    ip: int = field(default=0)
    stack: List[int] = field(default_factory=list)
    callstack: List[int] = field(default_factory=list)
    globals: Dict[str, int] = field(default_factory=dict)
    locals: List[Dict[str, int]] = field(default_factory=lambda: [{}])

    def load(self, var):
        assert type(var) is str
        val = self.locals[-1][var]
        self.stack.append(val)
        self.ip += 1

    def store(self, var):
        assert type(var) is str
        val = self.stack.pop()
        self.locals[-1][var] = val
        self.ip += 1

    def gload(self, var):
        assert type(var) is str
        val = self.globals[var]
        self.stack.append(val)
        self.ip += 1

    def gstore(self, var):
        assert type(var) is str
        val = self.stack.pop()
        self.globals[var] = val
        self.ip += 1

    def const(self, val):
        assert type(val) is int
        self.stack.append(val)
        self.ip += 1

    add = binop(operator.add)
    sub = binop(operator.sub)
    mul = binop(operator.mul)
    div = binop(operator.floordiv)
    mod = binop(operator.mod)

    and_ = binop(and_)
    or_  = binop(or_)
    lt   = binop(operator.lt)
    le   = binop(operator.le)
    gt   = binop(operator.gt)
    ge   = binop(operator.ge)
    eq   = binop(operator.eq)
    ne   = binop(operator.ne)

    def jmp(self, target):
        self.ip = target

    def jz(self, target):
        self.ip = target if not self.stack.pop() else self.ip + 1

    def jnz(self, target):
        self.ip = target if self.stack.pop() else self.ip + 1

    def call(self, target):
        self.locals.append({})
        self.callstack.append(self.ip + 1)
        self.ip = target

    def syscall(self, number):
        n_args = SYSCALL_ARGS[number]
        args = tuple(self.stack.pop() for _ in range(n_args))
        handler = SYSCALLS[number]
        handler(self, *args)
        self.ip += 1

    def ret(self):
        self.locals.pop()
        self.ip = self.callstack.pop()

def getop(op):
    op = str(op).lower()
    return getattr(State, op, None) or getattr(State, op + '_')

HANDLERS = {op: getop(op) for op in Op}

def execute(state, program, handlers=HANDLERS):
    state.ip = program.entry
    while state.ip < len(program.instructions):
        instruction = program.instructions[state.ip]
        handlers[instruction.op](state, *instruction.args)