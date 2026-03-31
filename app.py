import hashlib
import hmac
import logging
import os

from flask import Flask, request, jsonify

from qr_generator import generate_qr
from printnode_client import print_qr
from slack_notify import send_notification

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_shopify_webhook(data: bytes, hmac_header: str) -> bool:
    """Verify the HMAC signature from Shopify."""
    secret = os.environ["SHOPIFY_WEBHOOK_SECRET"].encode("utf-8")
    computed = hmac.new(secret, data, hashlib.sha256).digest()
    import base64
    computed_b64 = base64.b64encode(computed).decode("utf-8")
    return hmac.compare_digest(computed_b64, hmac_header)


@app.route("/webhook/orders", methods=["POST"])
def handle_order():
    # Verify Shopify HMAC
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
    if not verify_shopify_webhook(request.get_data(), hmac_header):
        logger.warning("Invalid webhook signature")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    order_number = str(data.get("order_number", data.get("name", "unknown")))
    order_id = data.get("id")
    customer = data.get("customer", {})
    customer_name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "N/A"
    total = data.get("total_price", "0.00")
    currency = data.get("currency", "USD")

    store_url = os.environ.get("SHOPIFY_STORE_DOMAIN", "")
    order_url = f"https://{store_url}/admin/orders/{order_id}"

    logger.info(f"New order #{order_number} from {customer_name} for {currency} {total}")

    # Generate QR code
    try:
        pdf_b64 = generate_qr(order_url, order_number)
        logger.info(f"QR code generated for order #{order_number}")
    except Exception:
        logger.exception("Failed to generate QR code")
        return jsonify({"error": "QR generation failed"}), 500

    # Print via PrintNode
    try:
        result = print_qr(pdf_b64, order_number)
        logger.info(f"Print job submitted: {result}")
    except Exception:
        logger.exception("Failed to submit print job")

    # Slack notification
    try:
        send_notification(order_number, customer_name, f"{currency} {total}", order_url)
        logger.info(f"Slack notification sent for order #{order_number}")
    except Exception:
        logger.exception("Failed to send Slack notification")

    return jsonify({"status": "ok"}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
