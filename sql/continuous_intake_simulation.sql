-- Continuous intake simulation for the HRT preparation database.
-- Run inside hrt_prep after schema.sql and sample_data.sql.

INSERT INTO organisations (organisation_name, organisation_type, country_code, security_notes)
VALUES ('Riverline Documentation Network', 'CSO partner', 'KE', 'Fictional low-connectivity partner using offline handover.');

INSERT INTO sources (source_code, source_type, partner_organisation_id, reliability_rating, risk_level, notes)
SELECT
    'SRC-NL-004',
    'CSO partner submission',
    organisation_id,
    3,
    'restricted',
    'Fictional source submitting imagery and field notes via offline handover.'
FROM organisations
WHERE organisation_name = 'Riverline Documentation Network';

INSERT INTO locations (country_code, admin_area, locality, latitude, longitude, geolocation_confidence, notes)
VALUES ('KE', 'Central Region', 'Riverline Bus Stage', -0.430000, 36.970000, 60, 'Fictional new intake location.');

INSERT INTO incidents (
    incident_code,
    title,
    incident_type,
    occurred_at,
    location_id,
    summary,
    verification_status,
    sensitivity
)
VALUES (
    'INC-NL-004',
    'Riverline Bus Stage night operation',
    'night operation',
    '2026-02-24 21:15:00+03',
    currval('locations_location_id_seq'),
    'Fictional new incident received through continuous intake.',
    'unverified',
    'restricted'
);

INSERT INTO media_files (
    external_video_system_id,
    incident_id,
    source_id,
    original_filename,
    media_type,
    file_sha256,
    captured_at,
    received_at,
    storage_uri,
    access_classification,
    retention_category,
    verification_status,
    legal_status,
    metadata_json
)
SELECT
    'VIDSYS-0006',
    i.incident_id,
    s.source_id,
    'riverline_video_006.mp4',
    'video',
    repeat('f', 64),
    '2026-02-24 21:18:00+03',
    now(),
    'secure://evidence/project-northlight/006',
    'restricted',
    'legal_hold_review',
    'unverified',
    'needs_review',
    '{"duration_seconds":31,"device_time_present":true,"gps_embedded":false}'::jsonb
FROM incidents i
JOIN sources s ON s.source_code = 'SRC-NL-004'
WHERE i.incident_code = 'INC-NL-004';

INSERT INTO media_files (
    external_video_system_id,
    incident_id,
    source_id,
    original_filename,
    media_type,
    file_sha256,
    captured_at,
    received_at,
    storage_uri,
    access_classification,
    retention_category,
    verification_status,
    legal_status,
    metadata_json
)
SELECT
    'VIDSYS-0007',
    i.incident_id,
    s.source_id,
    'riverline_image_007.jpg',
    'photo',
    repeat('7', 64),
    '2026-02-24 21:20:00+03',
    now(),
    'secure://evidence/project-northlight/007',
    'restricted',
    'legal_hold_review',
    'unverified',
    'needs_review',
    '{"exif_present":true,"gps_embedded":false}'::jsonb
FROM incidents i
JOIN sources s ON s.source_code = 'SRC-NL-004'
WHERE i.incident_code = 'INC-NL-004';

INSERT INTO media_files (
    external_video_system_id,
    incident_id,
    source_id,
    original_filename,
    media_type,
    file_sha256,
    captured_at,
    received_at,
    storage_uri,
    access_classification,
    retention_category,
    verification_status,
    legal_status,
    metadata_json
)
SELECT
    'VIDSYS-0008',
    i.incident_id,
    s.source_id,
    'riverline_field_note_008.txt',
    'document',
    repeat('8', 64),
    NULL,
    now(),
    'secure://evidence/project-northlight/008',
    'restricted',
    'source_risk_review',
    'unverified',
    'restricted_use',
    '{}'::jsonb
FROM incidents i
JOIN sources s ON s.source_code = 'SRC-NL-004'
WHERE i.incident_code = 'INC-NL-004';

INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes)
SELECT media_id, 'collected', captured_at, 'SRC-NL-004', NULL, 'SRC-NL-004', 'device capture', file_sha256, 'Original collection.', 'Continuous intake simulation.'
FROM media_files
WHERE external_video_system_id IN ('VIDSYS-0006', 'VIDSYS-0007');

INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes)
SELECT media_id, 'transferred', received_at - INTERVAL '1 hour', 'SRC-NL-004', 'SRC-NL-004', 'secure intake', 'offline encrypted handover', file_sha256, 'Secure offline partner handover.', 'Continuous intake simulation.'
FROM media_files
WHERE external_video_system_id IN ('VIDSYS-0006', 'VIDSYS-0007');

INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes)
SELECT media_id, 'ingested', received_at, 'PRS-INV-001', 'secure intake', 'video system', 'controlled ingest', file_sha256, 'Evidence intake.', 'Continuous intake simulation.'
FROM media_files
WHERE external_video_system_id IN ('VIDSYS-0006', 'VIDSYS-0007');

INSERT INTO verification_steps (media_id, incident_id, step_type, method, result, confidence, reviewer_code, notes)
SELECT
    m.media_id,
    m.incident_id,
    'technical_review',
    'Hash check, metadata extraction, and duplicate scan.',
    'partially_verified',
    55,
    'PRS-INV-001',
    'No duplicate hash found; location and time still need corroboration.'
FROM media_files m
WHERE m.external_video_system_id IN ('VIDSYS-0006', 'VIDSYS-0007');

INSERT INTO tags (tag_name, tag_type)
VALUES ('night_operation', 'incident_feature'), ('offline_handover', 'transfer_feature')
ON CONFLICT (tag_name) DO NOTHING;

INSERT INTO media_tags (media_id, tag_id, tagged_by)
SELECT m.media_id, t.tag_id, 'PRS-INV-001'
FROM media_files m
JOIN tags t ON t.tag_name IN ('night_operation', 'offline_handover')
WHERE m.external_video_system_id IN ('VIDSYS-0006', 'VIDSYS-0007')
ON CONFLICT DO NOTHING;

UPDATE incidents
SET verification_status = 'partially_verified',
    updated_at = now()
WHERE incident_code = 'INC-NL-004';

SELECT
    i.incident_code,
    i.title,
    COUNT(m.media_id) AS received_items,
    COUNT(*) FILTER (WHERE m.media_type = 'video') AS videos,
    COUNT(*) FILTER (WHERE m.media_type = 'photo') AS images,
    COUNT(*) FILTER (WHERE m.media_type = 'document') AS documents,
    COUNT(*) FILTER (WHERE m.verification_status = 'unverified') AS unverified_items,
    COUNT(*) FILTER (WHERE m.legal_status = 'restricted_use') AS restricted_use_items
FROM incidents i
JOIN media_files m ON m.incident_id = i.incident_id
WHERE i.incident_code = 'INC-NL-004'
GROUP BY i.incident_code, i.title;
