import sys
import os
import glob
import io
import re
import contextlib
import difflib

current_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

import syntax
import bc

@contextlib.contextmanager
def redirect_stdin(file):
    original = sys.stdin
    sys.stdin = file
    yield
    sys.stdin = original

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in _nsre.split(s)]

files = glob.glob(os.path.join(current_dir, '*.nox'))
cases = sorted(files, key=natural_sort_key)
for test_case in cases:
    name = os.path.basename(test_case)
    print(f'Test {name:<10}', end='', flush=True)

    with open(test_case, 'rt', encoding='utf-8') as f:
        program = f.read()

    with open(test_case.replace('.nox', '.in'), 'rt', encoding='utf-8') as f:
        input = f.read()

    with open(test_case.replace('.nox', '.out'), 'rt', encoding='utf-8') as f:
        expected_output = f.read()

    program = syntax.parse(program)
    program = bc.compile(program)

    out = io.StringIO()
    input = io.StringIO(input)
    state = bc.State(ip=0, stack=[], memory={})
    with contextlib.redirect_stdout(out), redirect_stdin(input):
        bc.execute(state, program)

    assert len(state.stack) == 0, str(stack)
    actual_output = out.getvalue()

    if actual_output != expected_output:
        print('FAIL')
        diffs = difflib.ndiff(
            expected_output.splitlines(keepends=True),
            actual_output.splitlines(keepends=True)
        )
        print(''.join(diffs))
    else:
        print('OK')