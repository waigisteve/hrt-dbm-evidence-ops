-- PostgreSQL schema for a fictional Videre-style investigative evidence system.
-- The closed-source video system remains the system of record for original media.
-- This relational layer supports cross-referencing, verification, governance, and reporting.

CREATE TYPE sensitivity_level AS ENUM ('low', 'medium', 'high', 'restricted');
CREATE TYPE verification_status AS ENUM ('unverified', 'partially_verified', 'verified', 'disputed', 'rejected');
CREATE TYPE custody_event_type AS ENUM ('collected', 'transferred', 'ingested', 'reviewed', 'exported', 'archived', 'deleted');
CREATE TYPE legal_review_status AS ENUM ('not_reviewed', 'needs_review', 'approved_for_legal_use', 'restricted_use', 'do_not_use');

CREATE TABLE locations (
    location_id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL,
    admin_area TEXT,
    locality TEXT,
    latitude NUMERIC(9, 6),
    longitude NUMERIC(9, 6),
    geolocation_confidence SMALLINT CHECK (geolocation_confidence BETWEEN 0 AND 100),
    notes TEXT
);

CREATE TABLE organisations (
    organisation_id BIGSERIAL PRIMARY KEY,
    organisation_name TEXT NOT NULL,
    organisation_type TEXT NOT NULL,
    country_code CHAR(2),
    security_notes TEXT
);

CREATE TABLE sources (
    source_id BIGSERIAL PRIMARY KEY,
    source_code TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    partner_organisation_id BIGINT REFERENCES organisations (organisation_id),
    reliability_rating SMALLINT CHECK (reliability_rating BETWEEN 1 AND 5),
    risk_level sensitivity_level NOT NULL DEFAULT 'high',
    contact_restricted BOOLEAN NOT NULL DEFAULT true,
    notes TEXT
);

CREATE TABLE persons (
    person_id BIGSERIAL PRIMARY KEY,
    person_code TEXT NOT NULL UNIQUE,
    person_role TEXT NOT NULL,
    sensitivity sensitivity_level NOT NULL DEFAULT 'restricted',
    protection_notes TEXT
);

CREATE TABLE incidents (
    incident_id BIGSERIAL PRIMARY KEY,
    incident_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    occurred_at TIMESTAMPTZ,
    location_id BIGINT REFERENCES locations (location_id),
    summary TEXT,
    verification_status verification_status NOT NULL DEFAULT 'unverified',
    sensitivity sensitivity_level NOT NULL DEFAULT 'high',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE incident_persons (
    incident_id BIGINT NOT NULL REFERENCES incidents (incident_id) ON DELETE CASCADE,
    person_id BIGINT NOT NULL REFERENCES persons (person_id),
    relationship_type TEXT NOT NULL,
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    protection_level sensitivity_level NOT NULL DEFAULT 'restricted',
    notes TEXT,
    PRIMARY KEY (incident_id, person_id, relationship_type)
);

CREATE TABLE alleged_actors (
    alleged_actor_id BIGSERIAL PRIMARY KEY,
    actor_name TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE incident_alleged_actors (
    incident_id BIGINT NOT NULL REFERENCES incidents (incident_id) ON DELETE CASCADE,
    alleged_actor_id BIGINT NOT NULL REFERENCES alleged_actors (alleged_actor_id),
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    basis TEXT NOT NULL,
    PRIMARY KEY (incident_id, alleged_actor_id)
);

CREATE TABLE media_files (
    media_id BIGSERIAL PRIMARY KEY,
    external_video_system_id TEXT UNIQUE,
    incident_id BIGINT REFERENCES incidents (incident_id),
    source_id BIGINT REFERENCES sources (source_id),
    original_filename TEXT NOT NULL,
    media_type TEXT NOT NULL CHECK (media_type IN ('video', 'photo', 'audio', 'document')),
    file_sha256 CHAR(64) NOT NULL,
    captured_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ NOT NULL,
    storage_uri TEXT NOT NULL,
    access_classification sensitivity_level NOT NULL DEFAULT 'high',
    retention_category TEXT NOT NULL,
    verification_status verification_status NOT NULL DEFAULT 'unverified',
    legal_status legal_review_status NOT NULL DEFAULT 'not_reviewed',
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE media_persons (
    media_id BIGINT NOT NULL REFERENCES media_files (media_id) ON DELETE CASCADE,
    person_id BIGINT NOT NULL REFERENCES persons (person_id),
    relationship_type TEXT NOT NULL,
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    visible_in_media BOOLEAN NOT NULL DEFAULT false,
    protection_level sensitivity_level NOT NULL DEFAULT 'restricted',
    notes TEXT,
    PRIMARY KEY (media_id, person_id, relationship_type)
);

CREATE TABLE verification_steps (
    verification_step_id BIGSERIAL PRIMARY KEY,
    media_id BIGINT REFERENCES media_files (media_id) ON DELETE CASCADE,
    incident_id BIGINT REFERENCES incidents (incident_id) ON DELETE CASCADE,
    step_type TEXT NOT NULL,
    method TEXT NOT NULL,
    result verification_status NOT NULL,
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    reviewer_code TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    notes TEXT
);

CREATE TABLE custody_events (
    custody_event_id BIGSERIAL PRIMARY KEY,
    media_id BIGINT NOT NULL REFERENCES media_files (media_id) ON DELETE CASCADE,
    event_type custody_event_type NOT NULL,
    event_at TIMESTAMPTZ NOT NULL,
    actor_code TEXT NOT NULL,
    from_holder TEXT,
    to_holder TEXT,
    transfer_method TEXT,
    event_hash CHAR(64),
    reason TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE access_logs (
    access_log_id BIGSERIAL PRIMARY KEY,
    media_id BIGINT REFERENCES media_files (media_id) ON DELETE CASCADE,
    user_code TEXT NOT NULL,
    action TEXT NOT NULL,
    purpose TEXT NOT NULL,
    accessed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ip_context TEXT
);

CREATE TABLE exports (
    export_id BIGSERIAL PRIMARY KEY,
    media_id BIGINT NOT NULL REFERENCES media_files (media_id),
    recipient_organisation_id BIGINT REFERENCES organisations (organisation_id),
    purpose TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    exported_at TIMESTAMPTZ NOT NULL,
    export_format TEXT NOT NULL,
    redaction_applied BOOLEAN NOT NULL DEFAULT true,
    export_sha256 CHAR(64),
    transfer_method TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE tags (
    tag_id BIGSERIAL PRIMARY KEY,
    tag_name TEXT NOT NULL UNIQUE,
    tag_type TEXT NOT NULL
);

CREATE TABLE media_tags (
    media_id BIGINT NOT NULL REFERENCES media_files (media_id) ON DELETE CASCADE,
    tag_id BIGINT NOT NULL REFERENCES tags (tag_id),
    tagged_by TEXT NOT NULL,
    tagged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (media_id, tag_id)
);

CREATE TABLE legal_reviews (
    legal_review_id BIGSERIAL PRIMARY KEY,
    media_id BIGINT REFERENCES media_files (media_id) ON DELETE CASCADE,
    incident_id BIGINT REFERENCES incidents (incident_id) ON DELETE CASCADE,
    status legal_review_status NOT NULL,
    reviewer_code TEXT NOT NULL,
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    restrictions TEXT,
    evidentiary_notes TEXT
);

CREATE INDEX idx_media_incident ON media_files (incident_id);
CREATE INDEX idx_media_source ON media_files (source_id);
CREATE INDEX idx_media_sha256 ON media_files (file_sha256);
CREATE INDEX idx_media_status ON media_files (verification_status, legal_status);
CREATE INDEX idx_media_received_at ON media_files (received_at);
CREATE INDEX idx_incident_persons_person ON incident_persons (person_id);
CREATE INDEX idx_media_persons_person ON media_persons (person_id);
CREATE INDEX idx_custody_media_event_at ON custody_events (media_id, event_at);
CREATE INDEX idx_verification_media ON verification_steps (media_id, reviewed_at);
CREATE INDEX idx_incidents_location_time ON incidents (location_id, occurred_at);
CREATE INDEX idx_access_logs_media_time ON access_logs (media_id, accessed_at);
