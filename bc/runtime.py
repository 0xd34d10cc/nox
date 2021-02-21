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

@dataclass
class State:
    stack: list
    memory: dict

    def const(self, val):
        assert type(val) is int
        self.stack.append(val)

    def load(self, var):
        assert type(var) is str
        val = self.memory[var]
        self.stack.append(val)

    def store(self, var):
        assert type(var) is str
        val = self.stack.pop()
        self.memory[var] = val

    add = binop(operator.add)
    sub = binop(operator.sub)
    mul = binop(operator.mul)
    div = binop(operator.truediv)

HANDLERS = {
    Op.CONST: State.const,
    Op.LOAD:  State.load,
    Op.STORE: State.store,
    Op.ADD:   State.add,
    Op.SUB:   State.sub,
    Op.MUL:   State.mul,
    Op.DIV:   State.div
}

assert len(HANDLERS) == len(Op)

def execute(state, instructions):
    for instruction in instructions:
        HANDLERS[instruction.op](state, *instruction.args)
