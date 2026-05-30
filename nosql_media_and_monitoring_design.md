# NoSQL Media, Visual Analytics, AI, and Monitoring Design

## Purpose

This extension demonstrates how a Database Manager could separate structured investigative metadata from media-object handling while still giving stakeholders a friendly, visual, filtered dashboard.

The design remains safe for an interview demo:

- No real victims, conflicts, or sensitive media.
- No unknown internet binaries are downloaded.
- Synthetic sample assets are generated locally.
- File extensions and MIME guesses are scanned before dashboard exposure.

## Data Architecture

```text
PostgreSQL OLTP
  Structured operational records:
  incidents, sources, media metadata, custody, verification, legal review

NoSQL media catalog
  File-backed JSONL document store:
  object path, hash, MIME, safety state, preview path, scan results

DuckDB OLAP
  Denormalised reporting fact table:
  evidence readiness, risk, source, status, stakeholder metrics

Dashboard
  Filtered stakeholder views:
  tables, charts, media cards, monitoring cards, AI review queue
```

## Why NoSQL for Media Objects

The operational database should not store large binary videos/photos directly. It should store stable references, hashes, metadata, and governance state. Media objects are better handled by an object-store pattern.

In production this could be:

- S3, Azure Blob Storage, or equivalent encrypted object storage.
- MongoDB/GridFS only if document-oriented media metadata and object chunking are needed.
- A digital evidence platform with controlled object storage.

In this demo:

- `media_store/objects/` acts as the object store.
- `media_store/catalog.jsonl` acts as the NoSQL document catalog.
- `media_store/quarantine/` represents rejected or suspicious objects.

## Safety Checks

`scripts/sync_media_catalog.py` generates and scans safe synthetic assets.

Checks include:

- Allowlisted extensions: `.svg`, `.txt`.
- Blocked extensions: `.exe`, `.bat`, `.cmd`, `.js`, `.vbs`, `.scr`, `.ps1`, `.dll`, `.zip`.
- MIME guess.
- SHA-256 hash.
- File size threshold.
- Safety status: `safe`, `review`, or `blocked`.

Production hardening would add antivirus scanning, file magic verification, content disarm and reconstruction, malware sandboxing, quarantine workflow, and chain-of-custody logging for every object movement.

## Dashboard Improvements

The dashboard now supports:

- Filters by incident, media type, verification state, legal state, access class, safety state, and search text.
- KPI cards.
- Media mix donut chart.
- Verification status bar chart.
- Stakeholder-specific tables.
- NoSQL media gallery.
- Monitoring cards.
- AI review queue.

Filtering applies consistently across KPIs, charts, and stakeholder views.

## AI Integration

AI is positioned as controlled workflow assistance, not evidence verification.

Supported demo uses:

- Video/audio transcription candidate.
- Translation candidate.
- Entity extraction from redacted notes.
- Similarity or duplicate detection.
- Visual triage of synthetic image/video placeholders.
- Summary drafting for human review.

Controls:

- No raw restricted media to unapproved external SaaS.
- Human review required.
- AI output labelled and auditable.
- Tool, version, reviewer, date, and decision logged.
- DPIA required for systematic sensitive-data processing.
- AI cannot identify perpetrators, make legal conclusions, or replace verification.

## Monitoring Model

The monitoring layer looks for both technical and evidentiary risks:

- Infiltration risk: unusual restricted-data access patterns would be monitored through access logs in production.
- Low performance: ETL refresh duration and stale dashboard data.
- Data quality: custody gaps, missing metadata, unverified backlog.
- Skewed information: overdependence on one source or too many records from one source cluster.
- Compliance risk: restricted records, legal-review backlog, unsafe media scan state.

Current demo metrics:

- Restricted data concentration.
- Custody gap rate.
- Unverified backlog.
- Single-source skew.
- Dashboard freshness.
- ETL refresh seconds.

## Interview Framing

> I would keep media binaries out of the relational database. PostgreSQL should manage evidence metadata, custody, verification, and governance. A NoSQL/object-store layer should hold object documents and media references, with safety scanning and quarantine. OLAP reporting should then expose filtered, role-specific dashboards without putting pressure on the operational evidence system.
