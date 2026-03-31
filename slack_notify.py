import logging
import os

import requests

logger = logging.getLogger(__name__)

SLACK_API = "https://slack.com/api"


def _slack_post(endpoint: str, token: str, **kwargs) -> dict:
    """Make a Slack API call and verify the response."""
    headers = kwargs.pop("headers", {})
    headers["Authorization"] = f"Bearer {token}"
    resp = requests.post(f"{SLACK_API}/{endpoint}", headers=headers, timeout=15, **kwargs)
    resp.raise_for_status()
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Slack {endpoint} error: {result.get('error')}")
    return result


def send_notification(
    order_number: str,
    customer_name: str,
    total: str,
    order_url: str,
    label_png: bytes = None,
):
    """Send a Slack notification with the label image attached."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL")
    if not token or not channel:
        logger.warning(
            f"Slack not configured: token={'set' if token else 'MISSING'}, "
            f"channel={'set' if channel else 'MISSING'}"
        )
        return

    comment = (
        f"*New Order #{order_number}*\n"
        f"Customer: {customer_name}\n"
        f"Total: {total}\n"
        f"<{order_url}|View Order>"
    )

    if label_png:
        filename = f"order-{order_number}.png"

        # Step 1: Get an upload URL from Slack
        upload_info = _slack_post(
            "files.getUploadURLExternal",
            token,
            data={"filename": filename, "length": len(label_png)},
        )
        upload_url = upload_info["upload_url"]
        file_id = upload_info["file_id"]

        # Step 2: Upload the file bytes to the provided URL
        resp = requests.post(upload_url, files={"file": (filename, label_png, "image/png")}, timeout=15)
        resp.raise_for_status()

        # Step 3: Complete the upload and share to channel
        import json
        _slack_post(
            "files.completeUploadExternal",
            token,
            json={
                "files": [{"id": file_id, "title": f"Order #{order_number}"}],
                "channel_id": channel,
                "initial_comment": comment,
            },
        )
    else:
        # Fallback: text-only message
        _slack_post(
            "chat.postMessage",
            token,
            json={"channel": channel, "text": comment},
        )

    logger.info(f"Slack notification sent for order #{order_number}")
