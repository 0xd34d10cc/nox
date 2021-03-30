from .instruction import Fn


def syscall(name, *args, returns_value=True):
    return Fn(name, args=list(args), locals=set(), returns_value=returns_value, start=None, end=None)


_by_number = {
    # Exit the program
    0: syscall('exit', 'code', returns_value=False),

    # File IO
    1: syscall('open', 'filename'),
    2: syscall('close', 'file'),
    3: syscall('read', 'file', 'n'),
    4: syscall('write', 'file', 'data'),

    # list builtins
    20: syscall('list'),
    21: syscall('list_get', 'list', 'i'),
    22: syscall('list_set','list',  'i', 'val', returns_value=False),
    23: syscall('list_push', 'list', 'val', returns_value=False),
    24: syscall('list_len', 'list'),
    25: syscall('list_clear', 'list', returns_value=False),
    26: syscall('list_slice', 'list', 'left', 'right'),
    27: syscall('list_ref', 'list'),
    28: syscall('list_unref', 'list'),

    100: syscall('print', 'val', returns_value=False),
    101: syscall('input')
}

_by_name = {
    s.name: (n, s)
    for n, s in _by_number.items()
}

def enumerate():
    return _by_name.values()

def number_by_name(name):
    if name in _by_name:
        return _by_name[name][0]
    else:
        return None

def by_name(name):
    return _by_name.get(name, None)

def by_number(n):
    return _by_number.get(n, None)