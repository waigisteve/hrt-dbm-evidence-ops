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
```

Endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Confirms API and dashboard snapshot availability |
| `GET /api/dashboard` | Returns the full current dashboard snapshot |
| `GET /api/dashboard/{role}` | Returns a role-shaped dashboard response |
| `GET /api/anomalies` | Returns AI anomaly facts |
| `GET /api/notifications` | Returns notification delivery status |

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

Those are the next steps.

## Next Baby Step

Update `dashboard/app.js` so it fetches from:

```text
/api/dashboard/{role}
```

instead of reading the full `dashboard/data.json` directly.

That creates a clean path to add JWT and server-side role filtering.

