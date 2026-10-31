"""
JapyScript — reference HTTP server runtime.

Serves compiled `.jpy` services over HTTP/1.1. Implements request parsing,
route dispatch, and response serialisation without external dependencies.

This module is the reference implementation used by `jpy serve`.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import threading


class Route:
    def __init__(self, method, path, handler):
        self.method = method.upper()
        self.path = path
        self.handler = handler

    def matches(self, method, path):
        return self.method == method.upper() and self.path == path


class Request:
    def __init__(self, method, path, headers, body, query):
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.query = query

    def json(self):
        return json.loads(self.body.decode("utf-8")) if self.body else None


class Response:
    def __init__(self, status=200, body=b"", headers=None):
        self.status = status
        self.body = body if isinstance(body, bytes) else str(body).encode()
        self.headers = headers or {}

    @classmethod
    def json(cls, data, status=200):
        body = json.dumps(data).encode("utf-8")
        return cls(status, body, {"Content-Type": "application/json"})


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, handler):
        self.routes.append(Route(method, path, handler))

    def dispatch(self, req):
        for r in self.routes:
            if r.matches(req.method, req.path):
                return r.handler(req)
        return Response.json({"error": "not found", "path": req.path}, 404)


class JapyHandler(BaseHTTPRequestHandler):
    router: Router = None

    def _handle(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        req = Request(
            self.command, parsed.path,
            {k.lower(): v for k, v in self.headers.items()},
            body, parse_qs(parsed.query),
        )
        try:
            resp = self.router.dispatch(req)
        except Exception as exc:
            resp = Response.json({"error": str(exc)}, 500)

        self.send_response(resp.status)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(resp.body)))
        self.end_headers()
        if resp.body:
            self.wfile.write(resp.body)

    do_GET = _handle
    do_POST = _handle
    do_PUT = _handle
    do_DELETE = _handle

    def log_message(self, fmt, *args):
        print(f"[jpy] {self.address_string()} — {fmt % args}")


class Server:
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.router = Router()
        self._httpd = None

    def route(self, method, path, handler):
        self.router.add(method, path, handler)
        return self

    def listen(self):
        self._httpd = HTTPServer((self.host, self.port), JapyHandler)
        JapyHandler.router = self.router
        print(f"[jpy] listening on http://{self.host}:{self.port}")
        self._httpd.serve_forever()

    def listen_async(self):
        t = threading.Thread(target=self.listen, daemon=True)
        t.start()
        return t


if __name__ == "__main__":
    s = Server()
    s.route("GET", "/health", lambda req: Response.json({"status": "ok"}))
    s.listen()
