from lark import Token, Tree
from .instruction import Program, Instruction, Op, Label


def compile_into(instructions, ast):
    # Leaf expression
    if type(ast) is Token:
        token = ast

        if token.type == 'SIGNED_INT':
            val = int(token.value)
            instructions.append(Instruction(Op.CONST, (val,)))
            return

        if token.type == 'VAR':
            var = token.value
            instructions.append(Instruction(Op.LOAD, (var,)))
            return

        raise Exception(f'Unexpected token: {token}')

    # statement
    assert type(ast) is Tree
    if ast.data == 'block':
        for statement in ast.children:
            compile_into(instructions, statement)
        return

    if ast.data == 'assign':
        var, op, expr = ast.children
        compile_into(instructions, expr)
        instructions.append(Instruction(Op.STORE, (var.value,)))
        return

    if ast.data == 'if_else':
        condition, if_true = ast.children
        compile_into(instructions, condition)
        end = Label.gen("if_end")
        instructions.append(Instruction(Op.JZ, (end,)))
        compile_into(instructions, if_true)
        instructions.append(end)
        return

    if ast.data == 'while':
        condition, body = ast.children
        cond_start = Label.gen('while_cond')
        while_body = Label.gen('while_body')
        instructions.append(Instruction(Op.JMP, (cond_start,)))
        instructions.append(while_body)
        compile_into(instructions, body)
        instructions.append(cond_start)
        compile_into(instructions, condition)
        instructions.append(Instruction(Op.JNZ, (while_body,)))
        return

    # non-leaf expression (i.e. binary operation)
    assert ast.data in ('disj', 'conj', 'cmp', 'sum', 'product'), ast.data
    assert len(ast.children) % 3 != 1, f'Invalid binop tree: {ast}'

    i = 0
    while i + 3 <= len(ast.children):
        l, op, r = ast.children[i:i+3]
        compile_into(instructions, l)
        compile_into(instructions, r)
        op = getattr(Op, op.type)
        instructions.append(Instruction(op, ()))
        i += 3

    if len(ast.children) != i:
        op, r = ast.children[i:i+2]
        compile_into(instructions, r)
        op = getattr(Op, op.type)
        instructions.append(Instruction(op, ()))

def compile(ast):
    instructions = []
    assert ast.data == 'block'
    for statement in ast.children:
        compile_into(instructions, statement)
    return Program.build(instructions)
