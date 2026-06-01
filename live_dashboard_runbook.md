# Live Dashboard and Continuous Simulation Runbook

## Architecture

```text
PostgreSQL OLTP
  - Receives sensitive evidence records
  - Preserves source, metadata, custody, legal status, access classification
  - Optimised for controlled write workflows

DuckDB OLAP
  - Receives refreshed reporting facts from PostgreSQL
  - Supports dashboard reporting and stakeholder summaries
  - Keeps analytics separate from operational evidence intake

Dashboard
  - Reads dashboard/data.json generated from OLAP refresh
  - Simulates stakeholder login views
  - Refreshes every 5 seconds
```

## Start the Dashboard

Terminal 1.

Use the same root-capable WSL terminal where PostgreSQL is running. If needed:

```bash
sudo -i
```

Then:

```bash
cd "/mnt/c/Users/Hp/Desktop/dba/2026/Videre_DBM_Prep_Pack"
python3 scripts/refresh_olap.py
python3 scripts/sync_media_catalog.py
python3 scripts/refresh_olap.py
python3 dashboard/server.py
```

Open:

```text
http://127.0.0.1:8765
```

The dashboard has demo stakeholder access tabs:

- Leadership
- Investigations
- Legal
- CSO Partners
- Data Protection
- AI Review

The password box is present to simulate separate access, but this is not production authentication.

## Run the One-Hour Continuous Simulation

Terminal 2.

Use another root-capable WSL terminal:

```bash
cd "/mnt/c/Users/Hp/Desktop/dba/2026/Videre_DBM_Prep_Pack"
python3 scripts/simulate_continuous_intake.py --minutes 60 --interval 30
```

For a quick test:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 2 --interval 15
```

The simulator continuously inserts new sensitive video, image, and document records into PostgreSQL, then refreshes DuckDB and the dashboard JSON.

Each simulator run now creates a fresh run ID, for example:

```text
INC-LIVE-20260601143022-a1b2c3-0001
SRC-LIVE-20260601143022-a1b2c3-0001
LIVE-20260601143022-a1b2c3-0001-1
```

This prevents repeated runs from reusing the same incident, source, media IDs, or hashes. The generated data also varies media types, verification states, legal states, access classes, custody completeness, confidence, and location confidence so the dashboard changes visibly while the simulation runs.

To force a named run for a demonstration:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 5 --interval 15 --run-id demo-001
```

## NoSQL Media Store

The demo includes a file-backed NoSQL-style media catalog:

```text
media_store/catalog.jsonl
media_store/objects/
media_store/quarantine/
```

Run:

```bash
python3 scripts/sync_media_catalog.py
python3 scripts/refresh_olap.py
```

The catalog stores one JSON document per media object. Each document includes media ID, incident code, original filename, object path, preview path, SHA-256 hash, detected MIME type, byte size, and safety scan status.

For safety, sample media objects are generated locally as synthetic SVG/text placeholders. The scanner allowlists safe demo extensions and flags blocked or unexpected extensions. This demonstrates the architecture without downloading unknown internet media or committing risky binaries.

## How to Explain the OLTP/OLAP Split

Use this phrasing:

> I would keep the operational evidence database separate from the reporting layer. PostgreSQL OLTP handles controlled intake, metadata, custody, verification, and legal status. DuckDB OLAP receives a reporting-ready copy so dashboards and stakeholder summaries do not interfere with the integrity or performance of the evidence system.

## How AI Is Integrated

The AI tab does not claim AI has verified evidence. It identifies candidate AI-assisted tasks and the controls required.

Safe examples:

- Local/private transcription of video or audio.
- Translation for internal triage.
- Entity extraction from redacted notes.
- Similarity or duplicate detection.
- Draft summaries for human review.

Controls:

- No raw restricted media to unapproved external SaaS.
- Human review required.
- AI output labelled as AI-assisted.
- Tool, version, reviewer, and decision logged.
- DPIA triggered for systematic processing of sensitive data.

## Monitoring Coverage

The Monitoring tab tracks:

- Portfolio-wide restricted-data concentration, custody gap rate, unverified backlog, and single-source skew.
- Recent intake window size, using the latest 30 evidence records.
- Recent custody gap rate, restricted concentration, unverified intake, verification progress, legal-ready yield, and single-source skew.
- Dashboard refresh freshness.
- ETL refresh duration.

The recent-window checks are designed to move visibly during a live demo. The full database can become stable as it grows, but the newest 30 records should change when the simulator inserts a fresh random batch.

To trigger a noticeable Monitoring tab change:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 2 --interval 15
```

Watch for these cards to move between percentages and alert states:

- Recent custody gap rate.
- Recent unverified intake.
- Recent verification progress.
- Recent legal-ready yield.
- Recent single-source skew.

Interview framing:

> I would monitor not only system health, but also evidentiary health. A database can be online and still produce weak findings if custody gaps, source skew, stale verification, or unsafe access patterns are not visible.

Interview phrasing:

> AI would sit behind data protection and verification controls. It can help triage, transcribe, translate, classify, and detect duplicates, but it cannot identify perpetrators, make legal conclusions, or replace human verification.
