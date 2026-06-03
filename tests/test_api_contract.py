from __future__ import annotations

import json
from pathlib import Path


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
