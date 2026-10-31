"""
JapyScript — AST node definitions.

All nodes are immutable dataclasses. Every node records its source location.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class Node:
    line: int = 0
    col: int = 0


# ---- expressions ----------------------------------------------------------
@dataclass(frozen=True)
class Literal(Node):
    value: Any = None


@dataclass(frozen=True)
class Identifier(Node):
    name: str = ""


@dataclass(frozen=True)
class BinaryOp(Node):
    op: str = ""
    left: Node = None
    right: Node = None


@dataclass(frozen=True)
class UnaryOp(Node):
    op: str = ""
    operand: Node = None


@dataclass(frozen=True)
class Call(Node):
    callee: Node = None
    args: List[Node] = field(default_factory=list)


@dataclass(frozen=True)
class Member(Node):
    obj: Node = None
    name: str = ""


@dataclass(frozen=True)
class Index(Node):
    obj: Node = None
    key: Node = None


@dataclass(frozen=True)
class Lambda(Node):
    params: List[str] = field(default_factory=list)
    body: Node = None


@dataclass(frozen=True)
class Await(Node):
    expr: Node = None


# ---- statements -----------------------------------------------------------
@dataclass(frozen=True)
class Block(Node):
    statements: List[Node] = field(default_factory=list)


@dataclass(frozen=True)
class Binding(Node):
    kind: str = "let"     # "let" | "const" | "var" | "implicit"
    name: str = ""
    value: Node = None


@dataclass(frozen=True)
class ExprStmt(Node):
    expr: Node = None


@dataclass(frozen=True)
class Return(Node):
    value: Optional[Node] = None


@dataclass(frozen=True)
class If(Node):
    condition: Node = None
    then_branch: Node = None
    elifs: List[tuple] = field(default_factory=list)
    else_branch: Optional[Node] = None


@dataclass(frozen=True)
class While(Node):
    condition: Node = None
    body: Node = None


@dataclass(frozen=True)
class For(Node):
    name: str = ""
    iterable: Node = None
    body: Node = None


@dataclass(frozen=True)
class FunctionDef(Node):
    name: str = ""
    params: List[str] = field(default_factory=list)
    body: Node = None
    is_async: bool = False


@dataclass(frozen=True)
class ClassDef(Node):
    name: str = ""
    bases: List[str] = field(default_factory=list)
    body: Block = None


@dataclass(frozen=True)
class Try(Node):
    body: Node = None
    except_var: Optional[str] = None
    except_body: Optional[Node] = None
    finally_body: Optional[Node] = None


@dataclass(frozen=True)
class Throw(Node):
    expr: Node = None
