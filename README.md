# JapyScript

**An independent, statically-checkable systems language with its own compiler, its own virtual machine, and its own standard library.**

JapyScript (`.jpy`) is designed for software that lives for a decade: network servers, compilers, protocol handlers, data-processing pipelines, background services, and interactive applications. It has no foreign runtime beneath it. Every layer — lexer, parser, checker, bytecode compiler, virtual machine, package manager — is part of JapyScript itself.

---

## Design goals

1. **Independence.** JapyScript does not delegate execution to any host language. Programs compile to JapyScript bytecode modules (`.jpc`) and execute on the JapyScript Virtual Machine.
2. **Readability under pressure.** Blocks are defined by indentation. Braces are accepted where they aid clarity, never required. Statement terminators are optional.
3. **Optional static typing.** Type declarations are verified at compile time. Untyped code runs without ceremony. Typed code catches errors before deployment.
4. **Concurrency as a primitive.** `async` / `await` are keywords. Top-level `await` is legal. Structured concurrency primitives (`spawn`, `select`, `join`) are first-class standard-library citizens.
5. **One binary.** The compiler, VM, standard library, formatter, linter, and package manager ship as a single self-contained executable.
6. **Boring where it counts.** Deterministic garbage collection, stable error messages, reproducible builds, no hidden global state.

---

## Language reference (excerpt)

### Bindings

``jpy
name = "Ada"
let count = 0
const LIMIT = 1024
``

### Functions

``jpy
def parse(source: string) -> Node:
    return Parser(source).build()

transform = (x) => x * 2
``

### Control flow

``jpy
for job in queue:
    if job.retries && job.retries >= MAX:
        dead_letter(job)
    elif job.priority > 5:
        dispatch(job)
    else:
        continue

while pending.count() > 0:
    process(pending.pop())
``

### Asynchronous execution

``jpy
async def fetch_route(path):
    response = await http.get(path)
    if !response.ok:
        throw new HttpError(response.status)
    return response.json()

routes = await Promise.all(paths.map(fetch_route))
``

### Servers

``jpy
app = Server(host="0.0.0.0", port=8080)

app.route("GET", "/health", () => {"status": "ok"})
app.route("POST", "/jobs", async (req) => {
    job = await queue.enqueue(req.body)
    return {"id": job.id, "accepted": true}
})

await app.listen()
``

### Types

``jpy
type Job = {
    id: string,
    payload: bytes,
    attempts: int
}

type Handler = (Job) -> Result

def execute(job: Job, handler: Handler) -> Result:
    return handler(job)
``

### Classes

``jpy
class Connection:
    def __init__(self, host: string, port: int):
        self.host = host
        self.port = port
        self.socket = null

    def open(self) -> bool:
        self.socket = net.connect(self.host, self.port)
        return self.socket != null
``

---

## Architecture

| Layer      | Responsibility |
| ---------- | -------------- |
| `lexer`    | Source → tokens. Indentation-aware. |
| `parser`   | Tokens → AST. Recursive descent plus Pratt expression parsing. |
| `checker`  | AST → typed AST. Optional, enabled per module. |
| `compiler` | Typed AST → bytecode modules (`.jpc`). |
| `vm`       | Bytecode → execution. Mark-sweep GC, green threads. |
| `stdlib`   | Written in JapyScript; compiled alongside user code. |
| `jpm`      | Package manager and registry client. |
| `jpy`      | Unified command-line interface. |

---

## Toolchain

- `jpy build <file.jpy>` — compile to bytecode
- `jpy run <file.jpy>` — compile and execute
- `jpy test` — run the project test suite
- `jpy fmt` — canonical formatter
- `jpy check` — static analysis and type checking
- `jpy serve` — launch the project server
- `jpm install <pkg>` — install packages
- `jpm publish` — publish a package

---

## Repository layout

``
japyscript/
  compiler/       lexer, parser, checker, bytecode emitter
  vm/             virtual machine
  stdlib/         language standard library
  server/         web server and HTTP primitives
  cli/            jpy command
  jpm/            package manager
  bindings/       native interop (C#, C, ...)
  notebooks/      design analyses and profiling notebooks
  tests/          conformance test suite
  docs/           specification, grammar, architecture
``

---

## Contributing

The language specification lives in `docs/SPEC.md`. Accepted changes add a test under `tests/`. Proposals must be small, motivated, and reviewed before implementation begins.

## License

MIT.
