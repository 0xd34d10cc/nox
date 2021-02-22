from lark import Lark, tree


language_grammar = '''
    ?start: program

    ?program: statement*
    ?statement: assign
    assign: VAR ASSIGN expr

    ?expr: disj
    ?disj: conj (OR conj)*
    ?conj: cmp (AND cmp)*
    ?cmp: arithm ((LT|LE|GT|GE|EQ|NE) arithm)*
    ?arithm: term ((ADD|SUB) term)*
    ?term: factor ((MUL|DIV) factor)*
    ?factor: SIGNED_INT | VAR | "(" expr ")"

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
    program = '''
        a = 4
        b = 3
        x = 1+2*b*(a+5)
    '''
    program = parse(program)
    tree.pydot__tree_to_png(program, 'program.png')