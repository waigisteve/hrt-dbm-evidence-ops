#!/usr/bin/env python3
"""Build a file-backed NoSQL media catalog with safe synthetic sample assets."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_JSON = ROOT / "dashboard" / "data.json"
STORE = ROOT / "media_store"
OBJECTS = STORE / "objects"
CATALOG = STORE / "catalog.jsonl"

ALLOWED_EXTENSIONS = {".svg", ".txt"}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".cmd", ".js", ".vbs", ".scr", ".ps1", ".dll", ".zip"}


def slug(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value).strip("-").lower()
    return clean or "media-object"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def synthetic_photo(row: dict[str, Any]) -> str:
    title = escape(row["incident_code"])
    subtitle = escape(row["original_filename"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
  <rect width="960" height="540" fill="#dfe7ef"/>
  <rect x="0" y="330" width="960" height="210" fill="#607086"/>
  <rect x="96" y="190" width="220" height="140" fill="#f4f6f9" stroke="#18212f" stroke-width="6"/>
  <rect x="620" y="145" width="180" height="185" fill="#f4f6f9" stroke="#18212f" stroke-width="6"/>
  <circle cx="760" cy="92" r="42" fill="#f2c94c"/>
  <path d="M0 360 C220 300 400 410 620 350 C760 310 850 320 960 300 L960 540 L0 540 Z" fill="#8fa3b8"/>
  <text x="48" y="62" font-family="Arial" font-size="30" font-weight="700" fill="#18212f">{title}</text>
  <text x="48" y="102" font-family="Arial" font-size="22" fill="#35465c">Synthetic safe image placeholder</text>
  <text x="48" y="492" font-family="Arial" font-size="20" fill="#ffffff">{subtitle}</text>
</svg>
"""


def synthetic_video_storyboard(row: dict[str, Any]) -> str:
    title = escape(row["incident_code"])
    subtitle = escape(row["original_filename"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">
  <rect width="960" height="540" fill="#18212f"/>
  <rect x="52" y="74" width="856" height="372" rx="8" fill="#0f1724" stroke="#8fa3b8" stroke-width="4"/>
  <polygon points="420,190 420,330 555,260" fill="#f2c94c"/>
  <rect x="92" y="388" width="776" height="18" fill="#35465c"/>
  <rect x="92" y="388" width="256" height="18" fill="#1d5f99"/>
  <text x="52" y="42" font-family="Arial" font-size="30" font-weight="700" fill="#ffffff">{title}</text>
  <text x="52" y="484" font-family="Arial" font-size="20" fill="#d8dee8">Synthetic video storyboard placeholder: {subtitle}</text>
</svg>
"""


def synthetic_note(row: dict[str, Any]) -> str:
    return "\n".join(
        [
            "Synthetic field note placeholder",
            f"Incident: {row['incident_code']}",
            f"Original filename: {row['original_filename']}",
            "Safety: generated locally, no real victim/source data.",
            "Use: dashboard demonstration only.",
            "",
        ]
    )


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def asset_for(row: dict[str, Any]) -> Path:
    stem = slug(f"{row['incident_code']}-{row['media_id']}-{row['original_filename']}")
    if row["media_type"] == "document":
        return OBJECTS / f"{stem}.txt"
    return OBJECTS / f"{stem}.svg"


def create_asset(row: dict[str, Any]) -> Path:
    path = asset_for(row)
    if row["media_type"] == "video":
        write_text(path, synthetic_video_storyboard(row))
    elif row["media_type"] == "photo":
        write_text(path, synthetic_photo(row))
    else:
        write_text(path, synthetic_note(row))
    return path


def scan_asset(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    mime, _ = mimetypes.guess_type(path.name)
    status = "safe"
    reasons: list[str] = []

    if suffix in BLOCKED_EXTENSIONS:
        status = "blocked"
        reasons.append("blocked_extension")
    if suffix not in ALLOWED_EXTENSIONS:
        status = "review"
        reasons.append("extension_not_in_allowlist")
    if path.stat().st_size > 2_000_000:
        status = "review"
        reasons.append("sample_asset_too_large")

    return {
        "safe_status": status,
        "scan_reasons": reasons or ["allowlisted_extension", "synthetic_local_asset"],
        "detected_mime": mime or "application/octet-stream",
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def load_existing_catalog() -> dict[str, dict[str, Any]]:
    if not CATALOG.exists():
        return {}
    existing: dict[str, dict[str, Any]] = {}
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            doc = json.loads(line)
            existing[str(doc["media_id"])] = doc
    return existing


def main() -> None:
    if not DASHBOARD_JSON.exists():
        raise SystemExit(
            "dashboard/data.json does not exist yet. Run `python3 scripts/refresh_olap.py` first, "
            "then rerun `python3 scripts/sync_media_catalog.py`."
        )
    data = json.loads(DASHBOARD_JSON.read_text(encoding="utf-8"))
    rows = data.get("investigations", [])
    OBJECTS.mkdir(parents=True, exist_ok=True)
    previous = load_existing_catalog()

    documents = []
    reused = 0
    for row in rows:
        path = asset_for(row)
        prior = previous.get(str(row["media_id"]))
        if path.exists() and prior and prior.get("bytes") == path.stat().st_size:
            scan = {key: prior[key] for key in ("safe_status", "scan_reasons", "detected_mime", "sha256", "bytes")}
            ingested_at = prior.get("ingested_at", datetime.now(timezone.utc).isoformat())
            reused += 1
        else:
            if not path.exists():
                create_asset(row)
            scan = scan_asset(path)
            ingested_at = datetime.now(timezone.utc).isoformat()
        documents.append(
            {
                "document_id": f"media-{row['media_id']}",
                "media_id": row["media_id"],
                "incident_code": row["incident_code"],
                "original_filename": row["original_filename"],
                "media_type": row["media_type"],
                "object_path": str(path.relative_to(ROOT)),
                "preview_path": str(path.relative_to(ROOT)),
                "source": "synthetic_safe_scaffold",
                "ingested_at": ingested_at,
                **scan,
            }
        )

    payload = "\n".join(json.dumps(doc, sort_keys=True) for doc in documents) + "\n"
    tmp_path = CATALOG.with_suffix(".jsonl.tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, CATALOG)
    print(f"Synced {len(documents)} NoSQL media catalog documents to {CATALOG} ({reused} reused, {len(documents) - reused} (re)scanned).")


if __name__ == "__main__":
    main()
