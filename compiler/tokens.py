"""
JapyScript — token model.

Every token carries its source location. The lexer emits a flat list of
tokens terminated by EOF. Blocks are represented by INDENT / DEDENT tokens.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenKind(Enum):
    # literals
    NUMBER   = auto()
    STRING   = auto()
    IDENT    = auto()

    # keywords
    KW_DEF     = auto()
    KW_CLASS   = auto()
    KW_RETURN  = auto()
    KW_IF      = auto()
    KW_ELIF    = auto()
    KW_ELSE    = auto()
    KW_FOR     = auto()
    KW_WHILE   = auto()
    KW_IN      = auto()
    KW_BREAK   = auto()
    KW_CONTINUE= auto()
    KW_TRY     = auto()
    KW_EXCEPT  = auto()
    KW_FINALLY = auto()
    KW_THROW   = auto()
    KW_IMPORT  = auto()
    KW_FROM    = auto()
    KW_AS      = auto()
    KW_ASYNC   = auto()
    KW_AWAIT   = auto()
    KW_LET     = auto()
    KW_CONST   = auto()
    KW_VAR     = auto()
    KW_TRUE    = auto()
    KW_FALSE   = auto()
    KW_NULL    = auto()
    KW_TYPE    = auto()

    # operators / punctuation
    PLUS      = auto()
    MINUS     = auto()
    STAR      = auto()
    SLASH     = auto()
    PERCENT   = auto()
    POW       = auto()
    EQ        = auto()
    EQEQ      = auto()
    NEQ       = auto()
    LT        = auto()
    LE        = auto()
    GT        = auto()
    GE        = auto()
    AND       = auto()
    OR        = auto()
    NOT       = auto()
    ARROW     = auto()
    LPAREN    = auto()
    RPAREN    = auto()
    LBRACKET  = auto()
    RBRACKET  = auto()
    LBRACE    = auto()
    RBRACE    = auto()
    COMMA     = auto()
    COLON     = auto()
    DOT       = auto()
    SEMI      = auto()

    # structure
    NEWLINE = auto()
    INDENT  = auto()
    DEDENT  = auto()
    EOF     = auto()


KEYWORDS = {
    "def": TokenKind.KW_DEF, "class": TokenKind.KW_CLASS,
    "return": TokenKind.KW_RETURN, "if": TokenKind.KW_IF,
    "elif": TokenKind.KW_ELIF, "else": TokenKind.KW_ELSE,
    "for": TokenKind.KW_FOR, "while": TokenKind.KW_WHILE,
    "in": TokenKind.KW_IN, "break": TokenKind.KW_BREAK,
    "continue": TokenKind.KW_CONTINUE, "try": TokenKind.KW_TRY,
    "except": TokenKind.KW_EXCEPT, "finally": TokenKind.KW_FINALLY,
    "throw": TokenKind.KW_THROW, "import": TokenKind.KW_IMPORT,
    "from": TokenKind.KW_FROM, "as": TokenKind.KW_AS,
    "async": TokenKind.KW_ASYNC, "await": TokenKind.KW_AWAIT,
    "let": TokenKind.KW_LET, "const": TokenKind.KW_CONST,
    "var": TokenKind.KW_VAR, "true": TokenKind.KW_TRUE,
    "false": TokenKind.KW_FALSE, "null": TokenKind.KW_NULL,
    "type": TokenKind.KW_TYPE,
}


@dataclass
class Token:
    kind: TokenKind
    value: Any
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.kind.name}, {self.value!r}, {self.line}:{self.col})"
