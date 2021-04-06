from lark import Lark


language_grammar = '''
    ?start: program

    program: global* function* statement*

    global    : "global" VAR ("," VAR)*
    function  : "fn" VAR "(" args  ")" ["->" typename] block
    args      : [VAR ("," VAR)*]
    typename  : "int" | "list" | "str"
    ?block    : "{" statement* "}"
    ?statement: assign | assign_at | if_else | while | do_while | for | return | pass | call
    if_else   : "if" expr block ("else" "if" expr block)* ["else" block]
    while     : "while" expr block
    do_while  : "do" block "while" expr
    for       : "for" statement "," expr "," statement block
    assign_at : atom "[" expr "]" ASSIGN expr
    assign    : VAR ASSIGN expr
    return    : "return" expr
    pass      : "pass"

    ?expr   : disj
    ?disj   : conj (OR conj)*
    ?conj   : cmp (AND cmp)*
    ?cmp    : sum ((LT|LE|GT|GE|EQ|NE) sum)*
    ?sum    : product ((ADD|SUB) product)*
    ?product: atom ((MUL|DIV|MOD) atom)*
    ?atom   : int_lit | char_lit | list_lit | str_lit | list_at | call | var_expr | "(" expr ")"
    int_lit : SIGNED_INT
    char_lit: "'" CHAR "'"
    list_lit: "[" [expr ("," expr)*] "]"
    str_lit : STR
    list_at : atom "[" expr "]"
    var_expr: VAR
    call    : VAR "(" [expr ("," expr)*] ")"

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
    CHAR: "a".."z" | "A".."Z"

    %import common.SIGNED_INT
    %import common.CNAME -> VAR
    %import common.ESCAPED_STRING -> STR
    %import common.WS
    %import common.CPP_COMMENT

    %ignore WS
    %ignore CPP_COMMENT
'''

parser = Lark(language_grammar)
parse = parser.parse

if __name__ == '__main__':
    import sys
    from lark import tree
    program = sys.argv[1]
    program = open(program, 'rt', encoding='utf-8').read()
    program = parse(program)
    tree.pydot__tree_to_png(program, 'program.png')