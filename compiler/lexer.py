"""
JapyScript — lexer.

Converts source text into a flat token stream, inserting INDENT / DEDENT
tokens around blocks and NEWLINE tokens between logical lines.
"""

from __future__ import annotations
from .tokens import Token, TokenKind, KEYWORDS


class LexerError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"{line}:{col}: {message}")
        self.message = message
        self.line = line
        self.col = col


OPERATORS = [
    ("**", TokenKind.POW),  ("==", TokenKind.EQEQ), ("!=", TokenKind.NEQ),
    ("<=", TokenKind.LE),   (">=", TokenKind.GE),   ("&&", TokenKind.AND),
    ("||", TokenKind.OR),   ("=>", TokenKind.ARROW),
    ("+",  TokenKind.PLUS), ("-",  TokenKind.MINUS),("*",  TokenKind.STAR),
    ("/",  TokenKind.SLASH),("%",  TokenKind.PERCENT),("=",  TokenKind.EQ),
    ("<",  TokenKind.LT),   (">",  TokenKind.GT),   ("!",  TokenKind.NOT),
    ("(",  TokenKind.LPAREN),(")", TokenKind.RPAREN),
    ("[",  TokenKind.LBRACKET),("]", TokenKind.RBRACKET),
    ("{",  TokenKind.LBRACE),("}", TokenKind.RBRACE),
    (",",  TokenKind.COMMA),(":",  TokenKind.COLON),
    (".",  TokenKind.DOT),  (";",  TokenKind.SEMI),
]


class Lexer:
    def __init__(self, source: str, filename: str = "<input>"):
        self.src = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.col = 1
        self.indent_stack = [0]
        self.tokens: list[Token] = []

    def error(self, msg):
        raise LexerError(msg, self.line, self.col)

    def peek(self, n=0):
        i = self.pos + n
        return self.src[i] if i < len(self.src) else ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def emit(self, kind, value=None, line=None, col=None):
        self.tokens.append(Token(kind, value, line or self.line, col or self.col))

    # ---- main loop --------------------------------------------------------
    def tokenize(self) -> list[Token]:
        at_line_start = True
        while self.pos < len(self.src):
            if at_line_start:
                at_line_start = self.handle_indentation()
                if self.pos >= len(self.src):
                    break
            ch = self.peek()

            if ch in " \t\r":
                self.advance()
                continue

            if ch == "\n":
                self.advance()
                self.emit(TokenKind.NEWLINE)
                at_line_start = True
                continue

            if ch == "/" and self.peek(1) == "/":
                while self.pos < len(self.src) and self.peek() != "\n":
                    self.advance()
                continue

            if ch == "/" and self.peek(1) == "*":
                self.skip_block_comment()
                continue

            if ch.isdigit() or (ch == "." and self.peek(1).isdigit()):
                self.read_number()
                continue

            if ch in "\"'":
                self.read_string()
                continue

            if ch.isalpha() or ch == "_":
                self.read_ident()
                continue

            if self.match_operator():
                continue

            self.error(f"unexpected character {ch!r}")

        # flush trailing NEWLINE + DEDENTs + EOF
        if self.tokens and self.tokens[-1].kind != TokenKind.NEWLINE:
            self.emit(TokenKind.NEWLINE)
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.emit(TokenKind.DEDENT)
        self.emit(TokenKind.EOF)
        return self.tokens

    # ---- indentation ------------------------------------------------------
    def handle_indentation(self) -> bool:
        """Measure leading spaces on the current line. Emit INDENT/DEDENT."""
        start = self.pos
        width = 0
        while self.pos < len(self.src):
            ch = self.peek()
            if ch == " ":
                width += 1; self.advance()
            elif ch == "\t":
                width += 4; self.advance()
            else:
                break

        # blank line or comment-only line → skip indentation entirely
        if self.pos >= len(self.src) or self.peek() == "\n":
            return True
        if self.peek() == "/" and self.peek(1) in "/*":
            return True

        current = self.indent_stack[-1]
        if width > current:
            self.indent_stack.append(width)
            self.emit(TokenKind.INDENT)
        elif width < current:
            while self.indent_stack and self.indent_stack[-1] > width:
                self.indent_stack.pop()
                self.emit(TokenKind.DEDENT)
            if self.indent_stack[-1] != width:
                self.pos = start
                self.error("inconsistent indentation")
        return False

    # ---- pieces -----------------------------------------------------------
    def skip_block_comment(self):
        depth = 0
        while self.pos < len(self.src):
            if self.peek() == "/" and self.peek(1) == "*":
                depth += 1; self.advance(); self.advance()
            elif self.peek() == "*" and self.peek(1) == "/":
                depth -= 1; self.advance(); self.advance()
                if depth == 0: return
            else:
                self.advance()
        self.error("unterminated block comment")

    def read_number(self):
        line, col = self.line, self.col
        buf = []
        is_float = False
        while self.pos < len(self.src):
            ch = self.peek()
            if ch.isdigit() or ch == "_":
                buf.append(self.advance())
            elif ch == "." and not is_float and self.peek(1).isdigit():
                is_float = True; buf.append(self.advance())
            else:
                break
        raw = "".join(buf).replace("_", "")
        self.emit(TokenKind.NUMBER, float(raw) if is_float else int(raw), line, col)

    def read_string(self):
        line, col = self.line, self.col
        quote = self.advance()
        buf = []
        while self.pos < len(self.src):
            ch = self.advance()
            if ch == "\\":
                nxt = self.advance()
                buf.append({"n": "\n", "t": "\t", "r": "\r",
                            "0": "\0", "\\": "\\",
                            "'": "'", '"': '"'}.get(nxt, nxt))
            elif ch == quote:
                self.emit(TokenKind.STRING, "".join(buf), line, col)
                return
            else:
                buf.append(ch)
        self.error("unterminated string")

    def read_ident(self):
        line, col = self.line, self.col
        buf = []
        while self.pos < len(self.src):
            ch = self.peek()
            if ch.isalnum() or ch == "_":
                buf.append(self.advance())
            else:
                break
        word = "".join(buf)
        self.emit(KEYWORDS.get(word, TokenKind.IDENT), word, line, col)

    def match_operator(self) -> bool:
        for text, kind in OPERATORS:
            if self.src.startswith(text, self.pos):
                line, col = self.line, self.col
                for _ in text:
                    self.advance()
                self.emit(kind, text, line, col)
                return True
        return False


def tokenize(source: str, filename: str = "<input>") -> list[Token]:
    return Lexer(source, filename).tokenize()
