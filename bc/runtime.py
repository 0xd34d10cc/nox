import operator
import sys

from typing import List, Dict
from dataclasses import dataclass
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

# name -> n_args
BUILTINS = {
    'read': 0,
    'write': 1
}

@dataclass
class State:
    __slots__ = ('ip', 'stack', 'memory')

    ip: int
    stack: List[int]
    memory: Dict[str, int]

    def load(self, var):
        assert type(var) is str
        val = self.memory[var]
        self.stack.append(val)
        self.ip += 1

    def store(self, var):
        assert type(var) is str
        val = self.stack.pop()
        self.memory[var] = val
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
        assert False, 'Not implemented'

    def call_native(self, target):
        n_args = BUILTINS[target.name]
        args = tuple(self.stack.pop() for _ in range(n_args))
        handler = getattr(self, target.name, None) or getattr(self, target.name + '_')
        handler(*args)
        self.ip += 1

    # "native" functions
    def read(self):
        value = input('I: ') if sys.stdin.isatty() else input()
        self.stack.append(int(value))

    def write(self, value):
        if sys.stdout.isatty():
            print(f'O: {value}')
        else:
            print(value)

def getop(op):
    op = str(op).lower()
    return getattr(State, op, None) or getattr(State, op + '_')

HANDLERS = {op: getop(op) for op in Op}

def execute(state, program, handlers=HANDLERS):
    while state.ip < len(program.instructions):
        instruction = program.instructions[state.ip]
        handlers[instruction.op](state, *instruction.args)