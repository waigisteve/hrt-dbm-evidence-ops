"""Redacted stakeholder notifications for threshold-breaching anomalies.

The default mode is dry-run. Real Slack or email delivery only happens when
environment variables explicitly enable it and provide credentials. This keeps
the demo safe while showing where production alerting would integrate.
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any
from urllib.request import Request, urlopen


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}
DEFAULT_STAKEHOLDER_EMAILS = {
    "leadership": "leadership@example.org",
    "investigations": "investigations@example.org",
    "legal": "legal@example.org",
    "data_protection": "dpo@example.org",
    "monitoring": "monitoring@example.org",
    "operations": "operations@example.org",
}


@dataclass(frozen=True)
class NotificationConfig:
    dry_run: bool
    min_severity: str
    min_count: int
    slack_webhook_url: str
    smtp_host: str
    smtp_port: int
    smtp_sender: str
    smtp_password: str
    timeout_seconds: int
    stakeholder_emails: dict[str, str]


def load_notification_config() -> NotificationConfig:
    return NotificationConfig(
        dry_run=os.getenv("VIDERE_NOTIFY_DRY_RUN", "true").lower() != "false",
        min_severity=os.getenv("VIDERE_NOTIFY_MIN_SEVERITY", "high").lower(),
        min_count=int(os.getenv("VIDERE_NOTIFY_MIN_COUNT", "1")),
        slack_webhook_url=os.getenv("VIDERE_SLACK_WEBHOOK_URL", ""),
        smtp_host=os.getenv("VIDERE_SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("VIDERE_SMTP_PORT", "465")),
        smtp_sender=os.getenv("VIDERE_SMTP_SENDER", os.getenv("VIDERE_GMAIL_SENDER", "")),
        smtp_password=os.getenv("VIDERE_SMTP_PASSWORD", os.getenv("VIDERE_GMAIL_APP_PASSWORD", "")),
        timeout_seconds=int(os.getenv("VIDERE_NOTIFY_TIMEOUT_SECONDS", "10")),
        stakeholder_emails=load_stakeholder_emails(),
    )


def notify_threshold_anomalies(ai_recommendations: dict[str, Any]) -> dict[str, Any]:
    """Notify stakeholders about anomalies beyond configured thresholds.

    Only redacted anomaly facts are sent: type, severity, count, owner,
    description, and sample media IDs. Raw media, exact locations, source names,
    file hashes, and personal data are intentionally absent.
    """
    config = load_notification_config()
    selected = [
        anomaly
        for anomaly in ai_recommendations.get("anomalies", [])
        if should_notify(anomaly, config)
    ]
    events = [build_event(anomaly, config) for anomaly in selected]

    for event in events:
        if config.dry_run:
            event["deliveries"] = dry_run_deliveries(config)
            event["delivery_status"] = "dry_run"
            event["delivery_detail"] = "Notifications composed but not sent. Set VIDERE_NOTIFY_DRY_RUN=false to send."
            continue
        event["deliveries"] = deliver_event(event, config)
        event["delivery_status"] = combined_status(event["deliveries"])
        event["delivery_detail"] = "; ".join(delivery["detail"] for delivery in event["deliveries"])

    return {
        "enabled": not config.dry_run,
        "dry_run": config.dry_run,
        "min_severity": config.min_severity,
        "min_count": config.min_count,
        "event_count": len(events),
        "events": events,
    }


def should_notify(anomaly: dict[str, Any], config: NotificationConfig) -> bool:
    severity = SEVERITY_RANK.get(str(anomaly.get("severity", "")).lower(), 0)
    min_severity = SEVERITY_RANK.get(config.min_severity, SEVERITY_RANK["high"])
    count = int(anomaly.get("count", 0))
    return severity >= min_severity and count >= config.min_count


def build_event(anomaly: dict[str, Any], config: NotificationConfig) -> dict[str, Any]:
    owner = str(anomaly.get("owner", "monitoring")).lower()
    recipient = config.stakeholder_emails.get(owner, DEFAULT_STAKEHOLDER_EMAILS.get(owner, "monitoring@example.org"))
    subject = f"[Videre demo] {str(anomaly['severity']).upper()} anomaly: {anomaly['type']}"
    body = "\n".join(
        [
            subject,
            "",
            f"Owner: {owner}",
            f"Count: {anomaly['count']}",
            f"Description: {anomaly['description']}",
            f"Sample media IDs: {', '.join(anomaly.get('sample_media_ids') or ['portfolio-level'])}",
            "",
            "Action: Open the AI Review dashboard and review stakeholder recommendations.",
            "Safety: This notification contains redacted anomaly facts only.",
        ]
    )
    return {
        "channel": delivery_channels(config),
        "recipient": recipient,
        "owner": owner,
        "severity": anomaly["severity"],
        "type": anomaly["type"],
        "count": anomaly["count"],
        "subject": subject,
        "body": body,
    }


def delivery_channels(config: NotificationConfig) -> str:
    channels = configured_channels(config)
    return "+".join(channels) if channels else "none_configured"


def configured_channels(config: NotificationConfig) -> list[str]:
    channels: list[str] = []
    if config.slack_webhook_url:
        channels.append("slack")
    if config.smtp_sender and config.smtp_password:
        channels.append("email")
    return channels


def deliver_event(event: dict[str, Any], config: NotificationConfig) -> list[dict[str, str]]:
    deliveries: list[dict[str, str]] = []
    if config.slack_webhook_url:
        try:
            send_slack(event, config)
            deliveries.append({"channel": "slack", "status": "sent", "detail": "Sent to Slack webhook."})
        except Exception as exc:
            deliveries.append({"channel": "slack", "status": "failed", "detail": f"Slack send failed: {exc}"})
    if config.smtp_sender and config.smtp_password:
        try:
            send_email(event, config)
            deliveries.append({"channel": "email", "status": "sent", "detail": f"Sent to {event['recipient']} via SMTP."})
        except Exception as exc:
            deliveries.append({"channel": "email", "status": "failed", "detail": f"Email send failed: {exc}"})
    if not deliveries:
        deliveries.append({"channel": "none_configured", "status": "not_sent", "detail": "No Slack webhook or SMTP credentials configured."})
    return deliveries


def dry_run_deliveries(config: NotificationConfig) -> list[dict[str, str]]:
    channels = configured_channels(config)
    if not channels:
        channels = ["none_configured"]
    return [
        {
            "channel": channel,
            "status": "dry_run",
            "detail": "Notification composed but not sent. Set VIDERE_NOTIFY_DRY_RUN=false to send.",
        }
        for channel in channels
    ]


def combined_status(deliveries: list[dict[str, str]]) -> str:
    statuses = {delivery["status"] for delivery in deliveries}
    if statuses == {"sent"}:
        return "sent"
    if "sent" in statuses and "failed" in statuses:
        return "partial"
    if "failed" in statuses:
        return "failed"
    if "dry_run" in statuses:
        return "dry_run"
    return "not_sent"


def send_slack(event: dict[str, Any], config: NotificationConfig) -> None:
    payload = {
        "text": event["subject"],
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": event["subject"]}},
            {"type": "section", "text": {"type": "mrkdwn", "text": slack_body(event)}},
        ],
    }
    request = Request(
        config.slack_webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=config.timeout_seconds) as response:
        response.read()


def send_email(event: dict[str, Any], config: NotificationConfig) -> None:
    message = EmailMessage()
    message["From"] = config.smtp_sender
    message["To"] = event["recipient"]
    message["Subject"] = event["subject"]
    message.set_content(event["body"])
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=config.timeout_seconds, context=context) as smtp:
        smtp.login(config.smtp_sender, config.smtp_password)
        smtp.send_message(message)


def slack_body(event: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"*Owner:* {event['owner']}",
            f"*Count:* {event['count']}",
            f"*Type:* {event['type']}",
            "*Action:* Open the AI Review dashboard and review stakeholder recommendations.",
            "_Redacted anomaly facts only. No raw media, hashes, precise locations, source names, or personal data._",
        ]
    )


def load_stakeholder_emails() -> dict[str, str]:
    configured = dict(DEFAULT_STAKEHOLDER_EMAILS)
    raw = os.getenv("VIDERE_STAKEHOLDER_EMAILS", "")
    if not raw:
        return configured
    for pair in raw.split(","):
        if ":" not in pair:
            continue
        owner, email = pair.split(":", 1)
        configured[owner.strip().lower()] = email.strip()
    return configured
