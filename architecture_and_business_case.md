# Architecture and Business Case

## Business Case

HRT-style investigative teams need to receive high-risk multimedia, preserve its integrity, make it searchable, verify it responsibly, and package it safely for internal, legal, advocacy, partner, and AI-assisted workflows.

The system demonstrates a Database Manager approach that separates operational evidence handling from analytics:

- **PostgreSQL OLTP** protects the operational record: source, incident, media metadata, custody, verification, legal status, access classification, and retention.
- **NoSQL media catalog/object store** tracks media objects, previews, hashes, MIME decisions, safety status, and quarantine paths.
- **DuckDB OLAP** provides a rebuildable analytics layer for dashboards without putting pressure on the operational evidence database.
- **REST API and OpenAPI contract** expose controlled local read endpoints for health, stakeholder dashboard views, AI anomalies, notification status, and API documentation.
- **Dashboard** presents stakeholder-specific views: executives see concise strategic metrics, operators get filters and workflow queues, legal teams get precise readiness actions, partners see masked aggregates, data protection sees alerts, and AI reviewers see human-in-the-loop queues.

## What Is Achieved

| Capability | Achieved in demo | Value |
| --- | --- | --- |
| Secure intake model | Continuous simulated video/photo/document intake into PostgreSQL | Shows how fresh submissions are registered and governed |
| Evidence integrity | SHA-256 hashes, custody events, metadata fields, source links | Supports traceability and defensibility |
| OLTP/OLAP separation | PostgreSQL for operations, DuckDB for reporting | Protects evidence workflows from dashboard workload |
| NoSQL media model | JSONL document catalog plus object-store folders | Demonstrates scalable media-object handling without storing binaries in relational tables |
| REST API boundary | Local API service with OpenAPI contract and browser docs | Creates the path toward JWT, API gateway, server-side authorization, and dashboard API consumption |
| Stakeholder dashboards | Separate views for leadership, investigations, legal, CSO partners, data protection, AI, media, monitoring | Matches decision needs and cognitive load |
| AI governance | AI review queue with human-review controls | Shows safe innovation without automated evidentiary conclusions |
| Monitoring | Custody gaps, restricted concentration, unverified backlog, source skew, ETL duration | Tracks system and evidentiary health |

## Areas for Improvement

| Area | Current demo | Production improvement |
| --- | --- | --- |
| Authentication | Simulated stakeholder selector | Real SSO, MFA, RBAC, session management |
| Row-level security | UI-level separation only | PostgreSQL RLS policies and server-side authorization |
| API runtime | Local Python `http.server` REST wrapper | Production web framework/runtime, request validation, auth middleware, structured logs |
| Media storage | Local synthetic object store | Encrypted S3/Azure Blob/object store with lifecycle policy |
| Malware scanning | Extension/MIME/hash checks | Antivirus, file magic, sandboxing, quarantine workflow |
| ETL | Full refresh into DuckDB | CDC, incremental loads, orchestration, data quality gates |
| Monitoring | Dashboard-level metrics | Prometheus/Grafana, SIEM, audit anomaly detection |
| AI | Recommendation queue only | Approved private/local model pipeline with DPIA and audit logs |
| Legal workflow | Readiness status and next action | Calendar/deadline management, evidence-pack generation, approval workflow |

## Business Workflow

```mermaid
flowchart LR
    A[CSO partner / field collector / investigator] --> B[Secure intake]
    B --> C[Register source, incident, media metadata]
    C --> D[Preserve original object and calculate hash]
    D --> E[Log custody events]
    E --> F[Verification workflow]
    F --> G[Legal and data protection review]
    G --> H{Use decision}
    H -->|Internal only| I[Investigation queue]
    H -->|Legal ready| J[Controlled evidence pack]
    H -->|Partner feedback| K[Masked aggregate update]
    H -->|AI candidate| L[Human-in-the-loop AI review]
    H -->|Restricted| M[Hold / remediate / retain]
```

## OLTP Architecture

```mermaid
flowchart TB
    Intake[Secure intake channels] --> PG[(PostgreSQL OLTP)]
    ClosedVideo[Closed-source video system] --> PG
    ObjectStore[NoSQL media catalog + object store] --> PG

    PG --> Incidents[incidents]
    PG --> Media[media_files]
    PG --> Sources[sources]
    PG --> Custody[custody_events]
    PG --> Verify[verification_steps]
    PG --> Legal[legal_reviews]
    PG --> Access[access_logs]
    PG --> Exports[exports]

    Media --> Custody
    Media --> Verify
    Media --> Legal
    Media --> Exports
    Sources --> Media
    Incidents --> Media
```

## OLAP and Dashboard Architecture

```mermaid
flowchart LR
    PG[("PostgreSQL OLTP")] --> ETL["scripts/refresh_olap.py"]
    MediaCatalog["media_store/catalog.jsonl"] --> ETL
    ETL --> Duck[(DuckDB OLAP evidence_fact)]
    ETL --> Snapshot["dashboard/data.json"]
    Snapshot --> Api["api/server.py REST API"]
    Api --> OpenAPI["api/openapi.py OpenAPI contract"]
    Api --> ApiDocs["/api/docs + /api/openapi.json"]
    Api --> Dashboard["Stakeholder dashboard"]
    Snapshot -. fallback if API offline .-> Dashboard

    Dashboard --> Leadership[Leadership strategic view]
    Dashboard --> Investigations[Investigation workflow view]
    Dashboard --> Legal[Legal readiness view]
    Dashboard --> Partners[Masked CSO partner view]
    Dashboard --> DP[Data protection and monitoring]
    Dashboard --> AI[AI human-review queue]
    Dashboard --> Media[NoSQL media gallery]
```

Current local behavior: the browser dashboard prefers the REST API at `http://127.0.0.1:8770/api/dashboard` and falls back to `dashboard/data.json` if the API is offline. The next implementation step is to move `dashboard/app.js` to fetch role-shaped API responses from `/api/dashboard/{role}`.

## Schema Overview

`persons` is intentionally pseudonymous and connected through controlled relationship tables rather than direct identifying fields. This supports analysis while keeping protected identities compartmentalised.

- `incident_persons` links a protected person code to an incident as witness, victim, collector, reviewer, subject, or other relationship type.
- `media_persons` links a protected person code to a media item, including whether the person is visible in the media and the confidence of the relationship.
- Staff/action fields such as `reviewer_code`, `actor_code`, and `user_code` remain text codes in this demo because production identity integration would usually come from SSO/IAM and audit systems, not free joins to sensitive person records.

```mermaid
erDiagram
    ORGANISATIONS ||--o{ SOURCES : supports
    LOCATIONS ||--o{ INCIDENTS : locates
    INCIDENTS ||--o{ MEDIA_FILES : contains
    SOURCES ||--o{ MEDIA_FILES : submits
    PERSONS ||--o{ INCIDENT_PERSONS : involved_in
    INCIDENTS ||--o{ INCIDENT_PERSONS : has
    PERSONS ||--o{ MEDIA_PERSONS : linked_to
    MEDIA_FILES ||--o{ MEDIA_PERSONS : contains
    MEDIA_FILES ||--o{ CUSTODY_EVENTS : has
    MEDIA_FILES ||--o{ VERIFICATION_STEPS : has
    INCIDENTS ||--o{ VERIFICATION_STEPS : includes
    MEDIA_FILES ||--o{ ACCESS_LOGS : records
    MEDIA_FILES ||--o{ EXPORTS : produces
    ORGANISATIONS ||--o{ EXPORTS : receives
    MEDIA_FILES ||--o{ LEGAL_REVIEWS : reviewed_by
    INCIDENTS ||--o{ LEGAL_REVIEWS : has
    INCIDENTS ||--o{ INCIDENT_ALLEGED_ACTORS : references
    ALLEGED_ACTORS ||--o{ INCIDENT_ALLEGED_ACTORS : appears_in
    MEDIA_FILES ||--o{ MEDIA_TAGS : tagged
    TAGS ||--o{ MEDIA_TAGS : classifies
```

## diagrams.net / draw.io

Open diagrams.net, choose **File -> Import From -> Device**, then select:

```text
diagrams/hrt_architecture.drawio
```

For Mermaid-capable tools, use:

```text
diagrams/hrt_schema_erd.mmd
diagrams/hrt_oltp_olap_architecture.mmd
```

For dbdiagram.io, use DBML:

```text
diagrams/hrt_schema.dbml
```

Published dbdiagram link:

```text
https://dbdiagram.io/d/hrights-ngo-schema-6a1ac16ff15b4b045235d88d
```

## Database Manager Interview Framing

> My architecture keeps operational evidence handling separate from reporting and AI-assisted triage. PostgreSQL protects the authoritative evidence metadata and custody trail. The NoSQL/object-store layer handles media objects safely. DuckDB provides a rebuildable analytics layer for stakeholder dashboards. This gives teams practical visibility while protecting evidence integrity, source safety, and legal defensibility.
