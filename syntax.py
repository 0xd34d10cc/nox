from lark import Lark, tree


language_grammar = '''
    ?start: program

    ?program: block
    ?block: statement*
    ?statement: assign
    assign: VAR ASSIGN expr

    ?expr: disj
    ?disj: conj (OR conj)*
    ?conj: cmp (AND cmp)*
    ?cmp: sum ((LT|LE|GT|GE|EQ|NE) sum)*
    ?sum: product ((ADD|SUB) product)*
    ?product: atom ((MUL|DIV) atom)*
    ?atom: SIGNED_INT | VAR | "(" expr ")"

    ADD: "+"
    SUB: "-"
    MUL: "*"
    DIV: "/"

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
    %import common.WS
    %import common.CNAME -> VAR
    %ignore WS
'''

parser = Lark(language_grammar, parser='lalr')
parse = parser.parse

if __name__ == '__main__':
    program = open('example.nox', 'rt', encoding='utf-8').read()
    program = parse(program)
    tree.pydot__tree_to_png(program, 'program.png')