"""Local AI-style anomaly detection and recommendation generation.

This module deliberately uses structured rules instead of sending sensitive
evidence to an external model. In production, the `generate_recommendations`
boundary is where an approved private LLM could be called with redacted facts.

Production interpretation:

- Input is a redacted reporting snapshot, not raw evidence.
- Anomaly detection identifies operational, evidentiary, and governance risks.
- Recommendation generation converts those risks into stakeholder-specific
  actions for leadership, investigations, legal, partners, data protection,
  monitoring, operations, and AI review.
- A real GenAI integration should sit behind this same boundary and receive
  only redacted anomaly facts after DPIA, vendor review, security review, and
  human-in-the-loop approval.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


HIGH = "high"
MEDIUM = "medium"
LOW = "low"


def generate_ai_recommendations(
    rows: list[dict[str, str]],
    monitoring: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate dashboard-ready anomaly findings and recommendations.

    This function is the intended integration boundary for a future private LLM.
    The current implementation is deterministic so the interview demo is
    explainable, testable, and safe with sensitive-evidence assumptions.
    """
    anomalies = detect_anomalies(rows, monitoring)
    recommendations = build_recommendations(anomalies)
    return {
        "mode": "local_redacted_recommendation_engine",
        "model_boundary": (
            "No raw media, source names, precise locations, hashes, or personal data are sent to external AI. "
            "A production LLM integration should receive only redacted anomaly facts after DPIA and security review."
        ),
        "summary": {
            "anomaly_count": len(anomalies),
            "critical_count": sum(1 for item in anomalies if item["severity"] == HIGH),
            "recommendation_count": len(recommendations),
            "stakeholders": sorted({item["stakeholder"] for item in recommendations}),
        },
        "anomalies": anomalies,
        "recommendations": recommendations,
    }


def detect_anomalies(rows: list[dict[str, str]], monitoring: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Detect records and patterns that need human review.

    The checks intentionally cover both technical health and evidentiary health:
    a database can be online while the evidence estate is still weak because of
    custody gaps, missing metadata, source skew, or verification backlog.
    """
    anomalies: list[dict[str, Any]] = []
    total = max(1, len(rows))
    recent = rows[-30:] if len(rows) > 30 else rows

    custody_gaps = [row for row in rows if int(row["custody_events"]) == 0]
    restricted_unverified = [
        row
        for row in rows
        if row["access_classification"] == "restricted" and row["verification_status"] == "unverified"
    ]
    legal_ready = [
        row
        for row in rows
        if row["verification_status"] == "verified"
        and row["legal_status"] == "approved_for_legal_use"
        and int(row["custody_events"]) >= 2
    ]
    missing_metadata = [
        row
        for row in rows
        if row.get("metadata_json", "").strip() in {"", "{}"} or not row.get("captured_at", "").strip()
    ]
    unsafe_media = [
        row for row in rows if row.get("safe_status") not in {"", "safe", None} and row.get("safe_status") != "safe"
    ]
    source_counts = Counter(row["source_code"] for row in recent)
    dominant_source, dominant_count = source_counts.most_common(1)[0] if source_counts else ("unknown", 0)
    recent_unverified = [row for row in recent if row["verification_status"] == "unverified"]

    if custody_gaps:
        anomalies.append(
            anomaly(
                "custody_gap",
                HIGH if len(custody_gaps) / total > 0.25 else MEDIUM,
                len(custody_gaps),
                "Evidence records have no custody events.",
                "investigations",
                sample_media(custody_gaps),
            )
        )
    if restricted_unverified:
        anomalies.append(
            anomaly(
                "restricted_unverified",
                HIGH,
                len(restricted_unverified),
                "Restricted records remain unverified, increasing protection and interpretation risk.",
                "data_protection",
                sample_media(restricted_unverified),
            )
        )
    if missing_metadata:
        anomalies.append(
            anomaly(
                "metadata_gap",
                MEDIUM,
                len(missing_metadata),
                "Records have missing captured time or empty metadata.",
                "investigations",
                sample_media(missing_metadata),
            )
        )
    if unsafe_media:
        anomalies.append(
            anomaly(
                "media_safety_review",
                HIGH,
                len(unsafe_media),
                "Media catalog contains objects that are not marked safe.",
                "monitoring",
                sample_media(unsafe_media),
            )
        )
    if dominant_count / max(1, len(recent)) > 0.5:
        anomalies.append(
            anomaly(
                "recent_source_skew",
                MEDIUM,
                dominant_count,
                f"Latest intake window is dominated by one source code: {dominant_source}.",
                "leadership",
                [],
            )
        )
    if len(recent_unverified) / max(1, len(recent)) > 0.7:
        anomalies.append(
            anomaly(
                "recent_unverified_surge",
                MEDIUM,
                len(recent_unverified),
                "Latest intake is producing a high unverified workload.",
                "investigations",
                sample_media(recent_unverified),
            )
        )
    if len(legal_ready) / total < 0.05 and total >= 20:
        anomalies.append(
            anomaly(
                "low_legal_ready_yield",
                MEDIUM,
                len(legal_ready),
                "Very few records currently meet legal-ready evidence controls.",
                "legal",
                sample_media(legal_ready),
            )
        )

    recent_alerts = [
        item for item in monitoring if item.get("status") == "alert" and str(item.get("name", "")).startswith("recent")
    ]
    if recent_alerts:
        alert_names = ", ".join(str(item["name"]) for item in recent_alerts[:4])
        anomalies.append(
            anomaly(
                "monitoring_alert",
                MEDIUM,
                len(recent_alerts),
                f"Recent monitoring alerts need review: {alert_names}.",
                "monitoring",
                [],
            )
        )

    return anomalies


def build_recommendations(anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert anomaly facts into practical stakeholder actions."""
    recommendations: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in anomalies:
        grouped.setdefault(item["type"], []).append(item)

    if "custody_gap" in grouped:
        recommendations.extend(
            [
                rec(
                    "Investigations",
                    HIGH,
                    "Run a custody repair sprint.",
                    "Filter records with zero custody events, reconstruct transfer history from source and intake logs, and mark unresolved items as not ready for legal use.",
                    "Blocks weak evidence from being interpreted as defensible.",
                ),
                rec(
                    "CSO Partners",
                    MEDIUM,
                    "Refresh partner intake training.",
                    "Issue a one-page collection checklist covering capture time, transfer method, source code, and custody handover notes.",
                    "Reduces repeat custody gaps at the point of collection.",
                ),
            ]
        )
    if "restricted_unverified" in grouped:
        recommendations.extend(
            [
                rec(
                    "Data Protection",
                    HIGH,
                    "Tighten access until verification catches up.",
                    "Limit restricted-unverified records to need-to-know users, review sharing logs, and confirm retention category before wider analysis.",
                    "Protects sources and affected people while facts remain uncertain.",
                ),
                rec(
                    "Leadership",
                    MEDIUM,
                    "Allocate verification capacity to the restricted backlog.",
                    "Treat restricted-unverified items as a resourcing signal, not only a technical queue.",
                    "Improves protection posture and decision confidence.",
                ),
            ]
        )
    if "metadata_gap" in grouped:
        recommendations.append(
            rec(
                "Investigations",
                MEDIUM,
                "Make metadata completeness a daily intake control.",
                "Require captured time, source, incident, access class, retention category, and minimum technical metadata before closing intake.",
                "Improves traceability, search, corroboration, and legal defensibility.",
            )
        )
    if "recent_source_skew" in grouped:
        recommendations.append(
            rec(
                "Leadership",
                MEDIUM,
                "Treat source skew as a corroboration risk.",
                "Ask teams to identify independent corroboration routes before using latest trends for advocacy or legal claims.",
                "Prevents over-reliance on a single reporting channel.",
            )
        )
    if "recent_unverified_surge" in grouped:
        recommendations.append(
            rec(
                "Operations",
                MEDIUM,
                "Throttle onward reporting from fresh intake.",
                "Keep recent surge records in triage view until enough verification steps are completed.",
                "Avoids giving stakeholders premature conclusions.",
            )
        )
    if "low_legal_ready_yield" in grouped:
        recommendations.append(
            rec(
                "Legal",
                MEDIUM,
                "Create a legal-readiness exception queue.",
                "Separate records blocked by custody, verification, metadata, or access restrictions and assign owners for each blocker.",
                "Turns legal readiness from a status label into a work plan.",
            )
        )
    if "media_safety_review" in grouped:
        recommendations.append(
            rec(
                "Monitoring",
                HIGH,
                "Quarantine unsafe or unscanned objects.",
                "Do not preview or export media that fails extension, MIME, malware, or integrity checks until reviewed.",
                "Prevents unsafe files from entering investigator workflows.",
            )
        )
    if "monitoring_alert" in grouped:
        recommendations.append(
            rec(
                "Monitoring",
                MEDIUM,
                "Review recent-window alert drivers.",
                "Compare the latest 30 records against the full portfolio, then decide whether the issue is intake quality, source skew, verification capacity, or a system processing problem.",
                "Keeps live monitoring actionable instead of becoming a passive warning board.",
            )
        )

    recommendations.append(
        rec(
            "AI Review",
            LOW,
            "Use AI only on redacted anomaly facts or approved private processing.",
            "AI may draft summaries, cluster duplicates, suggest triage priorities, and produce training prompts, but humans must verify all findings.",
            "Keeps innovation aligned with data protection and evidentiary standards.",
        )
    )
    return recommendations


def anomaly(
    anomaly_type: str,
    severity: str,
    count: int,
    description: str,
    owner: str,
    sample_media_ids: list[str],
) -> dict[str, Any]:
    return {
        "type": anomaly_type,
        "severity": severity,
        "count": count,
        "description": description,
        "owner": owner,
        "sample_media_ids": sample_media_ids,
    }


def rec(stakeholder: str, severity: str, title: str, recommendation: str, expected_impact: str) -> dict[str, str]:
    return {
        "stakeholder": stakeholder,
        "severity": severity,
        "title": title,
        "recommendation": recommendation,
        "expected_impact": expected_impact,
    }


def sample_media(rows: list[dict[str, str]]) -> list[str]:
    return [str(row["media_id"]) for row in rows[:6]]
