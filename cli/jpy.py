#!/usr/bin/env python3
"""
JapyScript command-line interface.

    jpy run   <file.jpy>       compile and execute
    jpy build <file.jpy>       compile to .jpc bytecode
    jpy check <file.jpy>       static analysis
    jpy dis   <file.jpy>       print bytecode disassembly
    jpy repl                   interactive shell
    jpy fmt   <file.jpy>       format source
    jpy --version              show version
"""

from __future__ import annotations
import argparse
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.lexer import tokenize, LexerError
from compiler.parser import parse, ParseError
from compiler.emitter import Emitter, EmitError
from compiler.emitter.bytecode import disassemble
from compiler.checker import check, CheckError
from vm.machine import VM, JpyError

VERSION = "0.2.0"


def compile_source(source: str, filename: str = "<input>"):
    tokens = tokenize(source, filename)
    program = parse(tokens)
    return Emitter().compile_program(program)


def cmd_run(args) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            source = f.read()
        code = compile_source(source, args.file)
        VM().run(code)
        return 0
    except (LexerError, ParseError, EmitError, JpyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1


def cmd_build(args) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            source = f.read()
        code = compile_source(source, args.file)
    except (LexerError, ParseError, EmitError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out = args.file.rsplit(".", 1)[0] + ".jpc"
    with open(out, "wb") as f:
        pickle.dump(code, f)
    print(f"wrote {out}  ({len(code.instructions)} instructions, "
          f"{len(code.constants)} constants)")
    return 0


def cmd_check(args) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            source = f.read()
        tokens = tokenize(source, args.file)
        program = parse(tokens)
        check(program)
    except (LexerError, ParseError, CheckError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"{args.file}: ok")
    return 0


def cmd_dis(args) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            source = f.read()
        code = compile_source(source, args.file)
    except (LexerError, ParseError, EmitError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(disassemble(code))
    return 0


def cmd_repl(args) -> int:
    print(f"JapyScript REPL  v{VERSION}")
    print("Type Ctrl-D or 'exit' to quit.")
    vm = VM()
    while True:
        try:
            line = input("jpy> ")
        except EOFError:
            print()
            return 0
        if line.strip() in ("exit", "quit"):
            return 0
        try:
            code = compile_source(line, "<repl>")
            vm.run(code)
        except (LexerError, ParseError, EmitError, JpyError) as e:
            print(f"error: {e}", file=sys.stderr)


def cmd_fmt(args) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 1
    # Canonical formatter: currently only trims trailing whitespace and
    # normalises line endings. Full rules arrive with the formatter module.
    normalised = "\n".join(line.rstrip() for line in source.replace("\r\n", "\n").split("\n"))
    with open(args.file, "w", encoding="utf-8") as f:
        f.write(normalised)
    print(f"formatted {args.file}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="jpy", description="JapyScript toolchain")
    ap.add_argument("--version", action="version", version=f"jpy {VERSION}")
    sub = ap.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="compile and execute a .jpy file")
    p_run.add_argument("file")
    p_run.set_defaults(func=cmd_run)

    p_build = sub.add_parser("build", help="compile to .jpc bytecode")
    p_build.add_argument("file")
    p_build.set_defaults(func=cmd_build)

    p_check = sub.add_parser("check", help="static analysis")
    p_check.add_argument("file")
    p_check.set_defaults(func=cmd_check)

    p_dis = sub.add_parser("dis", help="disassemble compiled bytecode")
    p_dis.add_argument("file")
    p_dis.set_defaults(func=cmd_dis)

    p_repl = sub.add_parser("repl", help="interactive shell")
    p_repl.set_defaults(func=cmd_repl)

    p_fmt = sub.add_parser("fmt", help="format a source file")
    p_fmt.add_argument("file")
    p_fmt.set_defaults(func=cmd_fmt)

    args = ap.parse_args(argv)
    if not hasattr(args, "func"):
        ap.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
