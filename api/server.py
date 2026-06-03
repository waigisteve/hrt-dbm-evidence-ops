#!/usr/bin/env python3
"""Minimal HRT API service.

This is the first low-cost production-hardening step. It wraps the existing
dashboard snapshot with HTTP API endpoints without changing the database,
dashboard, or ETL flow.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.openapi import openapi_spec  # noqa: E402

SNAPSHOT_JSON = ROOT / "dashboard" / "data.json"
DEMO_TOKEN_SECRET = os.getenv("HRT_DEMO_TOKEN_SECRET", "hrt-local-demo-secret-change-me")
DEMO_TOKEN_TTL_SECONDS = int(os.getenv("HRT_DEMO_TOKEN_TTL_SECONDS", "3600"))
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
INTERNAL_ROLES = VALID_ROLES - {"partners"}
ANOMALY_ROLES = {"ai", "monitoring", "data_protection", "leadership"}
NOTIFICATION_ROLES = {"monitoring", "data_protection"}


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
                        "demo_login": "/api/auth/demo-login",
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
            claims = self.authorize_any_role(INTERNAL_ROLES)
            if claims is None:
                return
            self.send_json(self.snapshot())
            return

        if path.startswith("/api/dashboard/"):
            role = path.rsplit("/", 1)[-1]
            self.send_role_dashboard(role)
            return

        if path == "/api/anomalies":
            claims = self.authorize_any_role(ANOMALY_ROLES)
            if claims is None:
                return
            snapshot = self.snapshot()
            self.send_json(snapshot.get("ai_recommendations", {}).get("anomalies", []))
            return

        if path == "/api/notifications":
            claims = self.authorize_any_role(NOTIFICATION_ROLES)
            if claims is None:
                return
            self.send_json(self.snapshot().get("notifications", {}))
            return

        self.send_json({"error": "not_found", "path": path}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path == "/api/auth/demo-login":
            payload = self.read_json_body()
            role = str(payload.get("role", ""))
            password = str(payload.get("password", ""))
            if role not in VALID_ROLES:
                self.send_json(
                    {"error": "invalid_role", "valid_roles": sorted(VALID_ROLES)},
                    HTTPStatus.BAD_REQUEST,
                )
                return
            if password != "demo":
                self.send_json({"error": "invalid_demo_password"}, HTTPStatus.UNAUTHORIZED)
                return
            self.send_json(
                {
                    "token_type": "Bearer",
                    "access_token": create_demo_token(role),
                    "role": role,
                    "expires_in": DEMO_TOKEN_TTL_SECONDS,
                    "mode": "local_demo_hmac_token",
                }
            )
            return

        self.send_json({"error": "not_found", "path": path}, HTTPStatus.NOT_FOUND)

    def send_role_dashboard(self, role: str) -> None:
        if role not in VALID_ROLES:
            self.send_json(
                {"error": "invalid_role", "valid_roles": sorted(VALID_ROLES)},
                HTTPStatus.BAD_REQUEST,
            )
            return
        claims = self.authorize_role(role)
        if claims is None:
            return

        snapshot = self.snapshot()
        self.send_json(
            {
                "generated_at": snapshot.get("generated_at"),
                "role": role,
                "subject": claims.get("sub"),
                "kpis": snapshot.get("kpis", {}),
                "data": snapshot.get(role, []),
                "charts": snapshot.get("charts", {}),
                "ai_recommendations": snapshot.get("ai_recommendations", {}),
                "notifications": snapshot.get("notifications", {}),
            }
        )

    def authorize_role(self, requested_role: str) -> dict[str, Any] | None:
        claims = self.read_bearer_claims()
        if claims is None:
            return None
        token_role = claims.get("role")
        if token_role != requested_role:
            self.send_json(
                {"error": "forbidden_role", "token_role": token_role, "requested_role": requested_role},
                HTTPStatus.FORBIDDEN,
            )
            return None
        return claims

    def authorize_any_role(self, allowed_roles: set[str]) -> dict[str, Any] | None:
        claims = self.read_bearer_claims()
        if claims is None:
            return None
        token_role = claims.get("role")
        if token_role not in allowed_roles:
            self.send_json(
                {"error": "forbidden_endpoint", "token_role": token_role, "allowed_roles": sorted(allowed_roles)},
                HTTPStatus.FORBIDDEN,
            )
            return None
        return claims

    def read_bearer_claims(self) -> dict[str, Any] | None:
        auth_header = self.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            self.send_json({"error": "missing_bearer_token"}, HTTPStatus.UNAUTHORIZED)
            return None
        claims = verify_demo_token(auth_header.removeprefix("Bearer ").strip())
        if claims is None:
            self.send_json({"error": "invalid_or_expired_token"}, HTTPStatus.UNAUTHORIZED)
            return None
        return claims

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

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
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def log_message(self, format: str, *args: Any) -> None:
        return


def api_docs_html() -> str:
    endpoints = [
        ("POST", "/api/auth/demo-login", "Local demo role token"),
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


def create_demo_token(role: str) -> str:
    now = int(time.time())
    claims = {
        "sub": f"demo-user:{role}",
        "role": role,
        "iat": now,
        "exp": now + DEMO_TOKEN_TTL_SECONDS,
        "iss": "hrt-local-demo",
    }
    payload = encode_json(claims)
    signature = sign(payload)
    return f"{payload}.{signature}"


def verify_demo_token(token: str) -> dict[str, Any] | None:
    try:
        payload, signature = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(sign(payload), signature):
        return None
    try:
        claims = json.loads(base64.urlsafe_b64decode(pad_base64(payload)).decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        return None
    if int(claims.get("exp", 0)) < int(time.time()):
        return None
    if claims.get("role") not in VALID_ROLES:
        return None
    return claims


def encode_json(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")


def sign(payload: str) -> str:
    digest = hmac.new(DEMO_TOKEN_SECRET.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def pad_base64(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode("ascii")


def main() -> None:
    port = int(os.getenv("HRT_API_PORT", "8770"))
    server = ThreadingHTTPServer(("127.0.0.1", port), ApiHandler)
    print(f"HRT API running at http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
