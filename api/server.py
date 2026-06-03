#!/usr/bin/env python3
"""Minimal HRT API service.

This is the first low-cost production-hardening step. It wraps the existing
dashboard snapshot with HTTP API endpoints without changing the database,
dashboard, or ETL flow.
"""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
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
    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"

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
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


def main() -> None:
    port = int(os.getenv("HRT_API_PORT", "8770"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ApiHandler)
    print(f"HRT API running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
