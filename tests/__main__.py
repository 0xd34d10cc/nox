import sys
import os
import glob
import io
import re
import contextlib
import difflib
import subprocess
import traceback

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

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

def read_files(base):
    data = tuple()
    for ext in '.nox', '.in', '.out':
        with open(base.replace('.nox', ext), 'rt', encoding='utf-8') as f:
            data += (f.read(),)
    return data

def run_case(test_case):
    program, inp, expected_output = read_files(test_case)
    program = syntax.parse(program)
    program = bc.compile(program)
    assert program == bc.parse(str(program))

    out = io.StringIO()
    state = bc.State()
    with contextlib.redirect_stdout(out), use_as_stdin(inp):
        assert bc.execute(state, program) == 0

    assert len(state.stack) == 0, str(stack)
    actual_output = out.getvalue()
    if actual_output != expected_output:
        print('FAIL (bc)')
        diffs = difflib.ndiff(
            expected_output.splitlines(keepends=True),
            actual_output.splitlines(keepends=True)
        )
        print(''.join(diffs))
        return False

    asm = x64.compile(program)
    asm_file = test_case.replace('.nox', '.s')
    with open(asm_file, 'wt') as f:
        f.write(asm)

    driver.build(asm_file)
    binary = test_case.replace('.nox', '.exe')
    status = subprocess.run([binary], input=inp.encode(), capture_output=True, timeout=0.5, check=True)
    actual_output = status.stdout.decode()
    if actual_output != expected_output:
        print('FAIL (x64)')
        diffs = difflib.ndiff(
            expected_output.splitlines(keepends=True),
            actual_output.splitlines(keepends=True)
        )
        print(''.join(diffs))
        return False

    print('OK')
    return True

files = glob.glob(os.path.join(current_dir, '*.nox'))
cases = sorted(files, key=natural_sort_key)
successes = 0
for test_case in cases:
    name = os.path.basename(test_case)
    print(f'Test {name:<10}', end='', flush=True)
    try:
        if run_case(test_case):
            successes += 1
    except Exception as e:
        print(f'FAIL (exception)')
        traceback.print_exc()

print(f'Finished {len(cases)}: {successes} passed, {len(cases) - successes} failed')



