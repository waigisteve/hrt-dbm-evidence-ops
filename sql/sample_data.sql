-- Fictional practice data for Project Northlight.
-- All names, codes, locations, and file references are invented.

INSERT INTO organisations (organisation_name, organisation_type, country_code, security_notes) VALUES
('Northlight Civil Society Partner', 'CSO partner', 'KE', 'Fictional partner for practice only.'),
('Accountability Legal Review Group', 'legal reviewer', 'GB', 'Fictional legal review recipient.'),
('Secure Video Vendor', 'technology vendor', 'GB', 'Fictional closed-source video platform vendor.');

INSERT INTO locations (country_code, admin_area, locality, latitude, longitude, geolocation_confidence, notes) VALUES
('KE', 'Central Region', 'Kijani Market', -0.416100, 36.951200, 80, 'Fictional public market location.'),
('KE', 'Central Region', 'Mtoni Road Junction', -0.420500, 36.960100, 70, 'Fictional road junction.'),
('UG', 'Eastern Region', 'Naluba Trading Centre', 0.612000, 33.482000, 65, 'Fictional cross-border comparison location.');

INSERT INTO sources (source_code, source_type, partner_organisation_id, reliability_rating, risk_level, notes) VALUES
('SRC-NL-001', 'trained field collector', 1, 4, 'restricted', 'Uses secure handover route.'),
('SRC-NL-002', 'community witness', 1, 3, 'high', 'Identity restricted.'),
('SRC-NL-003', 'partner monitor', 1, 4, 'high', 'Provides contextual notes and time checks.');

INSERT INTO persons (person_code, person_role, sensitivity, protection_notes) VALUES
('PRS-INV-001', 'investigator', 'high', 'Internal fictional user code.'),
('PRS-LEG-001', 'legal reviewer', 'high', 'Internal fictional user code.'),
('PRS-FLD-001', 'field collector', 'restricted', 'Identity should not be disclosed.');

INSERT INTO alleged_actors (actor_name, actor_type, notes) VALUES
('Unit Alpha', 'security unit', 'Fictional alleged actor.'),
('Local Auxiliary Group', 'non-state group', 'Fictional alleged actor.');

INSERT INTO incidents (
    incident_code,
    title,
    incident_type,
    occurred_at,
    location_id,
    summary,
    verification_status,
    sensitivity
) VALUES
('INC-NL-001', 'Kijani Market dispersal', 'political violence', '2026-02-14 15:30:00+03', 1, 'Fictional incident involving crowd dispersal.', 'partially_verified', 'restricted'),
('INC-NL-002', 'Mtoni Road checkpoint abuse', 'abuse at checkpoint', '2026-02-16 18:10:00+03', 2, 'Fictional incident involving alleged abuse at a checkpoint.', 'verified', 'high'),
('INC-NL-003', 'Naluba comparison incident', 'political violence', '2026-02-21 11:20:00+03', 3, 'Fictional comparison incident for pattern analysis.', 'unverified', 'high');

INSERT INTO incident_alleged_actors (incident_id, alleged_actor_id, confidence, basis) VALUES
((SELECT incident_id FROM incidents WHERE incident_code = 'INC-NL-001'), 1, 70, 'Uniform and vehicle markings visible in footage.'),
((SELECT incident_id FROM incidents WHERE incident_code = 'INC-NL-002'), 1, 85, 'Two independent source accounts and visible insignia.'),
((SELECT incident_id FROM incidents WHERE incident_code = 'INC-NL-003'), 2, 50, 'Single-source contextual claim.');

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
) VALUES
('VIDSYS-0001', 1, 1, 'northlight_clip_001.mp4', 'video', repeat('a', 64), '2026-02-14 15:34:00+03', '2026-02-14 19:05:00+03', 'secure://evidence/project-northlight/001', 'restricted', 'legal_hold_review', 'partially_verified', 'needs_review', '{"device_time":"2026-02-14T15:34:00+03:00","duration_seconds":42}'),
('VIDSYS-0002', 1, 2, 'northlight_photo_002.jpg', 'photo', repeat('b', 64), '2026-02-14 15:36:00+03', '2026-02-15 08:20:00+03', 'secure://evidence/project-northlight/002', 'high', 'case_retention_7_years', 'unverified', 'not_reviewed', '{"exif_present":true}'),
('VIDSYS-0003', 2, 3, 'mtoni_clip_003.mp4', 'video', repeat('c', 64), '2026-02-16 18:12:00+03', '2026-02-16 22:01:00+03', 'secure://evidence/project-northlight/003', 'high', 'legal_hold_review', 'verified', 'approved_for_legal_use', '{"duration_seconds":67,"gps_embedded":false}'),
('VIDSYS-0004', 2, 1, 'mtoni_clip_004_duplicate.mp4', 'video', repeat('c', 64), '2026-02-16 18:12:00+03', '2026-02-17 09:30:00+03', 'secure://evidence/project-northlight/004', 'high', 'legal_hold_review', 'verified', 'approved_for_legal_use', '{"duplicate_candidate":true}'),
('VIDSYS-0005', 3, 2, 'naluba_note_005.txt', 'document', repeat('d', 64), NULL, '2026-02-22 12:00:00+03', 'secure://evidence/project-northlight/005', 'restricted', 'review_required', 'unverified', 'restricted_use', '{}');

INSERT INTO verification_steps (media_id, incident_id, step_type, method, result, confidence, reviewer_code, notes) VALUES
(1, 1, 'chronolocation', 'Compared shadow position and local event timing.', 'partially_verified', 65, 'PRS-INV-001', 'Time broadly plausible; needs second source.'),
(3, 2, 'geolocation', 'Matched storefront and road layout to approved map source.', 'verified', 85, 'PRS-INV-001', 'Location confirmed.'),
(3, 2, 'corroboration', 'Matched with independent source note and second video.', 'verified', 80, 'PRS-INV-001', 'Two-source corroboration achieved.'),
(4, 2, 'duplicate_review', 'Hash matched media VIDSYS-0003.', 'verified', 100, 'PRS-INV-001', 'Duplicate intake path identified.');

INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes) VALUES
(1, 'collected', '2026-02-14 15:34:00+03', 'PRS-FLD-001', NULL, 'SRC-NL-001', 'device capture', repeat('a', 64), 'Original collection.', 'Fictional event.'),
(1, 'transferred', '2026-02-14 18:40:00+03', 'SRC-NL-001', 'SRC-NL-001', 'secure intake', 'encrypted upload', repeat('a', 64), 'Secure submission.', 'Fictional event.'),
(1, 'ingested', '2026-02-14 19:05:00+03', 'PRS-INV-001', 'secure intake', 'video system', 'controlled ingest', repeat('a', 64), 'Evidence intake.', 'Fictional event.'),
(3, 'collected', '2026-02-16 18:12:00+03', 'SRC-NL-003', NULL, 'SRC-NL-003', 'device capture', repeat('c', 64), 'Original collection.', 'Fictional event.'),
(3, 'ingested', '2026-02-16 22:01:00+03', 'PRS-INV-001', 'secure intake', 'video system', 'controlled ingest', repeat('c', 64), 'Evidence intake.', 'Fictional event.'),
(3, 'reviewed', '2026-02-17 10:00:00+03', 'PRS-LEG-001', 'video system', 'legal review', 'controlled access', repeat('c', 64), 'Legal readiness review.', 'Fictional event.'),
(4, 'ingested', '2026-02-17 09:30:00+03', 'PRS-INV-001', 'secure intake', 'video system', 'controlled ingest', repeat('c', 64), 'Duplicate evidence intake.', 'Fictional event.');

INSERT INTO access_logs (media_id, user_code, action, purpose, ip_context) VALUES
(1, 'PRS-INV-001', 'view', 'verification review', 'approved-vpn'),
(3, 'PRS-INV-001', 'view', 'verification review', 'approved-vpn'),
(3, 'PRS-LEG-001', 'export_review', 'legal assessment', 'approved-vpn'),
(5, 'PRS-INV-001', 'view', 'triage restricted record', 'approved-vpn');

INSERT INTO exports (
    media_id,
    recipient_organisation_id,
    purpose,
    approved_by,
    exported_at,
    export_format,
    redaction_applied,
    export_sha256,
    transfer_method,
    notes
) VALUES
(3, 2, 'legal review package', 'PRS-LEG-001', '2026-02-18 14:00:00+03', 'redacted_mp4_plus_metadata_pdf', true, repeat('e', 64), 'encrypted transfer', 'Fictional controlled export.');

INSERT INTO tags (tag_name, tag_type) VALUES
('checkpoint', 'incident_feature'),
('crowd_dispersal', 'incident_feature'),
('needs_source_followup', 'workflow'),
('duplicate_candidate', 'data_quality');

INSERT INTO media_tags (media_id, tag_id, tagged_by) VALUES
(1, 2, 'PRS-INV-001'),
(2, 3, 'PRS-INV-001'),
(3, 1, 'PRS-INV-001'),
(4, 4, 'PRS-INV-001');

INSERT INTO legal_reviews (media_id, incident_id, status, reviewer_code, restrictions, evidentiary_notes) VALUES
(3, 2, 'approved_for_legal_use', 'PRS-LEG-001', 'Use redacted derivative externally.', 'Custody and verification sufficient for controlled sharing.'),
(5, 3, 'restricted_use', 'PRS-LEG-001', 'Do not share externally pending source-risk review.', 'Metadata incomplete and source risk unresolved.');
