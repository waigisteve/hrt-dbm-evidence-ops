#!/usr/bin/env python3
"""Serve the stakeholder dashboard with Python's built-in HTTP server."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


DASHBOARD_DIR = Path(__file__).resolve().parent
ROOT = DASHBOARD_DIR.parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path == "/":
            self.path = "/dashboard/index.html"
        super().do_GET()


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("HRT dashboard running at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
