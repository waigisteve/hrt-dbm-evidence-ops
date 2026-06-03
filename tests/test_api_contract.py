from __future__ import annotations

import json
from pathlib import Path

from api.openapi import openapi_spec


def test_dashboard_snapshot_contains_api_source_data() -> None:
    snapshot_path = Path("dashboard/data.json")
    assert snapshot_path.exists(), "Run python3 scripts/refresh_olap.py before API contract tests."
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert "generated_at" in snapshot
    assert "kpis" in snapshot
    assert isinstance(snapshot.get("investigations"), list)
    assert isinstance(snapshot.get("ai_recommendations", {}).get("anomalies", []), list)


def test_expected_dashboard_roles_are_present() -> None:
    snapshot = json.loads(Path("dashboard/data.json").read_text(encoding="utf-8"))
    for role in [
        "leadership",
        "investigations",
        "legal",
        "partners",
        "data_protection",
        "ai",
        "media",
        "monitoring",
    ]:
        assert role in snapshot


def test_openapi_contract_documents_current_endpoints() -> None:
    paths = openapi_spec()["paths"]

    for path in [
        "/",
        "/api",
        "/api/health",
        "/api/auth/demo-login",
        "/api/dashboard",
        "/api/dashboard/{role}",
        "/api/anomalies",
        "/api/notifications",
        "/api/openapi.json",
        "/api/docs",
    ]:
        assert path in paths
    assert "post" in paths["/api/auth/demo-login"]
    for path in [
        "/",
        "/api",
        "/api/health",
        "/api/dashboard",
        "/api/dashboard/{role}",
        "/api/anomalies",
        "/api/notifications",
        "/api/openapi.json",
        "/api/docs",
    ]:
        assert "get" in paths[path]
