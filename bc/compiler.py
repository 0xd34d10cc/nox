from lark import Token, Tree
from .instruction import Instruction, Op

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
    if ast.data == 'assign':
        var, op, expr = ast.children
        compile_into(instructions, expr)
        instructions.append(Instruction(Op.STORE, (var.value,)))
        return

    # non-leaf expression (i.e. binary operation)
    assert ast.data in ('disj', 'conj', 'cmp', 'arithm', 'term')
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
    assert ast.data == 'program'
    for statement in ast.children:
        compile_into(instructions, statement)
    return instructions
