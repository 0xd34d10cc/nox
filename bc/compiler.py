from lark import Token, Tree
from .instruction import Instruction, Op

OPS = {
    'ADD': Op.ADD,
    'SUB': Op.SUB,
    'MUL': Op.MUL,
    'DIV': Op.DIV
}

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
    assert ast.data == 'expr' or ast.data == 'term'
    if len(ast.children) % 3 == 1:
        raise Exception(f'Invalid binop tree: {ast}')

    i = 0
    while i + 3 <= len(ast.children):
        l, op, r = ast.children[i:i+3]
        compile_into(instructions, l)
        compile_into(instructions, r)
        instructions.append(Instruction(OPS[op.type], ()))
        i += 3

    if len(ast.children) != i:
        op, r = ast.children[i:i+2]
        compile_into(instructions, r)
        instructions.append(Instruction(OPS[op.type], ()))

def compile(ast):
    instructions = []
    assert ast.data == 'program'
    for statement in ast.children:
        compile_into(instructions, statement)
    return instructions
