#!/usr/bin/env python3
"""Minimal HRT API service.

This is the first low-cost production-hardening step. It wraps the existing
dashboard snapshot with HTTP API endpoints without changing the database,
dashboard, or ETL flow.
"""

from __future__ import annotations

import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.openapi import openapi_spec  # noqa: E402

SNAPSHOT_JSON = ROOT / "dashboard" / "data.json"
VALID_ROLES = {
    "leadership",
    "investigations",
    "legal",
    "partners",
    "data_protection",
    "ai",
    "media",
    "monitoring",
}


class ApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_common_headers()
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in {"/", "/api"}:
            self.send_json(
                {
                    "service": "hrt-api",
                    "status": "ok" if SNAPSHOT_JSON.exists() else "degraded",
                    "endpoints": {
                        "health": "/api/health",
                        "full_dashboard_snapshot": "/api/dashboard",
                        "role_dashboard": "/api/dashboard/{role}",
                        "anomalies": "/api/anomalies",
                        "notifications": "/api/notifications",
                        "openapi": "/api/openapi.json",
                        "docs": "/api/docs",
                    },
                    "valid_roles": sorted(VALID_ROLES),
                }
            )
            return

        if path == "/api/openapi.json":
            self.send_json(openapi_spec())
            return

        if path == "/api/docs":
            self.send_html(api_docs_html())
            return

        if path == "/api/health":
            self.send_json(
                {
                    "status": "ok" if SNAPSHOT_JSON.exists() else "degraded",
                    "service": "hrt-api",
                    "snapshot_exists": SNAPSHOT_JSON.exists(),
                }
            )
            return

        if path == "/api/dashboard":
            self.send_json(self.snapshot())
            return

        if path.startswith("/api/dashboard/"):
            role = path.rsplit("/", 1)[-1]
            self.send_role_dashboard(role)
            return

        if path == "/api/anomalies":
            snapshot = self.snapshot()
            self.send_json(snapshot.get("ai_recommendations", {}).get("anomalies", []))
            return

        if path == "/api/notifications":
            self.send_json(self.snapshot().get("notifications", {}))
            return

        self.send_json({"error": "not_found", "path": path}, HTTPStatus.NOT_FOUND)

    def send_role_dashboard(self, role: str) -> None:
        if role not in VALID_ROLES:
            self.send_json(
                {"error": "invalid_role", "valid_roles": sorted(VALID_ROLES)},
                HTTPStatus.BAD_REQUEST,
            )
            return

        snapshot = self.snapshot()
        self.send_json(
            {
                "generated_at": snapshot.get("generated_at"),
                "role": role,
                "kpis": snapshot.get("kpis", {}),
                "data": snapshot.get(role, []),
                "charts": snapshot.get("charts", {}),
                "ai_recommendations": snapshot.get("ai_recommendations", {}),
                "notifications": snapshot.get("notifications", {}),
            }
        )

    def snapshot(self) -> dict[str, Any]:
        if not SNAPSHOT_JSON.exists():
            raise FileNotFoundError("dashboard/data.json not found. Run scripts/refresh_olap.py first.")
        return json.loads(SNAPSHOT_JSON.read_text(encoding="utf-8"))

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_common_headers()
        self.end_headers()
        self.wfile.write(body)

    def send_common_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8766")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def log_message(self, format: str, *args: Any) -> None:
        return


def api_docs_html() -> str:
    endpoints = [
        ("GET", "/api/health", "API and snapshot health"),
        ("GET", "/api/dashboard", "Full dashboard snapshot"),
        ("GET", "/api/dashboard/leadership", "Role-shaped dashboard response"),
        ("GET", "/api/anomalies", "Redacted AI anomaly facts"),
        ("GET", "/api/notifications", "Notification delivery status"),
        ("GET", "/api/openapi.json", "OpenAPI 3.0 contract"),
    ]
    rows = "\n".join(
        f"<tr><td>{method}</td><td><a href='{path}'>{path}</a></td><td>{description}</td></tr>"
        for method, path, description in endpoints
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HRT API Docs</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #18212f; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 980px; }}
    th, td {{ border-bottom: 1px solid #d8dee8; padding: 10px; text-align: left; }}
    th {{ background: #f4f6f9; }}
    code, a {{ color: #1d5f99; }}
  </style>
</head>
<body>
  <h1>HRT Evidence Operations API</h1>
  <p>Minimal REST-style JSON API for the local reporting snapshot.</p>
  <p>OpenAPI contract: <a href="/api/openapi.json">/api/openapi.json</a></p>
  <table>
    <thead><tr><th>Method</th><th>Endpoint</th><th>Purpose</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>
"""


def main() -> None:
    port = int(os.getenv("HRT_API_PORT", "8770"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ApiHandler)
    print(f"HRT API running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
