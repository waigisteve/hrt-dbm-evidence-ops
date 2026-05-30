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

Interview phrasing:

> AI would sit behind data protection and verification controls. It can help triage, transcribe, translate, classify, and detect duplicates, but it cannot identify perpetrators, make legal conclusions, or replace human verification.
