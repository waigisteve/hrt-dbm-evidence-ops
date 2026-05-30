#!/usr/bin/env python3
"""Refresh the OLAP DuckDB store and dashboard JSON from PostgreSQL OLTP."""

from __future__ import annotations

import csv
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OLAP_DIR = ROOT / "olap"
DASHBOARD_DIR = ROOT / "dashboard"
OLAP_DB = OLAP_DIR / "videre_olap.duckdb"
SNAPSHOT_JSON = DASHBOARD_DIR / "data.json"
MEDIA_CATALOG = ROOT / "media_store" / "catalog.jsonl"
PG_DB = "videre_prep"


def run(command: list[str], input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{detail}")
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
    media_catalog = load_media_catalog()
    media_by_id = {str(item["media_id"]): item for item in media_catalog}
    for row in rows:
        catalog = media_by_id.get(str(row["media_id"]))
        if catalog:
            row["preview_path"] = "../" + catalog["preview_path"]
            row["safe_status"] = catalog["safe_status"]
            row["detected_mime"] = catalog["detected_mime"]
        else:
            row["preview_path"] = ""
            row["safe_status"] = "not_scanned"
            row["detected_mime"] = "unknown"

    charts = build_charts(rows, ready, restricted, custody_gaps, unverified)
    monitoring = build_monitoring(rows)

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
        "media": media_catalog,
        "monitoring": monitoring,
        "charts": charts,
    }


def load_media_catalog() -> list[dict[str, Any]]:
    if not MEDIA_CATALOG.exists():
        return []
    return [json.loads(line) for line in MEDIA_CATALOG.read_text(encoding="utf-8").splitlines() if line.strip()]


def count_by(rows: list[dict[str, str]], key: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return [{"label": label, "value": value} for label, value in sorted(counts.items())]


def build_charts(
    rows: list[dict[str, str]],
    ready: list[dict[str, str]],
    restricted: list[dict[str, str]],
    custody_gaps: list[dict[str, str]],
    unverified: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "media_type": count_by(rows, "media_type"),
        "verification_status": count_by(rows, "verification_status"),
        "legal_status": count_by(rows, "legal_status"),
        "risk_breakdown": [
            {"label": "Ready", "value": len(ready)},
            {"label": "Restricted", "value": len(restricted)},
            {"label": "Custody gaps", "value": len(custody_gaps)},
            {"label": "Unverified", "value": len(unverified)},
        ],
        "incident_heatmap": [
            {
                "incident_code": code,
                "title": items[0]["title"],
                "restricted": sum(1 for row in items if row["access_classification"] == "restricted"),
                "custody_gaps": sum(1 for row in items if int(row["custody_events"]) == 0),
                "unverified": sum(1 for row in items if row["verification_status"] == "unverified"),
                "total": len(items),
            }
            for code, items in group_by_incident(rows).items()
        ],
    }


def group_by_incident(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        grouped.setdefault(row["incident_code"], []).append(row)
    return grouped


def build_monitoring(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    total = max(1, len(rows))
    restricted_ratio = sum(1 for row in rows if row["access_classification"] == "restricted") / total
    custody_gap_ratio = sum(1 for row in rows if int(row["custody_events"]) == 0) / total
    unverified_ratio = sum(1 for row in rows if row["verification_status"] == "unverified") / total
    source_counts: dict[str, int] = {}
    for row in rows:
        source_counts[row["source_code"]] = source_counts.get(row["source_code"], 0) + 1
    max_source_share = max(source_counts.values(), default=0) / total

    return [
        monitor("restricted data concentration", restricted_ratio, 0.7, "High restricted-data concentration requires tight access review."),
        monitor("custody gap rate", custody_gap_ratio, 0.2, "Custody gaps should trigger intake remediation and partner coaching."),
        monitor("unverified backlog", unverified_ratio, 0.6, "Large unverified backlog can skew stakeholder interpretation."),
        monitor("single-source skew", max_source_share, 0.35, "Overdependence on one source can weaken corroboration."),
        monitor("dashboard freshness", 0.0, 1.0, "ETL completed for this snapshot."),
    ]


def monitor(name: str, value: float, threshold: float, message: str) -> dict[str, Any]:
    return {
        "name": name,
        "value": round(value, 3),
        "threshold": threshold,
        "status": "alert" if value > threshold else "ok",
        "message": message,
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
    started = time.perf_counter()
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
    snapshot = dashboard_snapshot(rows)
    snapshot["monitoring"].append(
        {
            "name": "etl refresh seconds",
            "value": round(time.perf_counter() - started, 3),
            "threshold": 5.0,
            "status": "ok" if (time.perf_counter() - started) <= 5.0 else "alert",
            "message": "Refresh duration from PostgreSQL to DuckDB and dashboard JSON.",
        }
    )
    SNAPSHOT_JSON.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Refreshed OLAP and dashboard snapshot with {len(rows)} evidence records.")


if __name__ == "__main__":
    main()
