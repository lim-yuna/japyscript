# JapyScript Server API

The `server/` package exposes a reference HTTP runtime for JapyScript services.

## Starting a server

```jpy
app = Server(host = "0.0.0.0", port = 8080)
app.route("GET", "/health", (req) => http.ok({"status": "ok"}))
await app.listen()
```

## Routes

`app.route(method, path, handler)`. Handlers receive a `Request` and return
a `Response` (or a coroutine that does). First matching route wins.

## Request

Fields: `method`, `path`, `headers`, `body`, `query`.

Helpers: `req.json()`, `req.text()`, `req.header(name)`.

## Response

Fields: `status`, `body`, `headers`.

Helpers in `http`: `ok`, `created`, `no_content`, `bad_request`,
`unauthorized`, `forbidden`, `not_found`, `server_error`, `redirect`.

## Lifecycle

`app.on_start(fn)` and `app.on_stop(fn)` register lifecycle handlers.

## Middleware

`app.use((req, next) => ...)` registers middleware around every handler.
