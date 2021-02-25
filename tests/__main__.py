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

files = glob.glob(os.path.join(current_dir, '*.nox'))
cases = sorted(files, key=natural_sort_key)
for test_case in cases:
    name = os.path.basename(test_case)
    print(f'Test {name:<10}', end='', flush=True)

    program, inp, expected_output = read_files(test_case)
    program = syntax.parse(program)
    program = bc.compile(program)
    assert program == bc.parse(str(program))

    out = io.StringIO()
    state = bc.State(ip=program.entry, stack=[], callstack=[], memory={})
    with contextlib.redirect_stdout(out), use_as_stdin(inp):
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