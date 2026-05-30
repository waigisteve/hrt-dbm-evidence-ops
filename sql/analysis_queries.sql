-- Practical analytical SQL for the Videre-style preparation work sample.

-- 1. Media records missing required evidence-management fields.
SELECT
    media_id,
    original_filename,
    external_video_system_id,
    incident_id,
    source_id,
    captured_at,
    received_at,
    verification_status,
    legal_status
FROM media_files
WHERE source_id IS NULL
   OR incident_id IS NULL
   OR captured_at IS NULL
   OR file_sha256 IS NULL
   OR retention_category IS NULL
   OR metadata_json = '{}'::jsonb;

-- 2. Media with no custody event after ingestion.
SELECT
    m.media_id,
    m.original_filename,
    m.received_at,
    COUNT(c.custody_event_id) AS custody_event_count
FROM media_files m
LEFT JOIN custody_events c ON c.media_id = m.media_id
GROUP BY m.media_id, m.original_filename, m.received_at
HAVING COUNT(c.custody_event_id) = 0;

-- 3. Custody gaps where the first custody event occurs after received_at.
SELECT
    m.media_id,
    m.original_filename,
    m.received_at,
    MIN(c.event_at) AS first_custody_event_at
FROM media_files m
JOIN custody_events c ON c.media_id = m.media_id
GROUP BY m.media_id, m.original_filename, m.received_at
HAVING MIN(c.event_at) > m.received_at + INTERVAL '1 hour';

-- 4. Potential duplicate media by hash or filename.
SELECT
    file_sha256,
    COUNT(*) AS duplicate_count,
    ARRAY_AGG(media_id ORDER BY media_id) AS media_ids,
    ARRAY_AGG(original_filename ORDER BY media_id) AS filenames
FROM media_files
GROUP BY file_sha256
HAVING COUNT(*) > 1
UNION ALL
SELECT
    MIN(file_sha256) AS file_sha256,
    COUNT(*) AS duplicate_count,
    ARRAY_AGG(media_id ORDER BY media_id) AS media_ids,
    ARRAY_AGG(original_filename ORDER BY media_id) AS filenames
FROM media_files
GROUP BY lower(original_filename)
HAVING COUNT(*) > 1;

-- 5. Incidents with at least two independent sources and verified media.
SELECT
    i.incident_code,
    i.title,
    COUNT(DISTINCT m.source_id) AS independent_sources,
    COUNT(m.media_id) AS verified_media_count
FROM incidents i
JOIN media_files m ON m.incident_id = i.incident_id
WHERE m.verification_status = 'verified'
GROUP BY i.incident_code, i.title
HAVING COUNT(DISTINCT m.source_id) >= 2;

-- 6. Pattern analysis by location, incident type, alleged actor, and month.
SELECT
    l.country_code,
    l.admin_area,
    i.incident_type,
    a.actor_name,
    DATE_TRUNC('month', i.occurred_at) AS incident_month,
    COUNT(DISTINCT i.incident_id) AS incident_count,
    COUNT(DISTINCT m.media_id) AS media_count
FROM incidents i
LEFT JOIN locations l ON l.location_id = i.location_id
LEFT JOIN incident_alleged_actors iaa ON iaa.incident_id = i.incident_id
LEFT JOIN alleged_actors a ON a.alleged_actor_id = iaa.alleged_actor_id
LEFT JOIN media_files m ON m.incident_id = i.incident_id
GROUP BY l.country_code, l.admin_area, i.incident_type, a.actor_name, DATE_TRUNC('month', i.occurred_at)
ORDER BY incident_month DESC, incident_count DESC;

-- 7. Evidence readiness report for legal review.
SELECT
    m.media_id,
    m.original_filename,
    i.incident_code,
    m.verification_status,
    m.legal_status,
    COUNT(DISTINCT c.custody_event_id) AS custody_events,
    COUNT(DISTINCT v.verification_step_id) AS verification_steps,
    CASE
        WHEN m.verification_status = 'verified'
         AND m.legal_status = 'approved_for_legal_use'
         AND COUNT(DISTINCT c.custody_event_id) >= 2
         AND COUNT(DISTINCT v.verification_step_id) >= 1
        THEN 'ready'
        ELSE 'not_ready'
    END AS evidentiary_readiness
FROM media_files m
LEFT JOIN incidents i ON i.incident_id = m.incident_id
LEFT JOIN custody_events c ON c.media_id = m.media_id
LEFT JOIN verification_steps v ON v.media_id = m.media_id
GROUP BY m.media_id, m.original_filename, i.incident_code, m.verification_status, m.legal_status;

-- 8. Access review for restricted records.
SELECT
    m.media_id,
    m.original_filename,
    m.access_classification,
    al.user_code,
    al.action,
    al.purpose,
    al.accessed_at
FROM media_files m
JOIN access_logs al ON al.media_id = m.media_id
WHERE m.access_classification IN ('high', 'restricted')
  AND al.accessed_at >= now() - INTERVAL '30 days'
ORDER BY al.accessed_at DESC;

-- 9. Migration validation: source-to-target reconciliation staging pattern.
-- Assumes a temporary table migration_source_manifest exists.
-- Columns: source_system_id, source_sha256, source_filename, source_record_updated_at.
SELECT
    s.source_system_id,
    s.source_filename,
    t.media_id,
    CASE
        WHEN t.media_id IS NULL THEN 'missing_in_target'
        WHEN t.file_sha256 <> s.source_sha256 THEN 'hash_mismatch'
        ELSE 'matched'
    END AS validation_status
FROM migration_source_manifest s
LEFT JOIN media_files t ON t.external_video_system_id = s.source_system_id;

-- 10. Records needing GDPR/data protection review.
SELECT
    m.media_id,
    m.original_filename,
    m.access_classification,
    m.retention_category,
    m.legal_status,
    s.risk_level AS source_risk_level,
    m.received_at
FROM media_files m
LEFT JOIN sources s ON s.source_id = m.source_id
WHERE m.access_classification = 'restricted'
   OR s.risk_level = 'restricted'
   OR m.retention_category ILIKE '%legal_hold%'
   OR m.legal_status IN ('restricted_use', 'do_not_use');
