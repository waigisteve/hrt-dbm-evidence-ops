#!/usr/bin/env python3
"""Simulate one hour of continuous sensitive evidence intake into PostgreSQL OLTP."""

from __future__ import annotations

import argparse
import random
import subprocess
import time
from datetime import datetime, timedelta, timezone


PG_DB = "videre_prep"
MEDIA_TYPES = ["video", "photo", "document"]
INCIDENT_TYPES = ["political violence", "checkpoint abuse", "night operation", "arbitrary detention"]
LOCALITIES = ["Kijani Market", "Mtoni Junction", "Riverline Bus Stage", "East Gate", "Old Depot"]


def run(command: list[str], input_text: str | None = None) -> str:
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def psql(sql: str) -> None:
    run(["sudo", "-u", "postgres", "psql", "-d", PG_DB, "-q"], sql)


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def make_hash(seed: int) -> str:
    chars = "0123456789abcdef"
    random.seed(seed)
    return "".join(random.choice(chars) for _ in range(64))


def insert_batch(batch_no: int) -> None:
    now = datetime.now(timezone.utc)
    incident_code = f"INC-LIVE-{batch_no:04d}"
    source_code = f"SRC-LIVE-{batch_no:04d}"
    locality = random.choice(LOCALITIES)
    incident_type = random.choice(INCIDENT_TYPES)
    media_count = random.randint(2, 4)

    statements = [
        f"""
INSERT INTO organisations (organisation_name, organisation_type, country_code, security_notes)
VALUES ({q('Live Partner Network ' + str(batch_no))}, 'CSO partner', 'KE', 'Simulated live intake partner.');
""",
        f"""
INSERT INTO sources (source_code, source_type, partner_organisation_id, reliability_rating, risk_level, notes)
VALUES ({q(source_code)}, 'live partner submission', currval('organisations_organisation_id_seq'), 3, 'restricted', 'Simulated live source.');
""",
        f"""
INSERT INTO locations (country_code, admin_area, locality, latitude, longitude, geolocation_confidence, notes)
VALUES ('KE', 'Central Region', {q(locality)}, -0.4 - ({batch_no}::numeric / 10000), 36.9 + ({batch_no}::numeric / 10000), 55, 'Simulated live location.');
""",
        f"""
INSERT INTO incidents (incident_code, title, incident_type, occurred_at, location_id, summary, verification_status, sensitivity)
VALUES ({q(incident_code)}, {q(locality + ' live intake ' + str(batch_no))}, {q(incident_type)}, {q(now.isoformat())}, currval('locations_location_id_seq'), 'Simulated continuous intake incident.', 'unverified', 'restricted');
""",
    ]

    for index in range(media_count):
        media_type = MEDIA_TYPES[index % len(MEDIA_TYPES)]
        media_id = f"LIVE-{batch_no:04d}-{index + 1}"
        filename = f"live_{batch_no:04d}_{index + 1}.{extension(media_type)}"
        captured_at = now - timedelta(minutes=random.randint(20, 180))
        metadata = metadata_json(media_type)
        legal_status = "restricted_use" if media_type == "document" else "needs_review"
        retention = "source_risk_review" if media_type == "document" else "legal_hold_review"
        file_hash = make_hash(batch_no * 100 + index)

        statements.append(
            f"""
INSERT INTO media_files (
    external_video_system_id, incident_id, source_id, original_filename, media_type, file_sha256,
    captured_at, received_at, storage_uri, access_classification, retention_category,
    verification_status, legal_status, metadata_json
)
VALUES (
    {q(media_id)}, currval('incidents_incident_id_seq'), currval('sources_source_id_seq'), {q(filename)},
    {q(media_type)}, {q(file_hash)}, {q(captured_at.isoformat())}, now(),
    {q('secure://evidence/live/' + media_id)}, 'restricted', {q(retention)},
    'unverified', {q(legal_status)}, {q(metadata)}::jsonb
);
"""
        )

        if media_type != "document":
            statements.extend(
                [
                    f"""
INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes)
VALUES (currval('media_files_media_id_seq'), 'collected', {q(captured_at.isoformat())}, {q(source_code)}, NULL, {q(source_code)}, 'device capture', {q(file_hash)}, 'Original collection.', 'One-hour live simulation.');
""",
                    f"""
INSERT INTO custody_events (media_id, event_type, event_at, actor_code, from_holder, to_holder, transfer_method, event_hash, reason, notes)
VALUES (currval('media_files_media_id_seq'), 'ingested', now(), 'PRS-INV-001', 'secure intake', 'video system', 'controlled ingest', {q(file_hash)}, 'Evidence intake.', 'One-hour live simulation.');
""",
                    f"""
INSERT INTO verification_steps (media_id, incident_id, step_type, method, result, confidence, reviewer_code, notes)
VALUES (currval('media_files_media_id_seq'), currval('incidents_incident_id_seq'), 'intake_triage', 'Hash check and metadata extraction.', 'partially_verified', 45, 'PRS-INV-001', 'Automated intake triage; human verification required.');
""",
                ]
            )

    psql("\n".join(statements))
    run(["python3", "scripts/refresh_olap.py"])
    print(f"{datetime.now().isoformat(timespec='seconds')} inserted {incident_code} with {media_count} items.")


def extension(media_type: str) -> str:
    return {"video": "mp4", "photo": "jpg", "document": "txt"}[media_type]


def metadata_json(media_type: str) -> str:
    if media_type == "video":
        return '{"duration_seconds":45,"gps_embedded":false,"device_time_present":true}'
    if media_type == "photo":
        return '{"exif_present":true,"gps_embedded":false}'
    return '{}'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--interval", type=int, default=30)
    args = parser.parse_args()

    batches = max(1, (args.minutes * 60) // args.interval)
    for batch_no in range(1, batches + 1):
        insert_batch(batch_no)
        if batch_no < batches:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
