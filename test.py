import sys
import os
import glob
import io
import contextlib
import subprocess

import pytest

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

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

@pytest.mark.parametrize('file', glob.glob(os.path.join(current_dir, 'tests', '*.nox')))
def test_program(file):
    program, inp, expected_output = read_files(file)
    program = syntax.parse(program)
    program = bc.compile(program)
    assert program == bc.parse(str(program))

    bytecode_file = file.replace('.nox', '.noxbc')
    with open(bytecode_file, 'wt') as f:
        f.write(str(program))

    out = io.StringIO()
    state = bc.State()
    with contextlib.redirect_stdout(out), use_as_stdin(inp):
        assert bc.execute(state, program) == 0

    assert len(state.stack) == 0, str(stack)
    assert expected_output == out.getvalue()

    asm = x64.compile(program)
    asm_file = file.replace('.nox', '.s')
    with open(asm_file, 'wt') as f:
        f.write(asm)

    driver.build(asm_file)
    binary = file.replace('.nox', '.exe')
    status = subprocess.run([binary], input=inp.encode(), capture_output=True, timeout=0.5, check=True)
    assert expected_output == status.stdout.decode()