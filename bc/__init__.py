from .instruction import Op, Instruction, Label, Program, Fn
from .parser import parse
from .runtime import State, execute
from .compiler import compile

from . import syscall