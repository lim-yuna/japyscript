"""
JapyScript — virtual machine.

A stack machine. Bytecode is a list of Instr; execution is a dispatch loop.
Functions are closures capturing the module globals. Exceptions use a
per-frame handler stack.
"""

from __future__ import annotations
from compiler.emitter.bytecode import Op, CodeObject


class JpyError(Exception):
    pass


class JpyRuntimeError(JpyError):
    def __init__(self, message, line=0):
        super().__init__(f"{line}: {message}" if line else message)
        self.message = message
        self.line = line


class JpyFunction:
    def __init__(self, code: CodeObject, globals_env: dict, name=None):
        self.code = code
        self.globals = globals_env
        self.name = name or code.name

    def __repr__(self):
        return f"<function {self.name} params={len(self.code.params)}>"


class Frame:
    def __init__(self, code: CodeObject, globals_env: dict, locals_env=None):
        self.code = code
        self.ip = 0
        self.stack: list = []
        self.locals = locals_env if locals_env is not None else {}
        self.globals = globals_env
        self.handlers: list[int] = []


# ---- builtins ------------------------------------------------------------
def _b_print(*args):
    print(*args)
    return None

def _b_len(x):
    return len(x)

def _b_range(*args):
    return list(range(*args))

def _b_str(x):
    return str(x)

def _b_int(x):
    return int(x)

def _b_float(x):
    return float(x)

def _b_bool(x):
    return bool(x)

def _b_type(x):
    if x is None:
        return "null"
    return type(x).__name__


BUILTINS = {
    "print": _b_print,
    "len":   _b_len,
    "range": _b_range,
    "str":   _b_str,
    "int":   _b_int,
    "float": _b_float,
    "bool":  _b_bool,
    "type":  _b_type,
}


def _truthy(v):
    if v is None: return False
    if v is False: return False
    if isinstance(v, (int, float)) and v == 0: return False
    if isinstance(v, str) and v == "": return False
    if isinstance(v, (list, dict)) and len(v) == 0: return False
    return True


# ---- the VM --------------------------------------------------------------
class VM:
    def __init__(self, globals_env: dict | None = None):
        self.globals = globals_env if globals_env is not None else dict(BUILTINS)
        self.frames: list[Frame] = []
        self.last_value = None

    def run(self, code: CodeObject):
        frame = Frame(code, self.globals)
        self.frames.append(frame)
        try:
            self._loop()
        finally:
            self.frames.clear()
        return self.last_value

    # ---- dispatch loop ----------------------------------------------------
    def _loop(self):
        while self.frames:
            frame = self.frames[-1]
            if frame.ip >= len(frame.code.instructions):
                # implicit return
                self.frames.pop()
                if self.frames:
                    self.frames[-1].stack.append(None)
                else:
                    return
                continue

            instr = frame.code.instructions[frame.ip]
            frame.ip += 1
            try:
                self._execute(frame, instr)
            except JpyRuntimeError as e:
                self._handle_exception(frame, e)
            except Exception as e:
                self._handle_exception(frame, JpyRuntimeError(str(e), instr.line))

    def _handle_exception(self, frame, err):
        if frame.handlers:
            target = frame.handlers.pop()
            # trim stack to a known safe depth (we don't track it exactly;
            # conservatively trim to the marker that was pushed at setup)
            frame.stack = frame.stack[: -1] if frame.stack else []
            frame.stack.append(str(err))
            frame.ip = target
            return
        raise err

    def _execute(self, frame: Frame, instr):
        op = instr.op

        if op == Op.LOAD_CONST:
            frame.stack.append(frame.code.constants[instr.arg])

        elif op == Op.LOAD_NAME:
            name = instr.arg
            if name in frame.locals:
                frame.stack.append(frame.locals[name])
            elif name in self.globals:
                frame.stack.append(self.globals[name])
            elif name in BUILTINS:
                frame.stack.append(BUILTINS[name])
            else:
                raise JpyRuntimeError(f"undefined name: {name}", instr.line)

        elif op == Op.STORE_NAME:
            frame.locals[instr.arg] = frame.stack.pop()

        elif op == Op.POP:
            if frame.stack:
                frame.stack.pop()

        elif op == Op.DUP:
            frame.stack.append(frame.stack[-1])

        elif op == Op.BINARY:
            right = frame.stack.pop()
            left = frame.stack.pop()
            frame.stack.append(self._binary(instr.arg, left, right, instr.line))

        elif op == Op.UNARY:
            v = frame.stack.pop()
            if instr.arg == "!":
                frame.stack.append(not _truthy(v))
            elif instr.arg == "-":
                frame.stack.append(-v)
            else:
                raise JpyRuntimeError(f"bad unary op: {instr.arg}", instr.line)

        elif op == Op.JUMP:
            frame.ip = instr.arg

        elif op == Op.JUMP_IF_FALSE:
            v = frame.stack.pop()
            if not _truthy(v):
                frame.ip = instr.arg

        elif op == Op.JUMP_IF_TRUE:
            v = frame.stack.pop()
            if _truthy(v):
                frame.ip = instr.arg

        elif op == Op.GET_ITER:
            v = frame.stack.pop()
            frame.stack.append(iter(v))

        elif op == Op.FOR_ITER:
            it = frame.stack[-1]
            try:
                nxt = next(it)
            except StopIteration:
                frame.stack.pop()
                frame.ip = instr.arg
                return
            frame.stack.append(nxt)

        elif op == Op.MAKE_FUNCTION:
            code = instr.arg
            frame.stack.append(JpyFunction(code, self.globals))

        elif op == Op.CALL:
            argc = instr.arg
            args = [frame.stack.pop() for _ in range(argc)][::-1]
            callee = frame.stack.pop()
            if isinstance(callee, JpyFunction):
                self._call_function(callee, args)
            elif callable(callee):
                frame.stack.append(callee(*args))
            else:
                raise JpyRuntimeError(f"not callable: {callee!r}", instr.line)

        elif op == Op.RETURN:
            val = frame.stack.pop() if frame.stack else None
            self.frames.pop()
            if self.frames:
                self.frames[-1].stack.append(val)
            else:
                self.last_value = val

        elif op == Op.GET_ATTR:
            obj = frame.stack.pop()
            if hasattr(obj, instr.arg):
                frame.stack.append(getattr(obj, instr.arg))
            elif isinstance(obj, dict) and instr.arg in obj:
                frame.stack.append(obj[instr.arg])
            else:
                raise JpyRuntimeError(
                    f"no attribute {instr.arg!r} on {type(obj).__name__}", instr.line)

        elif op == Op.SET_ATTR:
            val = frame.stack.pop()
            obj = frame.stack.pop()
            setattr(obj, instr.arg, val)

        elif op == Op.GET_INDEX:
            key = frame.stack.pop()
            obj = frame.stack.pop()
            try:
                frame.stack.append(obj[key])
            except Exception as e:
                raise JpyRuntimeError(str(e), instr.line)

        elif op == Op.SET_INDEX:
            val = frame.stack.pop()
            key = frame.stack.pop()
            obj = frame.stack.pop()
            obj[key] = val

        elif op == Op.BUILD_LIST:
            n = instr.arg
            items = [frame.stack.pop() for _ in range(n)][::-1]
            frame.stack.append(items)

        elif op == Op.BUILD_DICT:
            n = instr.arg
            items = []
            for _ in range(n):
                v = frame.stack.pop()
                k = frame.stack.pop()
                items.append((k, v))
            items.reverse()
            frame.stack.append(dict(items))

        elif op == Op.SETUP_EXCEPT:
            # marker + handler
            frame.stack.append("<except>")
            frame.handlers.append(instr.arg)

        elif op == Op.POP_EXCEPT:
            if frame.handlers:
                frame.handlers.pop()
            # drop the marker if present
            if frame.stack and frame.stack[-1] == "<except>":
                frame.stack.pop()

        elif op == Op.THROW:
            v = frame.stack.pop()
            raise JpyRuntimeError(str(v), instr.line)

        elif op == Op.MAKE_CLASS:
            name, bases = instr.arg
            frame.stack.pop()  # the placeholder
            frame.stack.append(type(name, tuple(bases) or (object,), {}))

        elif op == Op.AWAIT:
            # In this reference VM, await on a plain value returns it.
            # Full coroutine scheduling is provided by vm/scheduler.py.
            pass

        elif op == Op.PRINT:
            v = frame.stack.pop()
            print(v)

        elif op == Op.HALT:
            self.last_value = frame.stack.pop() if frame.stack else None
            self.frames.clear()
            return

        else:
            raise JpyRuntimeError(f"unhandled opcode {op.name}", instr.line)

    # ---- helpers ----------------------------------------------------------
    def _call_function(self, fn: JpyFunction, args):
        if len(args) != len(fn.code.params):
            raise JpyRuntimeError(
                f"{fn.name} expects {len(fn.code.params)} args, got {len(args)}")
        locals_env = dict(zip(fn.code.params, args))
        new_frame = Frame(fn.code, self.globals, locals_env)
        self.frames.append(new_frame)

    def _binary(self, op, a, b, line):
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            return a / b
        if op == "%":
            return a % b
        if op == "**":
            return a ** b
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == "<=":
            return a <= b
        if op == ">":
            return a > b
        if op == ">=":
            return a >= b
        if op in ("&&", "and"):
            return b if _truthy(a) else a
        if op in ("||", "or"):
            return a if _truthy(a) else b
        if op == "is":
            return a is b
        raise JpyRuntimeError(f"bad binary op: {op}", line)


def run(code: CodeObject):
    return VM().run(code)
