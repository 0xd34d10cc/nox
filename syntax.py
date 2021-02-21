from lark import Lark, tree


language_grammar = '''
    ?start: expr

    ?expr: term (ADD term | SUB term)*
    ?term: factor (MUL factor | DIV factor)*
    ?factor: SIGNED_INT | "(" expr ")"

    ADD: "+"
    SUB: "-"
    MUL: "*"
    DIV: "/"

    %import common.SIGNED_INT
    %import common.WS
    %ignore WS
'''

parser = Lark(language_grammar, parser='lalr')
parse = parser.parse

if __name__ == '__main__':
    parsed = parse('1+2*3*(4+5)')
    tree.pydot__tree_to_png(parsed, 'tree.png')