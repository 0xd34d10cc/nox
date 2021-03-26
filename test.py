import sys
import os
import glob
import io
import contextlib
import subprocess
import re

import pytest

import syntax
import bc
import x64
import driver

@contextlib.contextmanager
def use_as_stdin(s):
    original = sys.stdin
    sys.stdin = io.StringIO(s)
    yield
    sys.stdin = original

def read_files(base):
    data = tuple()
    for ext in '.nox', '.in', '.out':
        with open(base.replace('.nox', ext), 'rt', encoding='utf-8') as f:
            data += (f.read(),)
    return data

current_dir = os.path.dirname(os.path.realpath(__file__))
files = glob.glob(os.path.join(current_dir, 'tests', '*.nox'))

def natural_sort_key(key, _re=re.compile(r'([0-9]+)')):
    return [int(item) if item.isdigit() else item for item in _re.split(key)]

files = sorted(files, key=natural_sort_key)

vm = None
rt = None

@pytest.mark.parametrize('file', files)
def test_program(file):
    global vm, rt

    program, inp, expected_output = read_files(file)
    program = syntax.parse(program)
    program = bc.compile(program)
    assert program == bc.parse(str(program))

    bytecode_text = file.replace('.nox', '.noxtbc')
    with open(bytecode_text, 'wt') as f:
        f.write(str(program))

    out = io.StringIO()
    state = bc.State(program)
    with contextlib.redirect_stdout(out), use_as_stdin(inp):
        assert bc.execute(state, program) == 0

    assert len(state.stack) == 0, str(stack)
    assert expected_output == out.getvalue()

    asm = x64.compile(program)
    asm_file = file.replace('.nox', '.s')
    with open(asm_file, 'wt') as f:
        f.write(asm)

    if rt is None:
        rt = driver.compile(driver.runtime())

    driver.build(asm_file, [rt], with_runtime=False)
    binary = file.replace('.nox', '.exe')
    status = subprocess.run([binary], input=inp.encode(), capture_output=True, timeout=0.5, check=True)
    assert expected_output == status.stdout.decode()

    bytecode = file.replace('.nox', '.noxbc')
    with open(bytecode, 'wb') as f:
        f.write(program.serialize())

    if vm is None:
        driver.build('vm.c', [rt], with_runtime=False)
        vm = 'vm.exe'
    status = subprocess.run([vm, bytecode], input=inp.encode(), capture_output=True, timeout=0.5, check=True)
    assert expected_output == status.stdout.decode()