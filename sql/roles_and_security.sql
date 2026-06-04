-- Least-privilege roles, append-only audit enforcement, and row-level security.
--
-- Run this AFTER schema.sql, once the tables and sequences exist. It replaces
-- the implicit "everything runs as the postgres superuser" posture with three
-- purpose-built roles:
--
--   hrt_app       OLTP read/write for operational/intake systems and the
--                 simulator. Can INSERT/SELECT/UPDATE operational tables, but
--                 only INSERT/SELECT on the audit tables (append-only).
--   hrt_etl       Read-only reporting role used by scripts/refresh_olap.py. It
--                 is the trusted redaction boundary: it can read everything but
--                 write nothing.
--   hrt_partner   Least-privilege partner-portal role. Under row-level security
--                 it cannot see media classified 'restricted'.
--
-- IMPORTANT: the placeholder passwords below MUST be rotated before any non-demo
-- use. Set real secrets out of band, e.g.:
--   ALTER ROLE hrt_app    PASSWORD '...';
--   ALTER ROLE hrt_etl    PASSWORD '...';
--   ALTER ROLE hrt_partner PASSWORD '...';
-- and require scram-sha-256 in pg_hba.conf (see live_dashboard_runbook.md).
--
-- NOTE: the superuser bypasses GRANTs and RLS, so the default demo flow
-- (sudo -u postgres) keeps working unchanged. These controls take effect when
-- the scripts connect as the dedicated roles via the HRT_PG_* environment
-- variables documented in the README.

-- ---------------------------------------------------------------------------
-- Roles (idempotent)
-- ---------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hrt_app') THEN
        CREATE ROLE hrt_app LOGIN PASSWORD 'change-me-app';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hrt_etl') THEN
        CREATE ROLE hrt_etl LOGIN PASSWORD 'change-me-etl';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hrt_partner') THEN
        CREATE ROLE hrt_partner LOGIN PASSWORD 'change-me-partner';
    END IF;
END;
$$;

GRANT USAGE ON SCHEMA public TO hrt_app, hrt_etl, hrt_partner;

-- ---------------------------------------------------------------------------
-- hrt_etl: read-only across the operational estate (the redaction boundary).
-- ---------------------------------------------------------------------------
GRANT SELECT ON ALL TABLES IN SCHEMA public TO hrt_etl;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO hrt_etl;

-- ---------------------------------------------------------------------------
-- hrt_app: read/write on operational tables.
-- ---------------------------------------------------------------------------
GRANT SELECT, INSERT, UPDATE ON
    locations, organisations, sources, persons, incidents,
    incident_persons, alleged_actors, incident_alleged_actors,
    media_files, media_persons, tags, media_tags, exports
TO hrt_app;

-- Append-only audit/integrity tables: INSERT + SELECT only. No UPDATE/DELETE is
-- granted, so the application role cannot rewrite or erase history even if a
-- bug or compromised credential tries to.
GRANT SELECT, INSERT ON
    custody_events, access_logs, verification_steps, legal_reviews
TO hrt_app;

-- Sequences needed for BIGSERIAL inserts and currval().
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO hrt_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO hrt_app;

-- ---------------------------------------------------------------------------
-- Row-level security: restricted media is hidden from the partner role.
-- RLS is demonstrated on media_files. Trusted internal roles (hrt_app, hrt_etl)
-- get a permissive ALL policy; the partner role only sees non-restricted rows.
-- The table owner / superuser bypass RLS unless FORCE is set, so the demo
-- default flow is unaffected.
-- ---------------------------------------------------------------------------
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS media_files_internal ON media_files;
CREATE POLICY media_files_internal ON media_files
    FOR ALL TO hrt_app, hrt_etl
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS media_files_partner ON media_files;
CREATE POLICY media_files_partner ON media_files
    FOR SELECT TO hrt_partner
    USING (access_classification <> 'restricted');

-- Partner role may read a redacted subset of media only.
GRANT SELECT ON media_files TO hrt_partner;
