from __future__ import annotations

from scripts.ai_recommendations import generate_ai_recommendations


def test_ai_recommendations_include_governance_metadata() -> None:
    result = generate_ai_recommendations(sample_rows(), [])

    assert result["mode"] == "local_redacted_recommendation_engine"
    assert "No raw media" in result["model_boundary"]
    assert "tool_name" in result["decision_log_fields"]
    assert "reviewer_decision" in result["decision_log_fields"]
    assert "automated verification conclusions" in result["prohibited_uses"]
    assert "legal conclusions" in result["prohibited_uses"]
    assert "velocity_gain" in result["scorecard"]
    assert "reviewer_correction_rate" in result["scorecard"]


def test_ai_recommendations_surface_stakeholder_actions_and_pilot_lanes() -> None:
    result = generate_ai_recommendations(sample_rows(), [])

    stakeholders = {item["stakeholder"] for item in result["recommendations"]}
    lane_priorities = {item["name"]: item["priority"] for item in result["pilot_lanes"]}

    assert "Investigations" in stakeholders
    assert "Data Protection" in stakeholders
    assert lane_priorities["Metadata extraction"] == "high"
    assert "Legal-readiness blockers" in lane_priorities


def test_ai_recommendations_are_deterministic_for_same_redacted_input() -> None:
    rows = sample_rows()

    assert generate_ai_recommendations(rows, []) == generate_ai_recommendations(rows, [])


def sample_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index in range(1, 22):
        rows.append(
            {
                "media_id": f"media-{index}",
                "custody_events": "0" if index <= 6 else "2",
                "access_classification": "restricted" if index <= 3 else "internal",
                "verification_status": "unverified" if index <= 18 else "verified",
                "legal_status": "not_reviewed",
                "metadata_json": "{}" if index <= 4 else '{"captured_by":"partner"}',
                "captured_at": "" if index <= 4 else "2026-01-01T00:00:00",
                "safe_status": "safe",
                "source_code": "SRC-A" if index <= 18 else "SRC-B",
            }
        )
    return rows
