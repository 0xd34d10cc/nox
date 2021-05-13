from ast import literal_eval
from dataclasses import dataclass, field
from lark import Tree

from . import syscall
from .instruction import Program, Instruction, Op, Label


@dataclass
class Compiler:
    instructions: list = field(default_factory=list)
    globals: set = field(default_factory=set)
    locals: list = field(default_factory=lambda: [set()])
    is_fn: bool = field(default=False)

    def push(self, instruction):
        self.instructions.append(instruction)

    def push_op(self, op, *args):
        self.push(Instruction(op, *args))

    def compile(self, ast):
        assert type(ast) is Tree, ast
        handler = getattr(self, ast.data, None) or getattr(self, ast.data + '_')
        handler(ast)

    def program(self, ast):
        main_marked = False
        for node in ast.children:
            if not main_marked and node.data not in ('global', 'function'):
                self.push(Label('main'))
                self.push_op(Op.ENTER, 'proc')
                main_marked = True
            self.compile(node)

        self.push_op(Op.CONST, 0)
        self.push_op(Op.SYSCALL, syscall.number_by_name('exit'))
        self.push_op(Op.LEAVE)

    def global_(self, ast):
        for var in ast.children:
            self.globals.add(var.value)

    def function(self, ast):
        if len(ast.children) == 3:
            name, args, body = ast.children
            ret = None
        elif len(ast.children) == 4:
            name, args, ret, body = ast.children
        else:
            assert False, len(ast)

        self.push(Label(name.value))
        args = [arg.value for arg in args.children]
        self.locals.append(set(args))
        self.push_op(Op.ENTER, "fn" if ret else "proc", *args)
        self.is_fn = ret is not None
        self.compile(body)
        if not ret:
            self.push_op(Op.RET)
        self.push_op(Op.LEAVE)
        self.locals.pop()

    def block(self, ast):
        for statement in ast.children:
            self.compile(statement)

    def assign(self, ast):
        var, op, expr = ast.children
        self.compile(expr)
        if var.value in self.locals[-1]:
            op = Op.STORE
        elif var.value in self.globals:
            op = Op.GSTORE
        else:
            # new local variable
            op = Op.STORE
            self.locals[-1].add(var.value)

        self.push_op(op, var.value)

    def assign_at(self, ast):
        location, idx, op, expr = ast.children
        self.compile(expr)
        self.compile(idx)
        self.compile(location)
        self.push_op(Op.SYSCALL, syscall.number_by_name('list_set'))

    def list_at(self, ast):
        location, idx = ast.children
        self.compile(idx)
        self.compile(location)
        self.push_op(Op.SYSCALL, syscall.number_by_name('list_get'))

    def var_expr(self, ast):
        var = ast.children[0].value
        if var in self.locals[-1]:
            op = Op.LOAD
        elif var in self.globals:
            op = Op.GLOAD
        else:
            assert False, f'Undefined "{var.value}" at {var.line}:{var.column}'
        self.push_op(op, var)

    def int_lit(self, ast):
        val = int(ast.children[0].value)
        self.push_op(Op.CONST, val)

    def char_lit(self, ast):
        val = ord(ast.children[0].value)
        self.push_op(Op.CONST, val)

    def list_lit(self, ast):
        self.push_op(Op.SYSCALL, syscall.number_by_name('list'))
        self.push_op(Op.STORE, '__list_lit')
        values = ast.children
        for val in values:
            self.compile(val)
            self.push_op(Op.LOAD, '__list_lit')
            self.push_op(Op.SYSCALL, syscall.number_by_name('push'))
        self.push_op(Op.LOAD, '__list_lit')

    def str_lit(self, ast):
        self.push_op(Op.SYSCALL, syscall.number_by_name('list'))
        self.push_op(Op.STORE, '__str_lit')
        assert len(ast.children) == 1
        for c in literal_eval(ast.children[0]):
            self.push_op(Op.CONST, ord(c))
            self.push_op(Op.LOAD, '__str_lit')
            self.push_op(Op.SYSCALL, syscall.number_by_name('push'))
        self.push_op(Op.LOAD, '__str_lit')

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

    def return_(self, ast):
        assert len(ast.children) in (0, 1)
        if len(ast.children):
            assert self.is_fn, f'Attempt to return value from procedure at {ast.line}:{ast.column}'
            ret = ast.children[0]
            self.compile(ret)
        else:
            assert not self.is_fn, f'No return value in function at {ast.line}:{ast.column}'
        self.push_op(Op.RET)

    def pass_(self, ast):
        # compiles to nothing
        pass

    def call(self, ast):
        name, *args = ast.children
        for arg in reversed(args):
            self.compile(arg)

        number = syscall.number_by_name(name.value)
        if number is not None:
            self.push_op(Op.SYSCALL, number)
        else:
            self.push_op(Op.CALL, Label(name.value))

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
    compiler = Compiler()
    compiler.compile(ast)
    return Program.build(compiler.instructions)
