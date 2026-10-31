# JapyScript

**Python's readability. JavaScript's reach.**

JapyScript (`.jpy`) is a general-purpose programming language that fuses the parts of Python and JavaScript that developers actually love — Python's clean indentation-based syntax, expressive collections, and readable control flow, married to JavaScript's event loop, arrow functions, template literals, and its universal runtime footprint.

Write code that reads like Python and runs where JavaScript runs.

## Why JapyScript

Python and JavaScript are the two most-used languages on Earth, and they solve opposite halves of the same problem:

- Python gives you **clarity** — indentation, slicing, comprehensions, a batteries-included standard library.
- JavaScript gives you **reach** — a single language on every client, every server, every edge runtime, plus the best async model in mainstream programming.

Developers are forced to pick. JapyScript refuses the choice. One syntax, one standard library, one package manager — compiled to both ecosystems.

## Design Principles

1. **Indentation is the block.** No braces required, no semicolons required. Braces are accepted where they aid clarity, never mandated.
2. **Two dialects, one grammar.** Python idioms and JavaScript idioms are both first-class. `arr.append(x)` and `arr.push(x)` do the same thing. `not x` and `!x` do the same thing. You never lose a habit.
3. **Transparent compilation.** `jpy` compiles to JavaScript and to Python. There is no opaque VM you can't debug — the output is readable, source-mapped, and inspectable.
4. **Types are optional and enforced where declared.** Untyped code runs. Typed code is checked before it runs. No ceremony tax.
5. **Zero-dependency core.** The compiler, runtime, and standard library ship as one installable with no third-party dependencies.
6. **Async is not an afterthought.** `async`/`await` is a language primitive with `await` allowed at top level.

## A Quick Tour

### Hello, world

```javascript
print("Hello, JapyScript!")
console.log("Hello, JapyScript!")   // same function
```

### Variables and constants

```javascript
name = "Ada"            // implicit declaration, Python-style
age = 36

const PI = 3.14159      // explicit, immutable
let counter = 0         // explicit, mutable
var legacy = true       // hoisted, kept for JS interop
```

### Functions

```javascript
def greet(name, greeting = "Hello"):
    return f"{greeting}, {name}!"

double = (x) => x * 2

def add(a: int, b: int) -> int:
    return a + b
```

### Control flow

```javascript
for item in items:
    if item.active && item.score >= 90:
        print(item.name)
    elif item.score >= 50:
        continue
    else:
        break

for i in range(10): print(i)

users.forEach((u) => print(u.name))
```

### Collections

```javascript
nums = [1, 2, 3]
nums.append(4)          // Python method
nums.push(5)            // JS method — identical effect

first = nums[0]
last  = nums[-1]        // negative indexing
slice = nums[1:3]       // slicing

squares = [n * n for n in nums if n % 2 == 1]

config = {"host": "localhost", "port": 8080}
config["debug"] = true
config.port             // attribute access on dicts
config.get("timeout", 30)
```

### Classes

```javascript
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        return f"{self.name} makes a sound"

class Dog(Animal):
    def speak(self):
        return f"{self.name} barks"

    @staticmethod
    def species():
        return "Canis familiaris"
```

### Asynchronous programming

```javascript
async def fetch_user(id):
    res = await fetch(f"/api/users/{id}")
    if !res.ok:
        throw new Error("user not found")
    return await res.json()

users = await Promise.all(ids.map((id) => fetch_user(id)))
```

### Error handling

```javascript
try:
    data = JSON.parse(raw)
except SyntaxError as e:
    print("bad json:", e.message)
finally:
    cleanup()
```

### Modules

```javascript
import math
import { readFile, writeFile } from "fs"
from datetime import now
```

### Optional types

```javascript
type Point = { x: float, y: float }

def distance(a: Point, b: Point) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
```

Type annotations are erased at runtime and verified by `jpy check` before execution.

## Toolchain

| Command | Purpose |
| --- | --- |
| `jpy run app.jpy` | Execute a JapyScript program |
| `jpy build app.jpy --target js` | Compile to JavaScript |
| `jpy build app.jpy --target py` | Compile to Python |
| `jpy check` | Static analysis and type checking |
| `jpy repl` | Interactive shell |
| `jpy fmt` | Canonical formatter |
| `jpy test` | Built-in test runner |
| `jpy doc` | Generate API documentation |
| `jpm install <pkg>` | Package manager (npm + PyPI compatible) |

## Compilation Targets

JapyScript compiles to readable, source-mapped JavaScript (ES2022) and to readable, source-mapped Python (3.11+). Anything the language can express is expressible on both targets; features without a native equivalent are polyfilled by the runtime library shipped with the compiler.

## Roadmap

- [x] **Phase 0** — Language specification and design document
- [ ] **Phase 1** — Lexer and tokenizer
- [ ] **Phase 2** — Parser and AST
- [ ] **Phase 3** — Tree-walking interpreter (reference implementation)
- [ ] **Phase 4** — JavaScript transpiler backend
- [ ] **Phase 5** — Standard library v1 (strings, collections, math, JSON, fs, http, datetime, regex)
- [ ] **Phase 6** — Python transpiler backend
- [ ] **Phase 7** — `jpm` package manager and registry client
- [ ] **Phase 8** — Static type checker
- [ ] **Phase 9** — Formatter, linter, language server (LSP), editor integrations
- [ ] **Phase 10** — Self-hosted compiler

Every phase ships a working artifact. Nothing is merged that does not run.

## Repository Layout

```
japyscript/
├── docs/           Language specification and design notes
├── src/
│   ├── lexer/      Tokenizer
│   ├── parser/     Parser and AST definitions
│   ├── interpreter/ Reference tree-walking interpreter
│   ├── transpiler/ JS and Python backends
│   └── checker/    Static analyzer and type checker
├── stdlib/         Standard library written in JapyScript
├── runtime/        Runtime support for compiled output
├── cli/            The `jpy` command
├── examples/       Runnable example programs
└── tests/          Conformance suite
```

## Contributing

Read `docs/SPEC.md` first. Every change needs a test in `tests/`. Proposals that add syntax must show both a JavaScript and a Python spelling of the same construct.