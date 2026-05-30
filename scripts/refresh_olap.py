#!/usr/bin/env python3
"""Refresh the OLAP DuckDB store and dashboard JSON from PostgreSQL OLTP."""

from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OLAP_DIR = ROOT / "olap"
DASHBOARD_DIR = ROOT / "dashboard"
OLAP_DB = OLAP_DIR / "videre_olap.duckdb"
SNAPSHOT_JSON = DASHBOARD_DIR / "data.json"
PG_DB = "videre_prep"


def run(command: list[str], input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def psql_csv(sql: str) -> list[dict[str, str]]:
    command = ["sudo", "-u", "postgres", "psql", "-d", PG_DB, "-A", "-F", ",", "-q", "-c", sql]
    output = run(command)
    lines = [line for line in output.splitlines() if line and not line.startswith("(")]
    if not lines:
        return []
    return list(csv.DictReader(lines))


def duckdb(sql: str) -> None:
    run(["duckdb", str(OLAP_DB)], sql)


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def numeric(value: str) -> str:
    return value if value not in {"", None} else "NULL"


def rebuild_olap(rows: list[dict[str, str]]) -> None:
    OLAP_DIR.mkdir(exist_ok=True)
    DASHBOARD_DIR.mkdir(exist_ok=True)

    values: list[str] = []
    for row in rows:
        values.append(
            "("
            + ",".join(
                [
                    numeric(row["media_id"]),
                    q(row["original_filename"]),
                    q(row["incident_code"]),
                    q(row["title"]),
                    q(row["media_type"]),
                    q(row["access_classification"]),
                    q(row["verification_status"]),
                    q(row["legal_status"]),
                    numeric(row["custody_events"]),
                    numeric(row["verification_steps"]),
                    q(row["retention_category"]),
                    q(row["received_at"]),
                    q(row["source_code"]),
                    q(row["risk_level"]),
                ]
            )
            + ")"
        )

    body = ",\n".join(values) if values else ""
    insert_sql = ""
    if body:
        insert_sql = f"""
INSERT INTO evidence_fact VALUES
{body};
"""

    duckdb(
        f"""
DROP TABLE IF EXISTS evidence_fact;
CREATE TABLE evidence_fact (
    media_id INTEGER,
    original_filename VARCHAR,
    incident_code VARCHAR,
    title VARCHAR,
    media_type VARCHAR,
    access_classification VARCHAR,
    verification_status VARCHAR,
    legal_status VARCHAR,
    custody_events INTEGER,
    verification_steps INTEGER,
    retention_category VARCHAR,
    received_at VARCHAR,
    source_code VARCHAR,
    source_risk_level VARCHAR
);
{insert_sql}
"""
    )


def dashboard_snapshot(rows: list[dict[str, str]]) -> dict[str, Any]:
    total = len(rows)
    ready = [
        row
        for row in rows
        if row["verification_status"] == "verified"
        and row["legal_status"] == "approved_for_legal_use"
        and int(row["custody_events"]) >= 2
    ]
    restricted = [row for row in rows if row["access_classification"] == "restricted"]
    custody_gaps = [row for row in rows if int(row["custody_events"]) == 0]
    needs_legal = [row for row in rows if row["legal_status"] in {"needs_review", "not_reviewed"}]
    unverified = [row for row in rows if row["verification_status"] == "unverified"]

    incidents: dict[str, dict[str, Any]] = {}
    for row in rows:
        item = incidents.setdefault(
            row["incident_code"],
            {"incident_code": row["incident_code"], "title": row["title"], "items": 0, "ready": 0, "restricted": 0},
        )
        item["items"] += 1
        if row in ready:
            item["ready"] += 1
        if row["access_classification"] == "restricted":
            item["restricted"] += 1

    ai_queue = [
        {
            "media_id": row["media_id"],
            "file": row["original_filename"],
            "suggested_use": ai_suggestion(row),
            "required_control": "Human review, source-risk check, no external SaaS for restricted raw media",
        }
        for row in rows
        if row["media_type"] in {"video", "audio", "document", "photo"} and row["verification_status"] == "unverified"
    ]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "total_items": total,
            "ready_for_legal": len(ready),
            "restricted_items": len(restricted),
            "custody_gaps": len(custody_gaps),
            "needs_legal_review": len(needs_legal),
            "unverified_items": len(unverified),
        },
        "leadership": list(incidents.values()),
        "investigations": rows,
        "legal": ready + needs_legal,
        "partners": custody_gaps,
        "data_protection": restricted,
        "ai": ai_queue,
    }


def ai_suggestion(row: dict[str, str]) -> str:
    media_type = row["media_type"]
    if media_type == "video":
        return "Local/private transcription, scene triage, duplicate/similarity check"
    if media_type == "photo":
        return "Metadata extraction, visual triage, similarity check"
    if media_type == "document":
        return "Entity extraction and summary after redaction"
    if media_type == "audio":
        return "Local/private transcription and translation"
    return "No AI action until sensitivity is reviewed"


def main() -> None:
    sql = """
SELECT
    m.media_id,
    m.original_filename,
    i.incident_code,
    i.title,
    m.media_type,
    m.access_classification,
    m.verification_status,
    m.legal_status,
    COUNT(DISTINCT c.custody_event_id) AS custody_events,
    COUNT(DISTINCT v.verification_step_id) AS verification_steps,
    m.retention_category,
    m.received_at,
    COALESCE(s.source_code, 'unknown') AS source_code,
    COALESCE(s.risk_level::text, 'unknown') AS risk_level
FROM media_files m
JOIN incidents i ON i.incident_id = m.incident_id
LEFT JOIN custody_events c ON c.media_id = m.media_id
LEFT JOIN verification_steps v ON v.media_id = m.media_id
LEFT JOIN sources s ON s.source_id = m.source_id
GROUP BY
    m.media_id,
    m.original_filename,
    i.incident_code,
    i.title,
    m.media_type,
    m.access_classification,
    m.verification_status,
    m.legal_status,
    m.retention_category,
    m.received_at,
    s.source_code,
    s.risk_level
ORDER BY m.media_id;
"""
    rows = psql_csv(sql)
    rebuild_olap(rows)
    SNAPSHOT_JSON.write_text(json.dumps(dashboard_snapshot(rows), indent=2), encoding="utf-8")
    print(f"Refreshed OLAP and dashboard snapshot with {len(rows)} evidence records.")


if __name__ == "__main__":
    main()
