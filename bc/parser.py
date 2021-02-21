from . import Op, Instruction
from lark import Lark, Transformer, v_args


bytecode_grammar = '''
    ?start: program

    program: instruction* -> program

    instruction: "CONST" num -> const
        | "LOAD" var         -> load
        | "STORE" var        -> store
        | "ADD"              -> add
        | "SUB"              -> sub
        | "MUL"              -> mul
        | "DIV"              -> div

    var: CNAME -> var
    num: SIGNED_INT -> number

    %import common.CNAME
    %import common.SIGNED_INT
    %import common.WS
    %ignore WS
'''

def make_handler(op):
    def handler(self, *args):
        return Instruction(op, args)
    return handler

@v_args(inline=True)
class BytecodeTransformer(Transformer):
    def program(self, *instructions):
        return list(instructions)

    number = int
    var    = str
    const  = make_handler(Op.CONST)
    load   = make_handler(Op.LOAD)
    store  = make_handler(Op.STORE)
    add    = make_handler(Op.ADD)
    sub    = make_handler(Op.SUB)
    mul    = make_handler(Op.MUL)
    div    = make_handler(Op.DIV)

bytecode_parser = Lark(
    bytecode_grammar,
    parser='lalr',
    transformer=BytecodeTransformer()
)

parse = bytecode_parser.parse