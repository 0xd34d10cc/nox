import operator

from dataclasses import dataclass
from .instruction import Instruction, Op

def binop(op):
    def handler(self):
        r = self.stack.pop()
        l = self.stack.pop()
        result = op(l, r)
        self.stack.append(result)
    return handler

def and_(l ,r):
    return operator.truth(l and r)

def or_(l, r):
    return operator.truth(l or r)

@dataclass
class State:
    stack: list
    memory: dict

    def load(self, var):
        assert type(var) is str
        val = self.memory[var]
        self.stack.append(val)

    def store(self, var):
        assert type(var) is str
        val = self.stack.pop()
        self.memory[var] = val

    def const(self, val):
        assert type(val) is int
        self.stack.append(val)

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

def getop(op):
    op = str(op).lower()
    return getattr(State, op, None) or getattr(State, op + '_')

HANDLERS = {op: getop(op) for op in Op}

def execute(state, instructions, handlers=HANDLERS):
    for instruction in instructions:
        handlers[instruction.op](state, *instruction.args)
