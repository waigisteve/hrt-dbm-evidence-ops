# Under the Hood: HRT Evidence Operations Simulation

## What This System Demonstrates

This project simulates a secure investigative evidence environment for the HRT Database Manager role. It shows how sensitive videos, images, field notes, and partner submissions can move through controlled intake, preservation, verification, analysis, legal review, reporting, and AI-assisted triage.

The design deliberately separates operational evidence handling from reporting:

- PostgreSQL is the OLTP system for controlled evidence intake and updates.
- DuckDB is the OLAP system for dashboard/reporting snapshots.
- The REST API reads the generated dashboard snapshot, not the live operational database.
- The browser dashboard prefers role-specific API reads and falls back to the generated JSON snapshot if the API is offline.

This separation is important because stakeholder reporting should not interfere with evidence integrity, custody logging, or operational database performance.

## Runtime Architecture

```text
Field / CSO / investigator submissions
        |
        v
PostgreSQL OLTP: hrt_prep
        |
        | scripts/refresh_olap.py
        v
DuckDB OLAP: olap/hrt_olap.duckdb
        |
        | dashboard/data.json
        v
REST API: http://127.0.0.1:8770/api/dashboard/{role}
        |
        v
Browser dashboard: http://127.0.0.1:8766

Fallback path if API is offline:

dashboard/data.json -> Browser dashboard
```

For full OLTP/OLAP architecture, business workflow, schema diagrams, and diagrams.net assets, see `architecture_and_business_case.md` and the `diagrams/` folder.

## PostgreSQL OLTP Layer

PostgreSQL stores the operational evidence data. It represents the environment where records are created, updated, protected, and reviewed.

Main responsibilities:

- Receive new evidence records.
- Preserve media identifiers, hashes, metadata, source references, and timestamps.
- Track chain-of-custody events.
- Track verification steps.
- Track legal review status.
- Track access classification and retention category.
- Support operational exception reports such as missing metadata or custody gaps.

Key tables:

- `media_files`: evidence item registry for videos, photos, audio, and documents.
- `incidents`: investigative incident records.
- `sources`: source and partner information.
- `locations`: structured place information.
- `custody_events`: collection, transfer, ingestion, review, export, archive, or deletion history.
- `verification_steps`: geolocation, chronolocation, technical review, corroboration, and duplicate review work.
- `legal_reviews`: legal readiness and restrictions.
- `access_logs`: access and use monitoring.
- `exports`: controlled external disclosure records.

## DuckDB OLAP Layer

DuckDB stores a reporting-oriented copy of selected evidence facts.

Main responsibilities:

- Keep reporting separate from operational evidence intake.
- Support dashboard summaries.
- Reduce accidental pressure on the OLTP database.
- Demonstrate a practical analytics/data-mart pattern.

Generated table:

- `evidence_fact`: denormalised reporting table created by `scripts/refresh_olap.py`.

This layer is disposable. It can be rebuilt from PostgreSQL.

## Dashboard Layer

The dashboard is a lightweight browser interface served by Python's built-in HTTP server. It now uses the REST API as the primary read path.

Files:

- `dashboard/server.py`: local static file server.
- `dashboard/index.html`: dashboard shell.
- `dashboard/app.js`: stakeholder view switching, role-specific API reads, static JSON fallback, and live refresh.
- `dashboard/styles.css`: visual layout.
- `dashboard/data.json`: generated reporting snapshot.

The dashboard refreshes every 5 seconds. It first calls:

```text
GET http://127.0.0.1:8770/api/dashboard/{role}
```

It also reads the full API snapshot as shared demo context for filters and cross-tab charts. If the API is offline, it falls back to:

```text
/dashboard/data.json
```

The access selector simulates stakeholder-specific access views:

- Leadership: incident-level readiness and risk summary.
- Investigations: working evidence queue.
- Legal: ready or pending legal review records.
- CSO Partners: custody and submission-quality issues.
- Data Protection: restricted records and high-risk processing.
- AI Review: candidate AI tasks and required controls.

This is a demo access model. In a production system, it would be replaced by real authentication, authorisation, MFA, audit logging, and server-side access enforcement.

## REST API Layer

The local API creates the service boundary needed for JWT, RBAC, API gateway routing, and future backend enforcement.

Files:

- `api/server.py`: local REST-style JSON API.
- `api/openapi.py`: OpenAPI 3.0 contract.
- `auth_rbac_implementation.md`: demo token/RBAC model and production identity-provider recommendation.

Implemented endpoints:

```text
GET /api/health
POST /api/auth/demo-login
GET /api/dashboard
GET /api/dashboard/{role}
GET /api/anomalies
GET /api/notifications
GET /api/openapi.json
GET /api/docs
```

The dashboard header shows `Role API online` when role-specific API reads are working, and `API offline fallback` when the browser has fallen back to the static snapshot. The role endpoint checks a local signed demo token before returning data.

## Continuous Intake Simulation

`scripts/simulate_continuous_intake.py` simulates an hour of ongoing submissions.

What it does:

1. Creates a new fictional CSO partner/source.
2. Creates a new fictional location and incident.
3. Inserts 2-4 new evidence items per batch.
4. Mixes video, image, and document submissions.
5. Adds custody events for video/image items.
6. Intentionally leaves some document records weaker to simulate real-world metadata and custody gaps.
7. Adds initial verification triage.
8. Refreshes the OLAP store and dashboard snapshot after each batch.

Default run:

```bash
python3 scripts/simulate_continuous_intake.py --minutes 60 --interval 30
```

This creates a new batch every 30 seconds for one hour.

## ETL / Reporting Refresh

`scripts/refresh_olap.py` is the bridge between OLTP and OLAP.

It:

1. Queries PostgreSQL using `psql`.
2. Pulls an evidence readiness dataset.
3. Rebuilds `olap/hrt_olap.duckdb`.
4. Writes `dashboard/data.json`.
5. Feeds the REST API and browser fallback path.

This is intentionally simple and transparent for interview demonstration. In production, this could become a scheduled ETL job, CDC pipeline, materialised view process, or managed warehouse ingestion.

## AI Integration Model

AI is represented as a controlled review queue, not as an automated decision-maker.

The dashboard AI tab identifies candidate uses:

- Local/private transcription.
- Translation for internal triage.
- Entity extraction from redacted notes.
- Similarity and duplicate detection.
- Metadata extraction support.
- Draft summaries for human review.

The controls are explicit:

- No raw restricted media to unapproved external SaaS.
- Human review is required.
- AI output is labelled as AI-assisted.
- Tool, version, reviewer, and decision should be logged.
- DPIA is required for systematic AI processing of sensitive data.
- AI must not identify perpetrators, make legal conclusions, or replace verification.

Interview phrasing:

> AI sits behind data protection and verification controls. It helps triage and reduce manual workload, but it does not convert unverified material into verified evidence.

## How This Maps to HRT's Role

| Job area | Demonstrated by |
| --- | --- |
| Systems Management & Optimisation | Live operational checks, custody gaps, metadata gaps, dashboard monitoring |
| Strategic Development & Migration | OLTP/OLAP separation, rebuildable analytics layer, migration validation queries |
| Relational Database Development | PostgreSQL schema linking incidents, media, sources, custody, verification, legal review |
| Verification & Investigative Workflows | Evidence readiness, metadata preservation, chain-of-custody tracking |
| AI & Innovation | AI review queue with controls and safe-use boundaries |
| Team Support & Capacity Building | Stakeholder-specific dashboard tabs and plain-language runbooks |
| Data Protection & Compliance | Restricted records, retention categories, access classification, DPIA triggers |

## Production Hardening Notes

This is an interview simulation. A production version would need:

- Real authentication and role-based authorisation.
- Server-side access enforcement.
- MFA and audit logs for dashboard use.
- Encrypted object storage for original media.
- Secure secret management.
- Backups and restore testing.
- Monitoring and alerting.
- Vendor SLA tracking.
- Data retention automation.
- DPIA and legal review workflow integration.
- A documented incident response process.
