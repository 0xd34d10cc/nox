import sys
import bc


def main(file):
    with open(file, 'rt', encoding='utf-8') as f:
        program = bc.parse(f.read())

    state = bc.State(stack=[], memory={})
    bc.execute(state, program)
    print(state)

if __name__ == '__main__':
    main(*sys.argv[1:])