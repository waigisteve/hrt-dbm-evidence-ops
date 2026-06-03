# Architecture Gap Assessment

This document shows how selected production architecture topics are represented in the HRT evidence operations demo, what is missing, and what would be required in a production implementation.

## Summary

| Topic | Current project status | Where to see it | Production gap |
|---|---|---|---|
| APIs | Not implemented as HTTP APIs | `scripts/refresh_olap.py`, `dashboard/server.py` | Replace script-only ETL and static JSON with service APIs for intake, dashboard reads, notifications, and health checks |
| API gateway | Not implemented | None | Add gateway/reverse proxy for routing, TLS, rate limiting, authentication, request logging, and WAF controls |
| JWT | Not implemented | `dashboard/index.html`, `dashboard/app.js` | Replace simulated login with OIDC/JWT validation and server-side authorization |
| Webhooks | Implemented outbound only | `scripts/notifications.py` | Add retry queues, idempotency keys, signing, backoff, and delivery audit table |
| Webhook scalability | Partially simulated | `scripts/notifications.py` | Move notification delivery to async workers/queue instead of blocking `refresh_olap.py` |
| Proxy | Documented for pgAdmin only | `pgadmin-wsl-postgresql-connection-guide.md` | Add production reverse proxy/API gateway pattern for dashboard/API access |
| SPOF | Present in several places | PostgreSQL local instance, `dashboard/data.json`, DuckDB file, local dashboard server | Add replication, backups, HA service deployment, queueing, and failover |
| CAP theorem | Not directly implemented | Architecture docs and OLTP/OLAP split | Define consistency/availability tradeoffs for evidence intake, reporting, and offline field collection |

## APIs

Current state:

- The project does not expose production REST or GraphQL APIs.
- The dashboard is served by `dashboard/server.py`, a Python static file server.
- The browser reads `dashboard/data.json` directly in `dashboard/app.js`.
- Data refresh is script-driven through `scripts/refresh_olap.py`.

Current flow:

```text
PostgreSQL hrt_prep
  -> scripts/refresh_olap.py
  -> olap/hrt_olap.duckdb
  -> dashboard/data.json
  -> dashboard/app.js
```

Production recommendation:

- Create API endpoints such as:
  - `POST /api/intake/media`
  - `GET /api/dashboard/leadership`
  - `GET /api/dashboard/investigations`
  - `GET /api/monitoring/anomalies`
  - `POST /api/notifications/test`
  - `GET /api/health`
- Keep raw evidence operations behind strict authentication and role-based authorization.
- Keep dashboard APIs read-only and filtered by stakeholder role.

## API Gateway

Current state:

- No API gateway is implemented.
- No reverse proxy, TLS termination, WAF, rate limiting, or centralized request logging exists in the demo.

Production recommendation:

Use an API gateway or reverse proxy such as NGINX, Kong, Traefik, Azure API Management, AWS API Gateway, or Cloudflare.

Responsibilities:

- TLS termination.
- Authentication handoff to identity provider.
- JWT validation or forwarding.
- Rate limiting.
- Request size limits for uploads.
- IP allowlisting for admin endpoints.
- Audit logging.
- Routing to API, dashboard, notification, and media services.

## JWT and Authentication

Current state:

- The dashboard has a simulated role selector and password field in `dashboard/index.html`.
- `dashboard/app.js` switches views in the browser.
- There is no real authentication, JWT, session management, MFA, or server-side authorization.
- `live_dashboard_runbook.md` explicitly notes this is not production authentication.

Production recommendation:

- Use OIDC with an identity provider such as Entra ID, Okta, Auth0, Keycloak, or Google Workspace.
- Issue JWT access tokens after login.
- Validate JWTs server-side before returning dashboard/API data.
- Map claims to roles:
  - `leadership`
  - `investigations`
  - `legal`
  - `partners`
  - `data_protection`
  - `monitoring`
  - `ai_review`
- Enforce authorization in the backend and database, not only in the UI.
- Add PostgreSQL row-level security where appropriate.

## Webhooks

Current state:

- Outbound Slack webhook delivery is implemented in `scripts/notifications.py`.
- Email delivery is implemented through SMTP in the same file.
- The alert payload is redacted and does not include raw media, precise locations, source names, hashes, or personal identifiers.
- Delivery results are exposed in `dashboard/data.json` and rendered in the AI Review dashboard.

Implemented behavior:

```text
AI anomaly detection
  -> threshold filter
  -> notification event
  -> Slack webhook and/or SMTP email
  -> delivery status in dashboard
```

Production gaps:

- No durable notification queue.
- No retry with exponential backoff.
- No idempotency key.
- No webhook signing for inbound webhooks.
- No delivery audit table in PostgreSQL.
- Notification sending currently happens inside the reporting refresh process.

Production recommendation:

- Add a notification table:
  - `notification_events`
  - `notification_deliveries`
  - `notification_retries`
- Move delivery to a worker service.
- Add retry and dead-letter handling.
- Store provider response metadata.
- Add idempotency keys so the same anomaly does not alert repeatedly.

## Webhook Scalability

Current state:

- Notifications are synchronous.
- If Slack or SMTP is slow, `refresh_olap.py` waits until timeout.
- Timeouts are configured by `HRT_NOTIFY_TIMEOUT_SECONDS`.

Production recommendation:

Use asynchronous processing:

```text
refresh_olap.py or API service
  -> writes notification event
  -> queue
  -> notification worker
  -> Slack/Gmail/provider
  -> delivery audit update
```

Suitable queue options:

- Redis Streams.
- RabbitMQ.
- Kafka.
- AWS SQS.
- Azure Service Bus.
- PostgreSQL-backed job queue for smaller deployments.

Operational controls:

- Retry budget.
- Dead-letter queue.
- Alert suppression window.
- Per-stakeholder rate limits.
- On-call escalation path.

## Proxy

Current state:

- `pgadmin-wsl-postgresql-connection-guide.md` documents a Windows port proxy attempt and SSH tunnel for pgAdmin.
- The dashboard itself does not sit behind a reverse proxy.

Production recommendation:

Use a reverse proxy/API gateway in front of:

- Dashboard.
- API service.
- Media preview service.
- Notification test endpoint.

The proxy should enforce:

- TLS.
- Security headers.
- Request body limits.
- Access logs.
- IP restrictions for admin routes.
- Rate limiting.
- Upstream health checks.

## SPOF: Single Points of Failure

Current SPOFs:

| Component | Why it is a SPOF |
|---|---|
| Local PostgreSQL | One local database instance |
| DuckDB file | Single reporting file |
| `dashboard/data.json` | Single generated dashboard snapshot |
| `dashboard/server.py` | One local process |
| Notification execution | Runs inside refresh process |
| Slack/Gmail providers | External provider dependency |
| Local media store | Single file-backed catalog |

Production mitigations:

- PostgreSQL backups, PITR, and replication.
- Separate reporting service or replicated OLAP store.
- Object storage with versioning and lifecycle policies.
- Dashboard service deployed with multiple replicas.
- Notification queue and workers.
- Multi-channel alerting with fallback.
- Health checks and uptime monitoring.
- Disaster recovery runbook.

## CAP Theorem

The CAP theorem says that under network partition, a distributed system must choose between consistency and availability.

Current demo:

- Mostly single-node, so CAP tradeoffs are not directly exercised.
- The OLTP/OLAP split demonstrates consistency boundaries:
  - PostgreSQL is the authoritative operational store.
  - DuckDB and `dashboard/data.json` are rebuildable reporting snapshots.
  - Dashboards may be slightly stale but should not mutate evidence.

Production interpretation for HRT:

| Workflow | Preferred tradeoff | Reason |
|---|---|---|
| Chain of custody | Consistency over availability | Incorrect custody records can damage evidentiary value |
| Evidence hash validation | Consistency over availability | Integrity must be defensible |
| Field/offline collection | Availability first, then reconciliation | Field teams may work during shutdowns or poor connectivity |
| Dashboard reporting | Availability with bounded staleness | Stakeholders can tolerate a refresh delay |
| Legal export | Consistency over availability | Export packs must be accurate and auditable |
| Notifications | Availability with deduplication | Alerts should be sent, but duplicates must be controlled |

Production recommendation:

- Treat the operational evidence database as the consistency anchor.
- Allow offline/field systems to collect locally with signed records and later reconciliation.
- Mark dashboard data with `generated_at` and source snapshot metadata.
- Use custody/hash validation before legal use.
- Make eventual consistency explicit in stakeholder dashboards.

## Interview Positioning

Use this explanation:

> This demo intentionally implements the evidence workflow rather than a full production platform. It has script-based ETL, a static dashboard read model, outbound Slack/email alerts, and simulated login. In production I would add APIs, an API gateway, OIDC/JWT authentication, server-side RBAC, queued webhook delivery, reverse proxy controls, high availability, and explicit CAP tradeoffs for field collection versus evidentiary integrity.

