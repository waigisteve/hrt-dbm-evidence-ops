# Security, Reliability & Scalability Hardening

This document records the hardening patches applied to the HRT prep pack after a
critical review. Each entry states the original weakness, the fix, and the
files touched. The guiding principle was to make the controls the pack already
*describes* (chain of custody, redaction, least privilege, masking) actually
*enforced* in code — while keeping the out-of-the-box demo runnable.

> Compatibility note: the PostgreSQL scripts still fall back to
> `sudo -u postgres` when no `HRT_*` connection env vars are set, and the
> superuser bypasses both GRANTs and RLS. So the quick-start flow is unchanged;
> the new controls take effect when you connect as the dedicated roles.

---

## Security

### S1 — Audit/custody trail is no longer destroyable
- **Was:** `custody_events`, `access_logs`, `verification_steps`, and
  `legal_reviews` referenced `media_files`/`incidents` with `ON DELETE CASCADE`.
  Deleting one media row silently wiped its entire chain of custody, access log,
  and verification/legal history.
- **Now:** those foreign keys use `ON DELETE RESTRICT` — evidence that still has
  audit history cannot be deleted. `sql/roles_and_security.sql` additionally
  grants the application role **INSERT + SELECT only** on these tables, so even a
  bug or stolen credential cannot UPDATE/DELETE history.
- **Files:** `sql/schema.sql`, `sql/roles_and_security.sql`

### S2 — Least-privilege database roles (no more "everything as superuser")
- **Was:** every script shelled out via `sudo -u postgres psql`; the read-only
  reporting refresh ran with full superuser rights. The schema had zero roles.
- **Now:** `sql/roles_and_security.sql` creates `hrt_app` (OLTP read/write),
  `hrt_etl` (read-only reporting boundary), and `hrt_partner` (partner portal).
  `scripts/db.py` builds the psql connection for the role a script needs from
  `HRT_*` env vars, reading the password from `PGPASSWORD` (never the command
  line). `refresh_olap.py` uses `etl`; `simulate_continuous_intake.py` uses `app`.
- **Files:** `scripts/db.py`, `scripts/refresh_olap.py`,
  `scripts/simulate_continuous_intake.py`, `sql/roles_and_security.sql`

### S3 — Row-level security on restricted media
- **Was:** `access_classification`/`sensitivity` columns were decorative; nothing
  enforced them at the database layer.
- **Now:** RLS is enabled on `media_files`. Trusted internal roles get a
  permissive policy; `hrt_partner` can only `SELECT` rows where
  `access_classification <> 'restricted'`.
- **Files:** `sql/roles_and_security.sql`

### S4 — Dashboard server no longer exposes the whole repo
- **Was:** `dashboard/server.py` served the entire pack root, so `sql/`,
  `scripts/`, runtime state, and docs were all downloadable, unauthenticated.
- **Now:** only `/dashboard/` and `/media_store/` paths are served; everything
  else returns 404. Added `X-Content-Type-Options`, `X-Frame-Options`, and
  `Referrer-Policy` headers.
- **Files:** `dashboard/server.py`
- **Current limitation:** the clean repo now has local demo token/RBAC on the
  API, but this is not production OIDC/JWT. For real use, put the dashboard/API
  behind a production identity provider and reverse proxy, validate provider
  JWTs server-side, and keep per-role snapshots enforced by the backend.

### S5 — Stored XSS in the dashboard
- **Was:** `table()` and several render functions interpolated intake-derived
  values (filenames, incident codes, MIME types) into `innerHTML` unescaped. A
  crafted filename would execute script in an analyst's browser.
- **Now:** `human()` escapes its output, `status()`/`severity()` escape the class
  attribute, and every raw value at a `table()`/card call site is wrapped in
  `escapeHtml`. Image `src` attributes are escaped too.
- **Files:** `dashboard/app.js`

### S6 — SVG generation escapes attribute contexts
- **Was:** `escape()` in `sync_media_catalog.py` handled `& < >` but not quotes.
- **Now:** it also escapes `"` and `'`, so a crafted incident code/filename
  cannot break out of generated SVG markup.
- **Files:** `scripts/sync_media_catalog.py`

### S7 — No secret leakage into the browser snapshot
- **Was:** notification delivery failures wrote raw exception text (which can
  contain webhook URLs or SMTP hosts) into `data.json`, which is served to the
  browser.
- **Now:** failures are logged to stderr; the snapshot carries only a generic
  "see server logs" status.
- **Files:** `scripts/notifications.py`

---

## Reliability

### R1 — Atomic file writes
- **Was:** `data.json` and `catalog.jsonl` were written in place while the
  dashboard polls `data.json` every 5s — a poll mid-write got truncated JSON.
- **Now:** both are written to a temp file and `os.replace()`d in atomically.
- **Files:** `scripts/refresh_olap.py`, `scripts/sync_media_catalog.py`

### R2 — Transactional OLAP rebuild
- **Was:** `DROP TABLE` + `CREATE` + `INSERT` was non-atomic; a crash mid-rebuild
  left an empty/partial fact table.
- **Now:** the rebuild runs in a transaction, populates `evidence_fact_new`, then
  atomically renames it over `evidence_fact`.
- **Files:** `scripts/refresh_olap.py`

### R3 — Transactional intake batches
- **Was:** batch statements ran in autocommit; a mid-batch failure left orphaned
  organisation/source/location rows.
- **Now:** each batch is wrapped in `BEGIN/COMMIT` with `ON_ERROR_STOP=1`.
- **Files:** `scripts/simulate_continuous_intake.py`

### R4 — No silent data loss in reporting
- **Was:** the reporting query used `JOIN incidents`, so any media without an
  incident silently vanished from the dashboard and OLAP.
- **Now:** `LEFT JOIN incidents` with `COALESCE` to an `UNASSIGNED` placeholder.
- **Files:** `scripts/refresh_olap.py`

### R5 — Trustworthy `updated_at`
- **Was:** `incidents.updated_at` was set once at insert and never updated.
- **Now:** a `set_updated_at()` trigger maintains `updated_at` on `incidents` and
  on `media_files` (new column).
- **Files:** `sql/schema.sql`

---

## Scalability

### P1 — Idempotent media catalog sync
- **Was:** every batch regenerated and re-hashed *every* asset — O(n²) over a
  simulation run.
- **Now:** assets are only (re)created and re-hashed when new or changed; existing
  unchanged assets reuse their prior scan result. Cost is now proportional to new
  intake.
- **Files:** `scripts/sync_media_catalog.py`

### P2 — JSONB index
- **Was:** `metadata_json` was queried with no supporting index.
- **Now:** a GIN index `idx_media_metadata_json` supports metadata queries.
- **Files:** `sql/schema.sql`

---

## Known limitations still worth addressing for production

- The dashboard/API has local demo token/RBAC, not production OIDC/JWT. Real
  deployments should validate provider JWTs, use MFA/conditional access, and
  serve per-role redacted snapshots behind an authenticating proxy or gateway.
- The OLAP refresh is still a full rebuild, not incremental/CDC.
- `pg_hba.conf` uses `trust` and there is no TLS or encryption at rest. These are
  runtime/infra concerns: require `scram-sha-256`, enable TLS, and consider
  column encryption for `protection_notes`/`security_notes` before real data.
- SQL is still assembled by string interpolation (with quote-escaping) rather
  than bound parameters, because the scripts shell out to `psql`. A production
  pipeline should use a driver (e.g. `psycopg`) with parameterized queries.
