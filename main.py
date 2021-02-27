import sys
import os
import subprocess
import shutil

import bc
import syntax
import x64


def rt_asm(target_os):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'rt', f'{target_os}.s')

def find_winsdk():
    base = r'C:\Program Files (x86)\Windows Kits\10\Lib'

    def version(path):
        return [int(part) for part in os.path.basename(path).split('.')]

    latest_sdk = max(os.listdir(base), key=version)
    return os.path.join(base, latest_sdk)

def build(program):
    assert os.name == 'nt', 'Assembly compilation for {os.name} is not implemented'
    assembler = shutil.which('nasm')
    linker = shutil.which('lld-link') or shutil.which('link')
    assert assembler, 'nasm is not in PATH'
    assert linker, 'linker is not in PATH'

    def assemble(program):
        subprocess.run([assembler, '-f', 'win64', program], check=True)
        return program.replace('.s', '.obj').replace('.asm', '.obj')

    obj = assemble(program)
    rt = assemble(rt_asm(os.name))
    kernel32 = os.path.join(find_winsdk(), 'um', 'x64', 'kernel32.lib')
    subprocess.run([linker, obj, rt, '/subsystem:console', '/entry:main', kernel32], check=True)
    os.remove(rt)
    os.remove(obj)

def main(file):
    if file.endswith('.s') or file.endswith('.asm'):
        build(file)
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

    x64.compile(program)
    # state = bc.State()
    # code = bc.execute(state, program)
    # print(f'Finished with code {code}')

if __name__ == '__main__':
    main(*sys.argv[1:])