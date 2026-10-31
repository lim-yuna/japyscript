"""
JapyScript — static checker.

Performs name resolution and optional type inference. Untyped programs pass
through unchanged; only declarations that introduce types are checked.

A program that fails the checker does not reach the emitter.
"""

from __future__ import annotations
from .. import ast
from . import types as T


class CheckError(Exception):
    def __init__(self, messages):
        if isinstance(messages, str):
            messages = [messages]
        self.messages = messages
        super().__init__("\n".join(messages))


class Checker:
    def __init__(self):
        self.scopes: list[dict[str, T.Type]] = [{}]
        self.errors: list[str] = []
        self.functions: dict[str, T.Type] = {}

    # ---- scope handling ---------------------------------------------------
    def push(self):
        self.scopes.append({})

    def pop(self):
        self.scopes.pop()

    def declare(self, name: str, ty: T.Type):
        self.scopes[-1][name] = ty

    def lookup(self, name: str) -> T.Type:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return T.ANY

    def report(self, node: ast.Node, message: str):
        self.errors.append(f"{node.line}:{node.col}: {message}")

    # ---- program ----------------------------------------------------------
    def check_program(self, program: ast.Block):
        for stmt in program.statements:
            self.check_stmt(stmt)
        if self.errors:
            raise CheckError(self.errors)

    # ---- statements -------------------------------------------------------
    def check_stmt(self, node: ast.Node):
        if isinstance(node, ast.Binding):
            t = self.infer(node.value)
            self.declare(node.name, t)

        elif isinstance(node, ast.FunctionDef):
            self.declare(node.name, T.ANY)
            self.push()
            for p in node.params:
                self.declare(p, T.ANY)
            for s in node.body.statements:
                self.check_stmt(s)
            self.pop()

        elif isinstance(node, ast.ClassDef):
            self.declare(node.name, T.ANY)
            self.push()
            for s in node.body.statements:
                self.check_stmt(s)
            self.pop()

        elif isinstance(node, ast.If):
            self.infer(node.condition)
            self.check_block(node.then_branch)
            for cond, block in node.elifs:
                self.infer(cond)
                self.check_block(block)
            if node.else_branch is not None:
                self.check_block(node.else_branch)

        elif isinstance(node, ast.While):
            self.infer(node.condition)
            self.check_block(node.body)

        elif isinstance(node, ast.For):
            self.push()
            self.declare(node.name, T.ANY)
            self.infer(node.iterable)
            for s in node.body.statements:
                self.check_stmt(s)
            self.pop()

        elif isinstance(node, ast.Try):
            self.check_block(node.body)
            if node.except_body is not None:
                self.push()
                if node.except_var:
                    self.declare(node.except_var, T.ANY)
                for s in node.except_body.statements:
                    self.check_stmt(s)
                self.pop()
            if node.finally_body is not None:
                self.check_block(node.finally_body)

        elif isinstance(node, ast.Throw):
            self.infer(node.expr)

        elif isinstance(node, ast.ExprStmt):
            self.infer(node.expr)

        elif isinstance(node, ast.Return):
            if node.value is not None:
                self.infer(node.value)

    def check_block(self, block: ast.Block):
        self.push()
        for s in block.statements:
            self.check_stmt(s)
        self.pop()

    # ---- expressions ------------------------------------------------------
    def infer(self, node: ast.Node) -> T.Type:
        if isinstance(node, ast.Literal):
            return T.from_literal(node.value)

        if isinstance(node, ast.Identifier):
            return self.lookup(node.name)

        if isinstance(node, ast.BinaryOp):
            lt = self.infer(node.left)
            rt = self.infer(node.right)
            if node.op in ("+", "-", "*", "/", "%", "**"):
                return T.unify(lt, rt)
            if node.op in ("==", "!=", "<", "<=", ">", ">=", "is"):
                return T.BOOL
            if node.op in ("&&", "||", "and", "or"):
                return T.unify(lt, rt)
            return T.ANY

        if isinstance(node, ast.UnaryOp):
            if node.op == "!":
                self.infer(node.operand)
                return T.BOOL
            return self.infer(node.operand)

        if isinstance(node, ast.Call):
            self.infer(node.callee)
            for a in node.args:
                self.infer(a)
            return T.ANY

        if isinstance(node, ast.Member):
            self.infer(node.obj)
            return T.ANY

        if isinstance(node, ast.Index):
            self.infer(node.obj)
            self.infer(node.key)
            return T.ANY

        if isinstance(node, ast.Lambda):
            self.push()
            for p in node.params:
                self.declare(p, T.ANY)
            self.infer(node.body)
            self.pop()
            return T.ANY

        if isinstance(node, ast.Await):
            self.infer(node.expr)
            return T.ANY

        return T.ANY


def check(program: ast.Block):
    Checker().check_program(program)
