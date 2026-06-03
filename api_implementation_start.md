# API Implementation Start

This is the first baby step toward turning the demo into a full-scale project.

## Why This Step First

The least-headwind first step is a small backend API that wraps the existing dashboard snapshot.

It is low cost because:

- No new cloud infrastructure is required.
- No new Python packages are required.
- No database schema change is required.
- The existing dashboard and ETL remain intact.
- It creates the foundation for JWT, API gateway, monitoring, and automated tests.

Estimated effort:

| Work | Timeline | Cost |
|---|---:|---:|
| Minimal local API | 1 day | Zero infrastructure cost |
| Basic API tests | 0.5 day | Zero infrastructure cost |
| Dashboard migration to API | 1-2 days | Zero infrastructure cost |
| JWT/RBAC proof of concept | 2-4 days | Usually zero to low cost with dev identity provider |

## Implemented Now

File:

```text
api/server.py
api/openapi.py
dashboard/app.js
```

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Confirms API and dashboard snapshot availability |
| `GET /api/dashboard` | Returns the full current dashboard snapshot |
| `GET /api/dashboard/{role}` | Returns a role-shaped dashboard response |
| `GET /api/anomalies` | Returns AI anomaly facts |
| `GET /api/notifications` | Returns notification delivery status |
| `GET /api/openapi.json` | Returns the OpenAPI 3.0 contract |
| `GET /api/docs` | Returns a simple browser-readable API documentation page |

Dashboard integration:

- `dashboard/app.js` now prefers `GET http://127.0.0.1:8770/api/dashboard`.
- If the API is offline, it falls back to `/dashboard/data.json`.
- The dashboard header shows `API online` or `API offline fallback`.

## How To Run

Make sure the reporting snapshot exists:

```bash
python3 scripts/refresh_olap.py
```

Start the API:

```bash
HRT_API_PORT=8770 python3 api/server.py
```

Open or test:

```text
http://127.0.0.1:8770/api/health
http://127.0.0.1:8770/api/dashboard/leadership
http://127.0.0.1:8770/api/anomalies
http://127.0.0.1:8770/api/notifications
http://127.0.0.1:8770/api/openapi.json
http://127.0.0.1:8770/api/docs
```

Command-line test:

```bash
curl http://127.0.0.1:8770/api/health
```

## What This Does Not Do Yet

- It does not implement JWT.
- It does not enforce server-side authorization.
- It does not replace the dashboard JSON fetch yet.
- It does not add an API gateway.
- It does not add a notification queue.
- It does not implement GraphQL or gRPC; this step is REST-style JSON over HTTP.

Those are the next steps.

## Next Baby Step

Move from full-snapshot API reads to role-specific API reads:

```text
/api/dashboard/{role}
```

That creates a cleaner path to JWT and server-side role filtering because each stakeholder tab can request only the read model it is allowed to see.
