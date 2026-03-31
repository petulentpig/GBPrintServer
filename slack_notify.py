import os

import requests


SLACK_UPLOAD_URL = "https://slack.com/api/files.upload"


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
        return

    comment = (
        f"*New Order #{order_number}*\n"
        f"Customer: {customer_name}\n"
        f"Total: {total}\n"
        f"<{order_url}|View Order>"
    )

    headers = {"Authorization": f"Bearer {token}"}

    if label_png:
        # Upload the label image with order details as comment
        resp = requests.post(
            SLACK_UPLOAD_URL,
            headers=headers,
            data={
                "channels": channel,
                "initial_comment": comment,
                "filename": f"order-{order_number}.png",
                "title": f"Order #{order_number}",
            },
            files={"file": (f"order-{order_number}.png", label_png, "image/png")},
            timeout=15,
        )
    else:
        # Fallback: text-only message
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers=headers,
            json={
                "channel": channel,
                "text": comment,
            },
            timeout=10,
        )

    resp.raise_for_status()
