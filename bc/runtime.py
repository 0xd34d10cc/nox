import operator
import sys

from typing import List

from . import syscall
from .instruction import Op

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

def sys_input(self):
    value = input('I: ') if sys.stdin.isatty() else input()
    self.stack.append(int(value))

def sys_print(self, value):
    if sys.stdout.isatty():
        print(f'O: {value}')
    else:
        print(value)

class ExitCode(Exception):
    def __init__(self, code):
        self.code = code

def sys_exit(self, value):
    raise ExitCode(value)

def sys_list(self):
    self.stack.append([])

def sys_list_get(self, l, i):
    self.stack.append(l[i])

def sys_list_set(self, l, i, v):
    l[i] = v

def sys_list_push(self, l, v):
    l.append(v)

def sys_list_len(self, l):
    self.stack.append(len(l))

def sys_list_clear(self, l):
    l.clear()

def sys_list_slice(self, l, left, right):
    if left == -1:
        left = None
    if right == -1:
        right = None
    self.stack.append(l[slice(left, right)])

_syscalls = {
    'exit': sys_exit,

    'list': sys_list,
    'list_get': sys_list_get,
    'list_set': sys_list_set,
    'push': sys_list_push,
    'len': sys_list_len,
    'clear': sys_list_clear,
    'slice': sys_list_slice,

    'input': sys_input,
    'print': sys_print
}

SYSCALLS = {}

for name, fn in _syscalls.items():
    n, s = syscall.by_name(name)
    SYSCALLS[n] = (fn, len(s.args))


class State:
    ip: int
    stack: List[int]
    callstack: List[int]
    globals: List[int]
    locals: List[List[int]]

    def __init__(self, program):
        self.ip = program.entry
        self.stack = []
        self.callstack = []
        self.globals = [0] * len(program.globals)
        self.locals = []

    def load(self, var_id):
        val = self.locals[-1][var_id]
        self.stack.append(val)
        self.ip += 1

    def store(self, var_id):
        val = self.stack.pop()
        self.locals[-1][var_id] = val
        self.ip += 1

    def gload(self, var_id: int):
        val = self.globals[var_id]
        self.stack.append(val)
        self.ip += 1

    def gstore(self, var_id):
        val = self.stack.pop()
        self.globals[var_id] = val
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
        self.callstack.append(self.ip + 1)
        self.ip = target

    def syscall(self, number):
        handler, n_args = SYSCALLS[number]
        args = tuple(self.stack.pop() for _ in range(n_args))
        handler(self, *args)
        self.ip += 1

    def ret(self):
        self.locals.pop()
        self.ip = self.callstack.pop()

    def enter(self, scope_type, n_args, n_locals):
        args = [
            self.stack.pop()
            for _ in range(n_args)
        ]
        self.locals.append(args + [0] * n_locals)
        self.ip += 1

    def leave(self):
        assert False, "Should be unreachable"

def getop(op):
    op = str(op)
    return getattr(State, op, None) or getattr(State, op + '_')

HANDLERS = {op: getop(op) for op in Op}

def execute(state, program, handlers=HANDLERS):
    state.ip = program.entry
    try:
        while True:
            instruction = program.instructions[state.ip]
            handlers[instruction.op](state, *instruction.args)
    except ExitCode as e:
        return e.code