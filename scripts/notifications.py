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
    gmail_sender: str
    gmail_app_password: str
    stakeholder_emails: dict[str, str]


def load_notification_config() -> NotificationConfig:
    return NotificationConfig(
        dry_run=os.getenv("VIDERE_NOTIFY_DRY_RUN", "true").lower() != "false",
        min_severity=os.getenv("VIDERE_NOTIFY_MIN_SEVERITY", "high").lower(),
        min_count=int(os.getenv("VIDERE_NOTIFY_MIN_COUNT", "1")),
        slack_webhook_url=os.getenv("VIDERE_SLACK_WEBHOOK_URL", ""),
        gmail_sender=os.getenv("VIDERE_GMAIL_SENDER", ""),
        gmail_app_password=os.getenv("VIDERE_GMAIL_APP_PASSWORD", ""),
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
            event["delivery_status"] = "dry_run"
            event["delivery_detail"] = "Notification composed but not sent. Set VIDERE_NOTIFY_DRY_RUN=false to send."
            continue
        event["delivery_status"], event["delivery_detail"] = deliver_event(event, config)

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
        "channel": delivery_channel(config),
        "recipient": recipient,
        "owner": owner,
        "severity": anomaly["severity"],
        "type": anomaly["type"],
        "count": anomaly["count"],
        "subject": subject,
        "body": body,
    }


def delivery_channel(config: NotificationConfig) -> str:
    if config.slack_webhook_url:
        return "slack"
    if config.gmail_sender and config.gmail_app_password:
        return "gmail"
    return "none_configured"


def deliver_event(event: dict[str, Any], config: NotificationConfig) -> tuple[str, str]:
    if config.slack_webhook_url:
        send_slack(event, config.slack_webhook_url)
        return "sent", "Sent to Slack webhook."
    if config.gmail_sender and config.gmail_app_password:
        send_gmail(event, config)
        return "sent", f"Sent to {event['recipient']} via Gmail SMTP."
    return "not_sent", "No Slack webhook or Gmail credentials configured."


def send_slack(event: dict[str, Any], webhook_url: str) -> None:
    payload = {
        "text": event["subject"],
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": event["subject"]}},
            {"type": "section", "text": {"type": "mrkdwn", "text": slack_body(event)}},
        ],
    }
    request = Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        response.read()


def send_gmail(event: dict[str, Any], config: NotificationConfig) -> None:
    message = EmailMessage()
    message["From"] = config.gmail_sender
    message["To"] = event["recipient"]
    message["Subject"] = event["subject"]
    message.set_content(event["body"])
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(config.gmail_sender, config.gmail_app_password)
        smtp.send_message(message)


def slack_body(event: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"*Owner:* {event['owner']}",
            f"*Count:* {event['count']}",
            f"*Type:* {event['type']}",
            "",
            event["body"],
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
