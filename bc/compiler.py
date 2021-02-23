from itertools import islice
from dataclasses import dataclass
from lark import Token, Tree
from .instruction import Program, Instruction, Op, Label

@dataclass
class Compiler:
    instructions: list

    def push(self, instruction):
        self.instructions.append(instruction)

    def push_op(self, op, *args):
        self.push(Instruction(op, *args))

    def compile(self, ast):
        # Leaf expression
        if type(ast) is Token:
            token = ast

            if token.type == 'SIGNED_INT':
                val = int(token.value)
                self.push_op(Op.CONST, val)
                return

            if token.type == 'VAR':
                var = token.value
                self.push_op(Op.LOAD, var)
                return

            assert False, f'Unexpected token: {token}'

        assert type(ast) is Tree
        handler = getattr(self, ast.data, None) or getattr(self, ast.data + '_')
        handler(ast)

    def block(self, ast):
        for statement in ast.children:
            self.compile(statement)

    def assign(self, ast):
        var, op, expr = ast.children
        self.compile(expr)
        self.push_op(Op.STORE, var.value)

    def if_else(self, ast):
        condition, if_true, *if_false = ast.children
        has_else = len(ast.children) > 2
        self.compile(condition)
        false = Label.gen('if_false')
        end = Label.gen('if_end')
        self.push_op(Op.JZ, false if len(if_false) else end)
        self.compile(if_true)
        if len(if_false):
            self.push_op(Op.JMP, end)
            self.push(false)
            self.compile(*if_false)

        self.push(end)

    def while_(self, ast):
        condition, body = ast.children
        cond_start = Label.gen('while_cond')
        while_body = Label.gen('while_body')
        self.push_op(Op.JMP, cond_start)
        self.push(while_body)
        self.compile(body)
        self.push(cond_start)
        self.compile(condition)
        self.push_op(Op.JNZ, while_body)

    def call_expr(self, ast):
        name = ast.children[0]
        # TODO: check that function returns value
        assert name in ('read', 'write')

        if name == 'read':
            assert len(ast.children) == 1, 'read() builtin function expects no arguments'
        elif name == 'write':
            assert len(ast.children) == 2, 'write() builtin function expects a single argument'

        for arg in islice(reversed(ast.children), len(ast.children) - 1):
            self.compile(arg)

        self.push_op(Op.CALL_NATIVE, Label(name))

    def call_statement(self, ast):
        # TODO: check that function doesn't return values
        self.call_expr(ast)

    def binop(self, ast):
        assert len(ast.children) % 2 != 0, f'Invalid binop tree: {ast}'
        l = ast.children[0]
        self.compile(l)

        i = 1
        while i + 2 <= len(ast.children):
            op, r = ast.children[i:i+2]
            self.compile(r)
            op = getattr(Op, op.type)
            self.push_op(op)
            i += 2

    disj = binop
    conj = binop
    cmp = binop
    sum = binop
    product = binop


def compile(ast):
    compiler = Compiler(instructions=[])
    compiler.compile(ast)
    return Program.build(compiler.instructions)
