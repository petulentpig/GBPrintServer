import os

import requests


SLACK_API_URL = "https://slack.com/api/chat.postMessage"


def send_notification(order_number: str, customer_name: str, total: str, order_url: str):
    """Send a Slack notification about a new order via Bot Token."""
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL")
    if not token or not channel:
        return

    message = {
        "channel": channel,
        "text": f"New order received!",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*New Order #{order_number}*\n"
                        f"Customer: {customer_name}\n"
                        f"Total: {total}\n"
                        f"<{order_url}|View Order>"
                    ),
                },
            }
        ],
    }

    resp = requests.post(
        SLACK_API_URL,
        json=message,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
