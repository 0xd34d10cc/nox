import operator

from typing import List, Dict
from dataclasses import dataclass
from .instruction import Instruction, Op, Program

def binop(op):
    def handler(self):
        r = self.stack.pop()
        l = self.stack.pop()
        result = op(l, r)
        self.stack.append(result)
        self.ip += 1
    return handler

def and_(l, r):
    return operator.truth(l and r)

def or_(l, r):
    return operator.truth(l or r)

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

def getop(op):
    op = str(op).lower()
    return getattr(State, op, None) or getattr(State, op + '_')

HANDLERS = {op: getop(op) for op in Op}

def execute(state, program, handlers=HANDLERS):
    while state.ip < len(program.instructions):
        instruction = program.instructions[state.ip]
        handlers[instruction.op](state, *instruction.args)