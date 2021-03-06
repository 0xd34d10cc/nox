import sys
import os
import subprocess
import shutil

import syntax
import bc
import x64


def runtime():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, 'rt', f'{os.name}.c')

sdk = None

def find_winsdk():
    global sdk
    if sdk is not None:
        return sdk

    base = r'C:\Program Files (x86)\Windows Kits\10\Lib'

    def version(path):
        return [int(part) for part in os.path.basename(path).split('.')]

    latest_sdk = max(os.listdir(base), key=version)
    sdk = os.path.join(base, latest_sdk)
    return sdk

compiler = shutil.which('cl')
assembler = shutil.which('nasm')
linker = shutil.which('link')

def compile(program, definitions=None):
    assert compiler, 'cl not in PATH'
    args = '/nologo', '/GS-', '/O2', '/Oi-', '/c'
    if definitions is not None:
        args += tuple(f'/D{d}' for d in definitions)
    subprocess.run([compiler, *args, program], check=True)
    return os.path.join(os.getcwd(), os.path.basename(program).replace('.c', '.obj'))

def assemble(program):
    assert os.name == 'nt', 'Assembly compilation for {os.name} is not implemented'
    assert assembler, 'nasm is not in PATH'
    subprocess.run([assembler, '-f', 'win64', program], check=True)
    return program.replace('.s', '.obj').replace('.asm', '.obj')

def build(program, objects=None, with_runtime=True, definitions=None):
    assert linker, 'linker is not in PATH'
    if objects is None:
        objects = []

    if program.endswith('.s'):
        obj = assemble(program)
    elif program.endswith('.c'):
        obj = compile(program, definitions=definitions)

    objects.append(obj)
    if with_runtime:
        rt = compile(runtime(), definitions=definitions)
        objects.append(rt)

    kernel32 = os.path.join(find_winsdk(), 'um', 'x64', 'kernel32.lib')
    args = '/nologo', '/nodefaultlib', '/subsystem:console', '/entry:main'
    out = program.replace('.s', '.exe').replace('.c', '.exe')
    subprocess.run([linker, *args, *objects, kernel32, f'/out:{out}'], check=True)
    if with_runtime:
        os.remove(rt)
    os.remove(obj)

def main(file):
    if file.endswith('.s') or file.endswith('.c'):
        build(file)
        return

    with open(file, 'rt', encoding='utf-8') as f:
        program = f.read()

    if file.endswith('.nox'):
        program = syntax.parse(program)
        program = bc.compile(program)
    elif file.endswith('.noxtbc'):
        program = bc.parse(program)
        # data = program.serialize()
        # with open(file.replace('.noxtbc', '.noxbc'), 'wb') as f:
        #     f.write(data)
        # return
        # TODO: implement --target option
        program = x64.compile(program)
    else:
        raise Exception(f'Unsupported file type: {file}')

    print(program)

if __name__ == '__main__':
    main(*sys.argv[1:])