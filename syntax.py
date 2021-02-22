from lark import Lark, tree


language_grammar = '''
    ?start: program

    ?program: statement*
    ?statement: assign
    assign: VAR EQ expr
    ?expr: term (ADD term | SUB term)*
    ?term: factor (MUL factor | DIV factor)*
    ?factor: SIGNED_INT | VAR | "(" expr ")"

    ADD: "+"
    SUB: "-"
    MUL: "*"
    DIV: "/"
    EQ: "="

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