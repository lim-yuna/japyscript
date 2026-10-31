"""
JapyScript — recursive descent parser with Pratt expression parsing.

Consumes the token stream produced by compiler.lexer and produces a Block
containing the whole program.
"""

from __future__ import annotations
from .tokens import Token, TokenKind
from . import ast


class ParseError(Exception):
    def __init__(self, message, line, col):
        super().__init__(f"{line}:{col}: {message}")
        self.message = message
        self.line = line
        self.col = col


# Binding power table for Pratt parsing. Higher binds tighter.
BINDING_POWER = {
    TokenKind.OR:   10, TokenKind.AND:  20,
    TokenKind.EQEQ: 30, TokenKind.NEQ:  30,
    TokenKind.LT:   40, TokenKind.LE:   40,
    TokenKind.GT:   40, TokenKind.GE:   40,
    TokenKind.PLUS: 50, TokenKind.MINUS:50,
    TokenKind.STAR: 60, TokenKind.SLASH:60,
    TokenKind.PERCENT: 60,
    TokenKind.POW:  70,
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.prev_line = 0

    # ---- token helpers ----------------------------------------------------
    def peek(self) -> Token:
        return self.tokens[self.pos]

    def peek_kind(self) -> TokenKind:
        return self.tokens[self.pos].kind

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def check(self, kind: TokenKind) -> bool:
        return self.peek_kind() == kind

    def match(self, *kinds) -> Token | None:
        if self.peek_kind() in kinds:
            return self.advance()
        return None

    def expect(self, kind: TokenKind, what: str) -> Token:
        if not self.check(kind):
            t = self.peek()
            raise ParseError(f"expected {what}, got {t.kind.name}", t.line, t.col)
        return self.advance()

    def skip_newlines(self):
        while self.check(TokenKind.NEWLINE):
            self.advance()

    # ---- program ----------------------------------------------------------
    def parse_program(self) -> ast.Block:
        stmts = []
        self.skip_newlines()
        while not self.check(TokenKind.EOF):
            stmts.append(self.statement())
            self.skip_newlines()
        return ast.Block(statements=stmts, line=1, col=1)

    # ---- statements -------------------------------------------------------
    def statement(self) -> ast.Node:
        self.skip_newlines()
        t = self.peek()
        k = t.kind

        if k == TokenKind.KW_DEF:   return self.function_def(async_=False)
        if k == TokenKind.KW_ASYNC: return self.async_statement()
        if k == TokenKind.KW_CLASS: return self.class_def()
        if k == TokenKind.KW_IF:    return self.if_statement()
        if k == TokenKind.KW_WHILE: return self.while_statement()
        if k == TokenKind.KW_FOR:   return self.for_statement()
        if k == TokenKind.KW_RETURN:return self.return_statement()
        if k == TokenKind.KW_TRY:   return self.try_statement()
        if k == TokenKind.KW_THROW: return self.throw_statement()
        if k in (TokenKind.KW_LET, TokenKind.KW_CONST, TokenKind.KW_VAR):
            return self.explicit_binding()

        # implicit binding:  name = expr
        if k == TokenKind.IDENT and self.tokens[self.pos + 1].kind == TokenKind.EQ:
            name_tok = self.advance()
            self.advance()  # '='
            value = self.expression(0)
            self.expect(TokenKind.NEWLINE, "end of statement")
            return ast.Binding("implicit", name_tok.value, value,
                               line=name_tok.line, col=name_tok.col)

        expr = self.expression(0)
        self.expect(TokenKind.NEWLINE, "end of statement")
        return ast.ExprStmt(expr=expr, line=expr.line, col=expr.col)

    def explicit_binding(self) -> ast.Binding:
        kw = self.advance()
        kind = kw.value if kw.value else kw.kind.name[3:].lower()
        name_tok = self.expect(TokenKind.IDENT, "binding name")
        self.expect(TokenKind.EQ, "'='")
        value = self.expression(0)
        self.expect(TokenKind.NEWLINE, "end of statement")
        return ast.Binding(kind, name_tok.value, value,
                           line=kw.line, col=kw.col)

    def function_def(self, async_=False) -> ast.FunctionDef:
        self.advance()  # 'def'
        name_tok = self.expect(TokenKind.IDENT, "function name")
        self.expect(TokenKind.LPAREN, "'('")
        params = []
        if not self.check(TokenKind.RPAREN):
            while True:
                params.append(self.expect(TokenKind.IDENT, "parameter").value)
                if not self.match(TokenKind.COMMA):
                    break
        self.expect(TokenKind.RPAREN, "')'")
        if self.match(TokenKind.ARROW):
            # return type annotation - consume a type expression loosely
            self.consume_type_annotation()
        self.expect(TokenKind.COLON, "':'")
        body = self.suite()
        return ast.FunctionDef(name_tok.value, params, body, async_,
                               line=name_tok.line, col=name_tok.col)

    def async_statement(self):
        self.advance()  # 'async'
        if self.check(TokenKind.KW_DEF):
            return self.function_def(async_=True)
        expr = self.expression(0)
        self.expect(TokenKind.NEWLINE, "end of statement")
        return ast.ExprStmt(expr=expr, line=expr.line, col=expr.col)

    def class_def(self) -> ast.ClassDef:
        kw = self.advance()
        name_tok = self.expect(TokenKind.IDENT, "class name")
        bases = []
        if self.match(TokenKind.LPAREN):
            if not self.check(TokenKind.RPAREN):
                while True:
                    bases.append(self.expect(TokenKind.IDENT, "base class").value)
                    if not self.match(TokenKind.COMMA):
                        break
            self.expect(TokenKind.RPAREN, "')'")
        self.expect(TokenKind.COLON, "':'")
        body = self.suite()
        return ast.ClassDef(name_tok.value, bases, body,
                            line=kw.line, col=kw.col)

    def if_statement(self) -> ast.If:
        kw = self.advance()
        cond = self.expression(0)
        self.expect(TokenKind.COLON, "':'")
        then_branch = self.suite()
        elifs = []
        else_branch = None
        self.skip_newlines_soft()
        while self.check(TokenKind.KW_ELIF):
            self.advance()
            ec = self.expression(0)
            self.expect(TokenKind.COLON, "':'")
            elifs.append((ec, self.suite()))
            self.skip_newlines_soft()
        if self.check(TokenKind.KW_ELSE):
            self.advance()
            self.expect(TokenKind.COLON, "':'")
            else_branch = self.suite()
        return ast.If(cond, then_branch, elifs, else_branch,
                      line=kw.line, col=kw.col)

    def while_statement(self) -> ast.While:
        kw = self.advance()
        cond = self.expression(0)
        self.expect(TokenKind.COLON, "':'")
        body = self.suite()
        return ast.While(cond, body, line=kw.line, col=kw.col)

    def for_statement(self) -> ast.For:
        kw = self.advance()
        name_tok = self.expect(TokenKind.IDENT, "loop variable")
        self.expect(TokenKind.KW_IN, "'in'")
        iterable = self.expression(0)
        self.expect(TokenKind.COLON, "':'")
        body = self.suite()
        return ast.For(name_tok.value, iterable, body,
                       line=kw.line, col=kw.col)

    def return_statement(self) -> ast.Return:
        kw = self.advance()
        value = None
        if not self.check(TokenKind.NEWLINE):
            value = self.expression(0)
        self.expect(TokenKind.NEWLINE, "end of statement")
        return ast.Return(value, line=kw.line, col=kw.col)

    def try_statement(self) -> ast.Try:
        kw = self.advance()
        self.expect(TokenKind.COLON, "':'")
        body = self.suite()
        except_var, except_body, finally_body = None, None, None
        self.skip_newlines_soft()
        if self.check(TokenKind.KW_EXCEPT):
            self.advance()
            if self.check(TokenKind.IDENT):
                except_var = self.advance().value
            self.expect(TokenKind.COLON, "':'")
            except_body = self.suite()
            self.skip_newlines_soft()
        if self.check(TokenKind.KW_FINALLY):
            self.advance()
            self.expect(TokenKind.COLON, "':'")
            finally_body = self.suite()
        return ast.Try(body, except_var, except_body, finally_body,
                       line=kw.line, col=kw.col)

    def throw_statement(self) -> ast.Throw:
        kw = self.advance()
        expr = self.expression(0)
        self.expect(TokenKind.NEWLINE, "end of statement")
        return ast.Throw(expr, line=kw.line, col=kw.col)

    def suite(self) -> ast.Block:
        """Parse an indented block (with INDENT/DEDENT) after a ':'."""
        self.expect(TokenKind.NEWLINE, "newline after ':'")
        self.expect(TokenKind.INDENT, "indented block")
        stmts = []
        while not self.check(TokenKind.DEDENT) and not self.check(TokenKind.EOF):
            stmts.append(self.statement())
            self.skip_newlines()
        self.match(TokenKind.DEDENT)
        return ast.Block(statements=stmts, line=self.peek().line, col=self.peek().col)

    def skip_newlines_soft(self):
        while self.check(TokenKind.NEWLINE):
            self.advance()

    def consume_type_annotation(self):
        """Loose consumption of a type expression after '->' or ':'."""
        depth = 0
        while self.pos < len(self.tokens):
            k = self.peek_kind()
            if k in (TokenKind.LBRACKET, TokenKind.LPAREN, TokenKind.LBRACE):
                depth += 1
            elif k in (TokenKind.RBRACKET, TokenKind.RPAREN, TokenKind.RBRACE):
                if depth == 0:
                    return
                depth -= 1
            elif k in (TokenKind.COLON, TokenKind.EQ, TokenKind.NEWLINE) and depth == 0:
                return
            self.advance()

    # ---- expressions (Pratt) ---------------------------------------------
    def expression(self, min_bp: int) -> ast.Node:
        left = self.prefix()
        while True:
            k = self.peek_kind()
            bp = BINDING_POWER.get(k, 0)
            if bp <= min_bp:
                break
            op_tok = self.advance()
            right = self.expression(bp)
            left = ast.BinaryOp(op_tok.value, left, right,
                                line=op_tok.line, col=op_tok.col)
        return left

    def prefix(self) -> ast.Node:
        t = self.peek()

        if t.kind == TokenKind.NUMBER:
            self.advance()
            return ast.Literal(t.value, line=t.line, col=t.col)

        if t.kind == TokenKind.STRING:
            self.advance()
            return ast.Literal(t.value, line=t.line, col=t.col)

        if t.kind == TokenKind.KW_TRUE:
            self.advance()
            return ast.Literal(True, line=t.line, col=t.col)

        if t.kind == TokenKind.KW_FALSE:
            self.advance()
            return ast.Literal(False, line=t.line, col=t.col)

        if t.kind == TokenKind.KW_NULL:
            self.advance()
            return ast.Literal(None, line=t.line, col=t.col)

        if t.kind == TokenKind.NOT:
            self.advance()
            operand = self.expression(75)
            return ast.UnaryOp("!", operand, line=t.line, col=t.col)

        if t.kind == TokenKind.MINUS:
            self.advance()
            operand = self.expression(75)
            return ast.UnaryOp("-", operand, line=t.line, col=t.col)

        if t.kind == TokenKind.KW_AWAIT:
            self.advance()
            expr = self.expression(75)
            return ast.Await(expr, line=t.line, col=t.col)

        if t.kind == TokenKind.IDENT:
            self.advance()
            node: ast.Node = ast.Identifier(t.value, line=t.line, col=t.col)
            return self.postfix(node)

        if t.kind == TokenKind.LPAREN:
            self.advance()
            # lambda: (a, b) => expr
            save = self.pos
            params = self.try_parse_lambda_params()
            if params is not None:
                return ast.Lambda(params, self.expression(0),
                                  line=t.line, col=t.col)
            self.pos = save
            inner = self.expression(0)
            self.expect(TokenKind.RPAREN, "')'")
            return self.postfix(inner)

        if t.kind == TokenKind.LBRACKET:
            self.advance()
            items = []
            if not self.check(TokenKind.RBRACKET):
                while True:
                    items.append(self.expression(0))
                    if not self.match(TokenKind.COMMA):
                        break
            self.expect(TokenKind.RBRACKET, "']'")
            return ast.Literal(items, line=t.line, col=t.col)

        raise ParseError(f"unexpected token {t.kind.name}", t.line, t.col)

    def try_parse_lambda_params(self):
        """Inside '(', try to match 'ident (, ident)* ) =>'."""
        params = []
        save = self.pos
        try:
            if not self.check(TokenKind.RPAREN):
                while True:
                    if not self.check(TokenKind.IDENT):
                        self.pos = save
                        return None
                    params.append(self.advance().value)
                    if not self.match(TokenKind.COMMA):
                        break
            if not self.check(TokenKind.RPAREN):
                self.pos = save; return None
            self.advance()
            if not self.check(TokenKind.ARROW):
                self.pos = save; return None
            self.advance()  # '=>'
            return params
        except ParseError:
            self.pos = save
            return None

    def postfix(self, node: ast.Node) -> ast.Node:
        while True:
            t = self.peek()
            if t.kind == TokenKind.LPAREN:
                self.advance()
                args = []
                if not self.check(TokenKind.RPAREN):
                    while True:
                        args.append(self.expression(0))
                        if not self.match(TokenKind.COMMA):
                            break
                self.expect(TokenKind.RPAREN, "')'")
                node = ast.Call(node, args, line=t.line, col=t.col)
            elif t.kind == TokenKind.DOT:
                self.advance()
                name_tok = self.expect(TokenKind.IDENT, "member name")
                node = ast.Member(node, name_tok.value,
                                  line=name_tok.line, col=name_tok.col)
            elif t.kind == TokenKind.LBRACKET:
                self.advance()
                key = self.expression(0)
                self.expect(TokenKind.RBRACKET, "']'")
                node = ast.Index(node, key, line=t.line, col=t.col)
            else:
                return node


def parse(tokens: list[Token]) -> ast.Block:
    return Parser(tokens).parse_program()
