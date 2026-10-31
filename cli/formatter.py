"""
JapyScript — canonical source formatter.

Style rules (v0.3):
  1. Four spaces per indentation level.
  2. No trailing whitespace on any line.
  3. Exactly one blank line between top-level statements.
  4. Single space around binary operators and after commas.
  5. No space immediately inside parentheses or brackets.
  6. File ends with exactly one newline.
"""

from __future__ import annotations
from compiler.lexer import tokenize, LexerError
from compiler.tokens import TokenKind
from compiler.parser import parse, ParseError


class FormatError(Exception):
    pass


def _strip_trailing(line: str) -> str:
    return line.rstrip(" \t")


def _normalise_indent(line: str) -> str:
    if not line.strip():
        return ""
    width = 0
    for ch in line:
        if ch == " ":
            width += 1
        elif ch == "\t":
            width += 4
        else:
            break
    level = width // 4
    return "    " * level + line.lstrip(" \t")


def _normalise_operators(line: str) -> str:
    if line.strip().startswith("//"):
        return line
    out = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "=" and (i == 0 or line[i - 1] not in "!<>=+-*/%"):
            if i + 1 < len(line) and line[i + 1] == "=":
                out.append("==")
                i += 2
                continue
            while out and out[-1] == " ":
                out.pop()
            out.append(" = ")
            i += 1
            while i < len(line) and line[i] == " ":
                i += 1
            continue
        if ch == ",":
            out.append(", ")
            i += 1
            while i < len(line) and line[i] == " ":
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _normalise_parens(line: str) -> str:
    return (line
            .replace("( ", "(")
            .replace(" )", ")")
            .replace("[ ", "[")
            .replace(" ]", "]"))


def format_source(source: str) -> str:
    try:
        tokenize(source, "<format>")
        parse(tokenize(source, "<format>"))
    except (LexerError, ParseError) as e:
        raise FormatError(f"cannot format: {e}")

    raw_lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while raw_lines and raw_lines[-1] == "":
        raw_lines.pop()

    out: list[str] = []
    prev_blank = True
    for line in raw_lines:
        line = _strip_trailing(line)
        if line == "":
            if prev_blank:
                continue
            out.append("")
            prev_blank = True
            continue
        line = _normalise_indent(line)
        if not line.lstrip().startswith("//"):
            line = _normalise_parens(_normalise_operators(line))
        out.append(line)
        prev_blank = False

    return "\n".join(out) + "\n"


def format_file(path: str, in_place: bool = True) -> str:
    with open(path, encoding="utf-8") as f:
        source = f.read()
    formatted = format_source(source)
    if in_place:
        with open(path, "w", encoding="utf-8") as f:
            f.write(formatted)
    return formatted
