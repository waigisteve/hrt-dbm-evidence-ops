#!/usr/bin/env python3
"""Serve the stakeholder dashboard with Python's built-in HTTP server."""

from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Videre dashboard running at http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
