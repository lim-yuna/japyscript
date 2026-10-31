# JapyScript Compiler Architecture

The compiler is a five-stage pipeline. Each stage consumes a well-defined
representation and produces the next. Stages are independently testable.

```
source.jpy
   │
   ▼
[1] Lexer          source  →  Token stream
   │
   ▼
[2] Parser         tokens  →  AST
   │
   ▼
[3] Checker        AST     →  typed AST   (optional, per module)
   │
   ▼
[4] Emitter        typed AST → bytecode  (.jpc)
   │
   ▼
[5] VM             bytecode → execution
```

---

## Stage 1 — Lexer

`compiler/lexer.py` + `compiler/tokens.py`

The lexer is indentation-aware. It maintains a stack of indentation levels.
On entering a deeper indentation it emits `INDENT`; on exiting to a shallower
level it emits one `DEDENT` per level exited.

The lexer is a single-pass state machine. It does not look ahead by more than
one character.

## Stage 2 — Parser

`compiler/parser.py` + `compiler/ast.py`

Recursive descent for statements, Pratt parsing for expressions. The parser
consumes the `INDENT` / `DEDENT` stream to build `Block` nodes; it treats
optional braces as aliases for the same block structure.

The parser is *total*: every token sequence either yields an AST or a
`ParseError` with a source location. There is no silent recovery.

## Stage 3 — Checker

`compiler/checker/` (batch 2)

The checker walks the AST, resolves names, and — when a module opts in — applies
type inference and unification. Untyped modules pass through unchanged.

## Stage 4 — Emitter

`compiler/emitter/` (batch 3)

Bytecode is emitted per function. Constants live in a per-module pool. Control
flow is lowered to jumps; loops and `try`/`finally` use structured targets.

Every emitted instruction carries a source-map entry. `jpy build --debug`
includes the source map in the `.jpc` file.

## Stage 5 — VM

`vm/` (batch 4)

The VM is a stack machine with:
- Mark-sweep garbage collector with generational promotion.
- Green-thread scheduler for `async` / `await`.
- Deterministic object layout so that binary serialisation is stable across
  runs and across machines.

---

## Invariants

- A `.jpy` file that passes `jpy check` produces the same `.jpc` bytes on every
  conforming compiler version.
- No stage mutates its input.
- Every error carries `(file, line, column, message)`.

## Directory contract

| Directory | Owns |
| --------- | ---- |
| `compiler/` | All stages 1–4 |
| `vm/` | Stage 5 |
| `stdlib/` | JapyScript-level code shipped with the compiler |
| `server/` | Optional HTTP server runtime for `.jpy` services |
| `bindings/` | Foreign-function interface implementations |
