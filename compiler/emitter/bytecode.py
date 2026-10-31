"""
JapyScript — bytecode definitions.

A `.jpc` module is a `CodeObject` serialised to disk. CodeObjects contain a
list of Instructions and a constant pool. Instructions are fixed-width tuples
(op, arg, line) for fast dispatch in the VM.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class Op(Enum):
    # stack
    LOAD_CONST     = auto()
    LOAD_NAME      = auto()
    STORE_NAME     = auto()
    POP            = auto()
    DUP            = auto()

    # arithmetic / logic
    BINARY         = auto()
    UNARY          = auto()

    # control flow
    JUMP           = auto()
    JUMP_IF_FALSE  = auto()
    JUMP_IF_TRUE   = auto()

    # iteration
    GET_ITER       = auto()
    FOR_ITER       = auto()

    # functions
    MAKE_FUNCTION  = auto()
    CALL           = auto()
    RETURN         = auto()

    # objects
    MAKE_CLASS     = auto()
    GET_ATTR       = auto()
    SET_ATTR       = auto()
    GET_INDEX      = auto()
    SET_INDEX      = auto()
    BUILD_LIST     = auto()
    BUILD_DICT     = auto()

    # exceptions
    SETUP_EXCEPT   = auto()
    POP_EXCEPT     = auto()
    THROW          = auto()

    # async
    AWAIT          = auto()

    # builtins / lifecycle
    PRINT          = auto()
    HALT           = auto()


# Opcodes that carry no argument
NO_ARG_OPS = {
    Op.POP, Op.DUP, Op.RETURN, Op.HALT,
    Op.GET_ITER, Op.GET_INDEX,
    Op.SETUP_EXCEPT, Op.POP_EXCEPT,
    Op.PRINT, Op.AWAIT, Op.THROW,
}


@dataclass
class Instr:
    op: Op
    arg: Any = None
    line: int = 0

    def __repr__(self):
        if self.arg is None:
            return f"{self.op.name}"
        return f"{self.op.name} {self.arg!r}"


@dataclass
class CodeObject:
    name: str
    params: list[str]
    instructions: list[Instr]
    constants: list[Any]
    is_async: bool = False

    def __repr__(self):
        return f"<CodeObject {self.name} params={self.params} instrs={len(self.instructions)}>"


def disassemble(code: CodeObject) -> str:
    """Return a human-readable disassembly of a CodeObject."""
    lines = [f"; code object: {code.name}"]
    lines.append(f"; params:      {code.params}")
    lines.append(f"; constants:   {len(code.constants)}")
    lines.append("")
    for i, instr in enumerate(code.instructions):
        lines.append(f"  {i:4d}  {instr}")
    return "\n".join(lines)
