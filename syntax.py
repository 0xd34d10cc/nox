from lark import Lark


language_grammar = '''
    ?start: program

    ?program: statement*
    ?block: "{" statement* "}"
    ?statement: assign | if_else | while | do_while | for | call_statement
    if_else: "if" expr block ("else" "if" expr block)* ["else" block]
    while: "while" expr block
    do_while: "do" block "while" expr
    for: "for" statement "," expr "," statement block
    assign: VAR ASSIGN expr
    call_statement: VAR "(" [expr ("," expr)*] ")"

    ?expr: disj
    ?disj: conj (OR conj)*
    ?conj: cmp (AND cmp)*
    ?cmp: sum ((LT|LE|GT|GE|EQ|NE) sum)*
    ?sum: product ((ADD|SUB) product)*
    ?product: atom ((MUL|DIV|MOD) atom)*
    ?atom: SIGNED_INT | VAR | call_expr | "(" expr ")"
    call_expr: VAR "(" [expr ("," expr)*] ")"

    ADD: "+"
    SUB: "-"
    MUL: "*"
    DIV: "/"
    MOD: "%"

    AND: "&&"
    OR: "||"
    LT: "<"
    LE: "<="
    GT: ">"
    GE: ">="
    EQ: "=="
    NE: "!="

    ASSIGN: "="

    %import common.SIGNED_INT
    %import common.CNAME -> VAR
    %import common.WS
    %import common.CPP_COMMENT

    %ignore WS
    %ignore CPP_COMMENT
'''

parser = Lark(language_grammar, parser='lalr')
parse = parser.parse

if __name__ == '__main__':
    import sys
    from lark import tree
    program = sys.argv[1]
    program = open(program, 'rt', encoding='utf-8').read()
    program = parse(program)
    tree.pydot__tree_to_png(program, 'program.png')