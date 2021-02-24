from itertools import islice
from dataclasses import dataclass
from lark import Token, Tree
from .instruction import Program, Instruction, Op, Label


# name -> n_args
NATIVE_FUNCTIONS = {
    'read',
    'write'
}

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

    program = block

    def assign(self, ast):
        var, op, expr = ast.children
        self.compile(expr)
        self.push_op(Op.STORE, var.value)

    def if_else(self, ast):
        condition, if_true, *if_false = ast.children
        self.compile(condition)
        false = Label.gen('if_false')
        end = Label.gen('if_end')
        self.push_op(Op.JZ, false if len(if_false) else end)
        self.compile(if_true)

        if len(if_false):
            self.push_op(Op.JMP, end)

        i = 0
        while i + 2 < len(if_false):
            condition, body = if_false[i:i+2]
            self.push(false)
            self.compile(condition)
            false = Label.gen('if_false')
            self.push_op(Op.JZ, false)
            self.compile(body)
            self.push_op(Op.JMP, end)
            i += 2

        if i != len(if_false):
            self.push(false)
            self.compile(if_false[-1])

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

    def do_while(self, ast):
        body, condition = ast.children
        start = Label.gen('do_while')
        self.push(start)
        self.compile(body)
        self.compile(condition)
        self.push_op(Op.JNZ, start)

    def for_(self, ast):
        initialization, condition, step, body = ast.children
        for_cond = Label.gen('for_cond')
        for_body = Label.gen('for_body')
        self.compile(initialization)
        self.push_op(Op.JMP, for_cond)
        self.push(for_body)
        self.compile(body)
        self.compile(step)
        self.push(for_cond)
        self.compile(condition)
        self.push_op(Op.JNZ, for_body)


    def compile_native(self, ast):
        for arg in islice(reversed(ast.children), len(ast.children) - 1):
            self.compile(arg)

        self.push_op(Op.CALL_NATIVE, Label(ast.children[0]))

    def compile_call(self, ast):
        if ast.children[0] in NATIVE_FUNCTIONS:
            self.compile_native(ast)
            return

        assert False, 'Not implemented'

    call_expr = compile_call
    call_statement = compile_call

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
