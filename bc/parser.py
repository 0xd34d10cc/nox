from . import Op, Instruction, Label, Program
from lark import Lark, Transformer, v_args


bytecode_grammar = '''
    ?start: program

    program: item* -> program

    ?item: instruction | jmp_label
    jmp_label: var ":" -> label
    label: var -> label
    instruction: "load" var -> load
        | "store" var       -> store
        | "gload" var       -> gload
        | "gstore" var      -> gstore
        | "const" num       -> const
        | "add"             -> add
        | "sub"             -> sub
        | "mul"             -> mul
        | "div"             -> div
        | "mod"             -> mod
        | "and"             -> and_
        | "or"              -> or_
        | "lt"              -> lt
        | "le"              -> le
        | "gt"              -> gt
        | "ge"              -> ge
        | "eq"              -> eq
        | "ne"              -> ne
        | "jmp" label       -> jmp
        | "jz" label        -> jz
        | "jnz" label       -> jnz
        | "call" label      -> call
        | "syscall" num     -> syscall
        | "ret"             -> ret
        | "leave"           -> leave
        | "enter" fn_tag "(" [var ("," var)*] ")" -> enter

    fn_tag: "fn" -> fn
        | "proc" -> proc
    var: CNAME -> var
    num: SIGNED_INT -> number

    %import common.CNAME
    %import common.SIGNED_INT
    %import common.WS
    %import common.SH_COMMENT

    %ignore SH_COMMENT
    %ignore WS
'''

def make_handler(op):
    def handler(self, *args):
        return Instruction(op, *args)
    return handler

def const(val):
    def handler(self, *args):
        return val
    return handler

@v_args(inline=True)
class BytecodeTransformer(Transformer):
    def program(self, *instructions):
        return Program.build(list(instructions))

    number  = int
    var     = str
    label   = Label
    fn      = const('fn')
    proc    = const('proc')

    load    = make_handler(Op.LOAD)
    store   = make_handler(Op.STORE)
    gload   = make_handler(Op.GLOAD)
    gstore  = make_handler(Op.GSTORE)

    const   = make_handler(Op.CONST)
    add     = make_handler(Op.ADD)
    sub     = make_handler(Op.SUB)
    mul     = make_handler(Op.MUL)
    div     = make_handler(Op.DIV)
    mod     = make_handler(Op.MOD)

    and_    = make_handler(Op.AND)
    or_     = make_handler(Op.OR)
    lt      = make_handler(Op.LT)
    le      = make_handler(Op.LE)
    gt      = make_handler(Op.GT)
    ge      = make_handler(Op.GE)
    eq      = make_handler(Op.EQ)
    ne      = make_handler(Op.NE)

    jmp     = make_handler(Op.JMP)
    jz      = make_handler(Op.JZ)
    jnz     = make_handler(Op.JNZ)
    call    = make_handler(Op.CALL)
    syscall = make_handler(Op.SYSCALL)
    ret     = make_handler(Op.RET)

    enter   = make_handler(Op.ENTER)
    leave   = make_handler(Op.LEAVE)

bytecode_parser = Lark(
    bytecode_grammar,
    parser='lalr',
    transformer=BytecodeTransformer()
)

parse = bytecode_parser.parse