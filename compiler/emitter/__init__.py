"""
JapyScript — bytecode emitter.

Walks the AST and produces a CodeObject per function, plus a top-level
`<module>` CodeObject. Constants are pooled per module.
"""

from __future__ import annotations
from .. import ast
from .bytecode import Op, Instr, CodeObject


class EmitError(Exception):
    pass


class Emitter:
    def __init__(self):
        self.instructions: list[Instr] = []
        self.constants: list = []
        self.pending_break: list[int] = []
        self.pending_continue: list[int] = []
        self.loop_starts: list[int] = []
        self.handler_stack: list[int] = []

    # ---- helpers ----------------------------------------------------------
    def emit(self, op: Op, arg=None, line=0) -> int:
        self.instructions.append(Instr(op, arg, line))
        return len(self.instructions) - 1

    def add_const(self, value) -> int:
        for i, c in enumerate(self.constants):
            if type(c) is type(value) and c == value:
                return i
        self.constants.append(value)
        return len(self.constants) - 1

    def here(self) -> int:
        return len(self.instructions)

    def patch(self, idx: int, target: int):
        self.instructions[idx].arg = target

    # ---- program ----------------------------------------------------------
    def compile_program(self, program: ast.Block) -> CodeObject:
        for stmt in program.statements:
            self.compile_stmt(stmt)
        self.emit(Op.LOAD_CONST, self.add_const(None))
        self.emit(Op.HALT)
        return CodeObject(
            name="<module>",
            params=[],
            instructions=self.instructions,
            constants=self.constants,
        )

    # ---- statements -------------------------------------------------------
    def compile_stmt(self, node: ast.Node):
        if isinstance(node, ast.Binding):
            self.compile_expr(node.value)
            self.emit(Op.STORE_NAME, node.name, node.line)

        elif isinstance(node, ast.ExprStmt):
            self.compile_expr(node.expr)
            self.emit(Op.POP, line=node.line)

        elif isinstance(node, ast.Return):
            if node.value is not None:
                self.compile_expr(node.value)
            else:
                self.emit(Op.LOAD_CONST, self.add_const(None), node.line)
            self.emit(Op.RETURN, line=node.line)

        elif isinstance(node, ast.FunctionDef):
            inner = Emitter()
            for stmt in node.body.statements:
                inner.compile_stmt(stmt)
            inner.emit(Op.LOAD_CONST, inner.add_const(None))
            inner.emit(Op.RETURN)
            fn_code = CodeObject(
                name=node.name,
                params=node.params,
                instructions=inner.instructions,
                constants=inner.constants,
                is_async=node.is_async,
            )
            idx = self.emit(Op.MAKE_FUNCTION, fn_code, node.line)
            self.emit(Op.STORE_NAME, node.name, node.line)

        elif isinstance(node, ast.If):
            self.compile_if(node)

        elif isinstance(node, ast.While):
            self.compile_while(node)

        elif isinstance(node, ast.For):
            self.compile_for(node)

        elif isinstance(node, ast.Try):
            self.compile_try(node)

        elif isinstance(node, ast.Throw):
            self.compile_expr(node.expr)
            self.emit(Op.THROW, line=node.line)

        elif isinstance(node, ast.ClassDef):
            self.compile_expr(
                ast.Literal("<class-body>", line=node.line, col=node.col)
            )
            self.emit(Op.MAKE_CLASS, (node.name, node.bases), node.line)
            self.emit(Op.STORE_NAME, node.name, node.line)

    def compile_if(self, node: ast.If):
        self.compile_expr(node.condition)
        end_jumps: list[int] = []
        jif_false = self.emit(Op.JUMP_IF_FALSE, None, node.line)
        for s in node.then_branch.statements:
            self.compile_stmt(s)
        end_jumps.append(self.emit(Op.JUMP, None, node.line))
        self.patch(jif_false, self.here())

        for cond, block in node.elifs:
            self.compile_expr(cond)
            jf = self.emit(Op.JUMP_IF_FALSE, None, cond.line)
            for s in block.statements:
                self.compile_stmt(s)
            end_jumps.append(self.emit(Op.JUMP, None, cond.line))
            self.patch(jf, self.here())

        if node.else_branch is not None:
            for s in node.else_branch.statements:
                self.compile_stmt(s)

        target = self.here()
        for idx in end_jumps:
            self.patch(idx, target)

    def compile_while(self, node: ast.While):
        start = self.here()
        self.compile_expr(node.condition)
        jif = self.emit(Op.JUMP_IF_FALSE, None, node.line)
        prev_breaks = self.pending_break
        prev_continues = self.pending_continue
        self.pending_break = []
        self.pending_continue = []
        for s in node.body.statements:
            self.compile_stmt(s)
        jump_back = self.emit(Op.JUMP, start, node.line)
        # continue jumps target start (condition is re-evaluated)
        for idx in self.pending_continue:
            self.patch(idx, start)
        end = self.here()
        self.patch(jif, end)
        for idx in self.pending_break:
            self.patch(idx, end)
        self.pending_break = prev_breaks
        self.pending_continue = prev_continues

    def compile_for(self, node: ast.For):
        self.compile_expr(node.iterable)
        self.emit(Op.GET_ITER, line=node.line)
        start = self.here()
        for_iter = self.emit(Op.FOR_ITER, None, node.line)
        self.emit(Op.STORE_NAME, node.name, node.line)
        prev_breaks = self.pending_break
        prev_continues = self.pending_continue
        self.pending_break = []
        self.pending_continue = []
        for s in node.body.statements:
            self.compile_stmt(s)
        self.emit(Op.JUMP, start, node.line)
        end = self.here()
        self.patch(for_iter, end)
        for idx in self.pending_continue:
            self.patch(idx, start)
        for idx in self.pending_break:
            self.patch(idx, end)
        self.pending_break = prev_breaks
        self.pending_continue = prev_continues

    def compile_try(self, node: ast.Try):
        setup = self.emit(Op.SETUP_EXCEPT, None, node.line)
        for s in node.body.statements:
            self.compile_stmt(s)
        self.emit(Op.POP_EXCEPT)
        skip = self.emit(Op.JUMP, None, node.line)
        handler_start = self.here()
        self.patch(setup, handler_start)

        if node.except_body is not None:
            if node.except_var:
                self.emit(Op.STORE_NAME, node.except_var, node.line)
            else:
                self.emit(Op.POP)
            for s in node.except_body.statements:
                self.compile_stmt(s)

        after = self.here()
        self.patch(skip, after)

        if node.finally_body is not None:
            for s in node.finally_body.statements:
                self.compile_stmt(s)

    # ---- expressions ------------------------------------------------------
    def compile_expr(self, node: ast.Node):
        if isinstance(node, ast.Literal):
            self.emit(Op.LOAD_CONST, self.add_const(node.value), node.line)

        elif isinstance(node, ast.Identifier):
            self.emit(Op.LOAD_NAME, node.name, node.line)

        elif isinstance(node, ast.BinaryOp):
            self.compile_expr(node.left)
            self.compile_expr(node.right)
            self.emit(Op.BINARY, node.op, node.line)

        elif isinstance(node, ast.UnaryOp):
            self.compile_expr(node.operand)
            self.emit(Op.UNARY, node.op, node.line)

        elif isinstance(node, ast.Call):
            self.compile_expr(node.callee)
            for a in node.args:
                self.compile_expr(a)
            self.emit(Op.CALL, len(node.args), node.line)

        elif isinstance(node, ast.Member):
            self.compile_expr(node.obj)
            self.emit(Op.GET_ATTR, node.name, node.line)

        elif isinstance(node, ast.Index):
            self.compile_expr(node.obj)
            self.compile_expr(node.key)
            self.emit(Op.GET_INDEX, line=node.line)

        elif isinstance(node, ast.Lambda):
            inner = Emitter()
            inner.compile_expr(node.body)
            inner.emit(Op.RETURN)
            fn_code = CodeObject(
                name="<lambda>",
                params=node.params,
                instructions=inner.instructions,
                constants=inner.constants,
            )
            self.emit(Op.MAKE_FUNCTION, fn_code, node.line)

        elif isinstance(node, ast.Await):
            self.compile_expr(node.expr)
            self.emit(Op.AWAIT, line=node.line)

        else:
            raise EmitError(f"cannot emit expression: {type(node).__name__}")
