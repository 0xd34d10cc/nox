from . import Op, Instruction
from lark import Lark, Transformer, v_args


bytecode_grammar = '''
    ?start: program

    program: instruction* -> program

    instruction: "LOAD" var -> load
        | "STORE" var       -> store
        | "CONST" num       -> const
        | "ADD"             -> add
        | "SUB"             -> sub
        | "MUL"             -> mul
        | "DIV"             -> div
        | "AND"             -> and_
        | "OR"              -> or_
        | "LT"              -> lt
        | "LE"              -> le
        | "GT"              -> gt
        | "GE"              -> ge
        | "EQ"              -> eq
        | "NE"              -> ne

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
    label  = str

    load   = make_handler(Op.LOAD)
    store  = make_handler(Op.STORE)

    const  = make_handler(Op.CONST)
    add    = make_handler(Op.ADD)
    sub    = make_handler(Op.SUB)
    mul    = make_handler(Op.MUL)
    div    = make_handler(Op.DIV)

    and_   = make_handler(Op.AND)
    or_    = make_handler(Op.OR)
    lt     = make_handler(Op.LT)
    le     = make_handler(Op.LE)
    gt     = make_handler(Op.GT)
    ge     = make_handler(Op.GE)
    eq     = make_handler(Op.EQ)
    ne     = make_handler(Op.NE)

bytecode_parser = Lark(
    bytecode_grammar,
    parser='lalr',
    transformer=BytecodeTransformer()
)

parse = bytecode_parser.parse