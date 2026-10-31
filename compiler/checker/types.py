"""
JapyScript — type system primitives.

Types are represented as immutable values. `unify(a, b)` computes the least
upper bound of two types — the type of an expression that could be either.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Type:
    name: str

    def __repr__(self):
        return self.name


INT    = Type("int")
FLOAT  = Type("float")
STRING = Type("string")
BOOL   = Type("bool")
NULL   = Type("null")
BYTES  = Type("bytes")
ANY    = Type("any")
NEVER  = Type("never")


def unify(a: Type, b: Type) -> Type:
    """Least upper bound of two types."""
    if a == b:
        return a
    if a == ANY or b == ANY:
        return ANY
    if a == NEVER:
        return b
    if b == NEVER:
        return a
    if (a == INT and b == FLOAT) or (a == FLOAT and b == INT):
        return FLOAT
    return ANY


def from_literal(value) -> Type:
    if isinstance(value, bool):
        return BOOL
    if isinstance(value, int):
        return INT
    if isinstance(value, float):
        return FLOAT
    if isinstance(value, str):
        return STRING
    if value is None:
        return NULL
    return ANY


def is_numeric(t: Type) -> bool:
    return t in (INT, FLOAT)


def is_assignable(src: Type, dst: Type) -> bool:
    if dst == ANY or src == ANY:
        return True
    if src == dst:
        return True
    if src == INT and dst == FLOAT:
        return True
    return False
