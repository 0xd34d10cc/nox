import sys
import bc
import syntax


def main(file):
    with open(file, 'rt', encoding='utf-8') as f:
        program = f.read()

    if file.endswith('.nox'):
        program = syntax.parse(program)
        program = bc.compile(program)
    elif file.endswith('.noxbc'):
        program = bc.parse(program)
    else:
        raise Exception(f'Unsupported file type: {file}')

    state = bc.State()
    bc.execute(state, program)

if __name__ == '__main__':
    main(*sys.argv[1:])