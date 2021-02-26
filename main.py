import sys
import os
import subprocess
import shutil

import bc
import syntax


def find_winsdk():
    base = r'C:\Program Files (x86)\Windows Kits\10\Lib'

    def version(path):
        return [int(part) for part in os.path.basename(path).split('.')]

    latest_sdk = max(os.listdir(base), key=version)
    return os.path.join(base, latest_sdk)

def assemble(program):
    assert os.name == 'nt', 'Assembly compilation for {os.name} is not implemented'
    assembler = shutil.which('nasm')
    linker = shutil.which('lld-link') or shutil.which('link')
    assert assembler, 'nasm is not in PATH'
    assert linker, 'linker is not in PATH'

    subprocess.run([assembler, '-f', 'win64', program], check=True)
    obj = os.path.splitext(program)[0] + '.obj'
    kernel32 = os.path.join(find_winsdk(), 'um', 'x64', 'kernel32.lib')
    subprocess.run([linker, obj, '/subsystem:console', '/entry:main', kernel32], check=True)
    os.remove(obj)

def main(file):
    if file.endswith('.s') or file.endswith('.asm'):
        assemble(file)
        return

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