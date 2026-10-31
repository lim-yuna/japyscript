"""
JapyScript compiler package.

Exports the public compile pipeline and version metadata. Every stage of the
pipeline is importable on its own for tools that need partial compilation.
"""

__version__ = "0.3.0"

from .lexer import tokenize, Lexer, LexerError
from .parser import parse, Parser, ParseError
from .emitter import Emitter, EmitError
from .emitter.bytecode import CodeObject, Instr, Op, disassemble


def compile_source(source: str, filename: str = "<input>") -> CodeObject:
    """Lex, parse, and emit bytecode for a source string. No type checking."""
    tokens = tokenize(source, filename)
    program = parse(tokens)
    return Emitter().compile_program(program)


def compile_and_check(source: str, filename: str = "<input>") -> CodeObject:
    """Same as compile_source but runs the static checker first."""
    from .checker import check
    tokens = tokenize(source, filename)
    program = parse(tokens)
    check(program)
    return Emitter().compile_program(program)


__all__ = [
    "compile_source",
    "compile_and_check",
    "tokenize", "parse",
    "Lexer", "Parser", "Emitter",
    "LexerError", "ParseError", "EmitError",
    "CodeObject", "Instr", "Op", "disassemble",
    "__version__",
]
