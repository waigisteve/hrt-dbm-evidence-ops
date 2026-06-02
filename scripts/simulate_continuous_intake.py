#!/usr/bin/env python3
"""Simulate continuous sensitive evidence intake into PostgreSQL OLTP.

This script is demo-only. In production, equivalent records would normally be
created by connectors, imports, or APIs from:

- closed-source video/evidence platforms,
- secure file transfer and intake workflows,
- mobile/field collection tools,
- investigator verification systems,
- legal review or case-management systems,
- partner submission portals.

The simulator writes to the same OLTP tables those production integrations
would populate, then runs the reporting refresh so the dashboard, monitoring,
and AI recommendation layer update as if live evidence had arrived.
"""

from __future__ import annotations

import argparse
import random
import secrets
import subprocess
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4


PG_DB = "hrt_prep"
MEDIA_TYPES = ["video", "photo", "document"]
INCIDENT_TYPES = ["political violence", "checkpoint abuse", "night operation", "arbitrary detention"]
LOCALITIES = ["Kijani Market", "Mtoni Junction", "Riverline Bus Stage", "East Gate", "Old Depot"]
VERIFICATION_OUTCOMES = ["unverified", "partially_verified", "verified"]
ACCESS_CLASSES = ["high", "restricted"]


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


def make_hash() -> str:
    return secrets.token_hex(32)


def insert_batch(batch_no: int, run_id: str) -> None:
    now = datetime.now(timezone.utc)
    incident_code = f"INC-LIVE-{run_id}-{batch_no:04d}"
    source_code = f"SRC-LIVE-{run_id}-{batch_no:04d}"
    locality = random.choice(LOCALITIES)
    incident_type = random.choice(INCIDENT_TYPES)
    media_count = random.randint(2, 4)
    incident_status = random.choices(VERIFICATION_OUTCOMES, weights=[55, 35, 10], k=1)[0]

    statements = [
        f"""
INSERT INTO organisations (organisation_name, organisation_type, country_code, security_notes)
VALUES ({q('Live Partner Network ' + run_id + '-' + str(batch_no))}, 'CSO partner', 'KE', 'Simulated live intake partner.');
""",
        f"""
INSERT INTO sources (source_code, source_type, partner_organisation_id, reliability_rating, risk_level, notes)
VALUES ({q(source_code)}, 'live partner submission', currval('organisations_organisation_id_seq'), {random.randint(2, 5)}, {q(random.choice(ACCESS_CLASSES))}, 'Simulated live source.');
""",
        f"""
INSERT INTO locations (country_code, admin_area, locality, latitude, longitude, geolocation_confidence, notes)
VALUES ('KE', 'Central Region', {q(locality)}, -0.4 - ({random.randint(1, 9999)}::numeric / 100000), 36.9 + ({random.randint(1, 9999)}::numeric / 100000), {random.randint(45, 90)}, 'Simulated live location.');
""",
        f"""
INSERT INTO incidents (incident_code, title, incident_type, occurred_at, location_id, summary, verification_status, sensitivity)
VALUES ({q(incident_code)}, {q(locality + ' live intake ' + run_id + '-' + str(batch_no))}, {q(incident_type)}, {q(now.isoformat())}, currval('locations_location_id_seq'), 'Simulated continuous intake incident.', {q(incident_status)}, {q(random.choice(ACCESS_CLASSES))});
""",
    ]

    for index in range(media_count):
        media_type = random.choice(MEDIA_TYPES)
        media_id = f"LIVE-{run_id}-{batch_no:04d}-{index + 1}"
        filename = f"live_{run_id}_{batch_no:04d}_{index + 1}.{extension(media_type)}"
        captured_at = now - timedelta(minutes=random.randint(20, 180))
        metadata = metadata_json(media_type)
        verification_status = random.choices(VERIFICATION_OUTCOMES, weights=[60, 30, 10], k=1)[0]
        legal_status = legal_status_for(media_type, verification_status)
        retention = "source_risk_review" if media_type == "document" else "legal_hold_review"
        file_hash = make_hash()
        access_class = random.choice(ACCESS_CLASSES)

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
    {q('secure://evidence/live/' + media_id)}, {q(access_class)}, {q(retention)},
    {q(verification_status)}, {q(legal_status)}, {q(metadata)}::jsonb
);
"""
        )

        has_custody = media_type != "document" or random.random() < 0.35
        if has_custody:
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
VALUES (currval('media_files_media_id_seq'), currval('incidents_incident_id_seq'), 'intake_triage', 'Hash check and metadata extraction.', {q(verification_status if verification_status != "unverified" else "partially_verified")}, {random.randint(40, 85)}, 'PRS-INV-001', 'Automated intake triage; human verification required.');
""",
                ]
            )

    psql("\n".join(statements))
    run(["python3", "scripts/refresh_olap.py"])
    run(["python3", "scripts/sync_media_catalog.py"])
    run(["python3", "scripts/refresh_olap.py"])
    print(f"{datetime.now().isoformat(timespec='seconds')} inserted {incident_code} with {media_count} items.")


def extension(media_type: str) -> str:
    return {"video": "mp4", "photo": "jpg", "document": "txt"}[media_type]


def metadata_json(media_type: str) -> str:
    if media_type == "video":
        return '{"duration_seconds":%s,"gps_embedded":false,"device_time_present":true}' % random.randint(18, 180)
    if media_type == "photo":
        return '{"exif_present":true,"gps_embedded":false}'
    return '{}'


def legal_status_for(media_type: str, verification_status: str) -> str:
    if media_type == "document":
        return random.choice(["restricted_use", "needs_review"])
    if verification_status == "verified":
        return random.choices(["approved_for_legal_use", "needs_review"], weights=[35, 65], k=1)[0]
    return random.choice(["needs_review", "not_reviewed"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--interval", type=int, default=30)
    parser.add_argument("--run-id", default=None, help="Optional run token for generated IDs. Defaults to a fresh random token.")
    args = parser.parse_args()

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + uuid4().hex[:6]
    print(f"Starting live intake simulation run_id={run_id}")

    batches = max(1, (args.minutes * 60) // args.interval)
    for batch_no in range(1, batches + 1):
        insert_batch(batch_no, run_id)
        if batch_no < batches:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
