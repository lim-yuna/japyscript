"""
JapyScript — static linter.

Rules:
  W101  unused binding
  W102  shadowing (binding duplicates an earlier binding)
"""

from __future__ import annotations
from compiler import ast
from compiler.parser import parse, ParseError
from compiler.lexer import tokenize, LexerError


class Diagnostic:
    def __init__(self, code: str, message: str, line: int, col: int, severity="warning"):
        self.code = code
        self.message = message
        self.line = line
        self.col = col
        self.severity = severity

    def __repr__(self):
        return f"{self.line}:{self.col}  {self.severity} {self.code}: {self.message}"


class Linter:
    def __init__(self):
        self.diagnostics: list[Diagnostic] = []
        self.declared: dict[str, list] = {}
        self.used: dict[str, int] = {}

    def report(self, code, message, node, severity="warning"):
        self.diagnostics.append(
            Diagnostic(code, message, node.line, node.col, severity))

    def lint_program(self, program):
        for stmt in program.statements:
            self.lint_stmt(stmt)
        self.check_unused()

    def lint_stmt(self, node):
        if isinstance(node, ast.Binding):
            self.declared.setdefault(node.name, []).append(node)
            self.lint_expr(node.value)

        elif isinstance(node, ast.ExprStmt):
            self.lint_expr(node.expr)

        elif isinstance(node, ast.Return):
            if node.value is not None:
                self.lint_expr(node.value)

        elif isinstance(node, ast.FunctionDef):
            self.declared.setdefault(node.name, []).append(node)
            for p in node.params:
                self.declared.setdefault(p, []).append(node)
            for s in node.body.statements:
                self.lint_stmt(s)

        elif isinstance(node, ast.ClassDef):
            self.declared.setdefault(node.name, []).append(node)
            for s in node.body.statements:
                self.lint_stmt(s)

        elif isinstance(node, ast.If):
            self.lint_expr(node.condition)
            self.lint_block(node.then_branch)
            for cond, block in node.elifs:
                self.lint_expr(cond)
                self.lint_block(block)
            if node.else_branch is not None:
                self.lint_block(node.else_branch)

        elif isinstance(node, ast.While):
            self.lint_expr(node.condition)
            self.lint_block(node.body)

        elif isinstance(node, ast.For):
            self.declared.setdefault(node.name, []).append(node)
            self.lint_expr(node.iterable)
            self.lint_block(node.body)

        elif isinstance(node, ast.Try):
            self.lint_block(node.body)
            if node.except_var:
                self.declared.setdefault(node.except_var, []).append(node)
            if node.except_body is not None:
                self.lint_block(node.except_body)
            if node.finally_body is not None:
                self.lint_block(node.finally_body)

        elif isinstance(node, ast.Throw):
            self.lint_expr(node.expr)

    def lint_block(self, block):
        for s in block.statements:
            self.lint_stmt(s)

    def lint_expr(self, node):
        if isinstance(node, ast.Identifier):
            self.used[node.name] = self.used.get(node.name, 0) + 1

        elif isinstance(node, ast.BinaryOp):
            self.lint_expr(node.left)
            self.lint_expr(node.right)

        elif isinstance(node, ast.UnaryOp):
            self.lint_expr(node.operand)

        elif isinstance(node, ast.Call):
            self.lint_expr(node.callee)
            for a in node.args:
                self.lint_expr(a)

        elif isinstance(node, ast.Member):
            self.lint_expr(node.obj)

        elif isinstance(node, ast.Index):
            self.lint_expr(node.obj)
            self.lint_expr(node.key)

        elif isinstance(node, ast.Lambda):
            for p in node.params:
                self.declared.setdefault(p, []).append(node)
            self.lint_expr(node.body)

        elif isinstance(node, ast.Await):
            self.lint_expr(node.expr)

    def check_unused(self):
        BUILTINS = {
            "print", "len", "range", "str", "int", "float", "bool", "type",
            "true", "false", "null",
        }
        for name, nodes in self.declared.items():
            if name in BUILTINS:
                continue
            if name.startswith("_"):
                continue
            if self.used.get(name, 0) == 0:
                node = nodes[0]
                self.report("W101", f"unused binding: {name}", node)

    def report_double(self):
        for name, nodes in self.declared.items():
            if name.startswith("_"):
                continue
            if len(nodes) > 1:
                node = nodes[1]
                self.report("W102",
                            f"binding '{name}' shadows an earlier binding",
                            node)


def lint_source(source: str, filename: str = "<input>") -> list[Diagnostic]:
    try:
        tokens = tokenize(source, filename)
        program = parse(tokens)
    except (LexerError, ParseError) as e:
        return [Diagnostic("E100", str(e), 0, 0, severity="error")]
    linter = Linter()
    linter.lint_program(program)
    linter.report_double()
    return linter.diagnostics


def format_diagnostics(diags: list[Diagnostic], filename: str) -> str:
    if not diags:
        return f"{filename}: clean"
    lines = [f"{filename}:"]
    for d in diags:
        lines.append(f"  {d}")
    return "\n".join(lines)
