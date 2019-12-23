from __future__ import absolute_import, unicode_literals

import os
import sys
from distutils.spawn import find_executable

from virtualenv.info import IS_WIN

from .discover import Discover
from .py_info import CURRENT, PythonInfo
from .py_spec import PythonSpec


class Builtin(Discover):
    def __init__(self, options):
        super(Builtin, self).__init__()
        self.python_spec = options.python

    @classmethod
    def add_parser_arguments(cls, parser):
        parser.add_argument(
            "-p",
            "--python",
            dest="python",
            metavar="py",
            help="target interpreter for which to create a virtual (either absolute path or identifier string)",
            default=sys.executable,
        )

    def run(self):
        return get_interpreter(self.python_spec)

    def __str__(self):
        return "{} discover of python_spec={!r}".format(self.__class__.__name__, self.python_spec)


def get_interpreter(key):
    spec = PythonSpec.from_string_spec(key)
    for interpreter, impl_must_match in propose_interpreters(spec):
        if interpreter.satisfies(spec, impl_must_match):
            return interpreter


def propose_interpreters(spec):
    # 1. we always try with the lowest hanging fruit first, the current interpreter
    yield CURRENT, True

    # 2. if it's an absolut path and exists, use that
    if spec.is_abs and os.path.exists(spec.path):
        yield PythonInfo.from_exe(spec.path), True

    # 3. otherwise fallback to platform default logic
    if IS_WIN:
        from .windows import propose_interpreters

        for interpreter in propose_interpreters(spec):
            yield interpreter, True

    # 4. then maybe it's something exact on PATH - if it was direct lookup implementation no longer counts
    interpreter = find_on_path(spec.str_spec)
    if interpreter is not None:
        yield interpreter, False

    # 5. or from the spec we can deduce a name on path  that matches
    for exe, match in spec.generate_names():
        interpreter = find_on_path(exe)
        if interpreter is not None:
            yield interpreter, match


def find_on_path(key):
    exe = find_executable(key)
    if exe is not None:
        exe = os.path.abspath(exe)
        interpreter = PythonInfo.from_exe(str(exe), raise_on_error=False)
        return interpreter