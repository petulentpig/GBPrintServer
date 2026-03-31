import os

import requests


PRINTNODE_API_URL = "https://api.printnode.com/printjobs"


def print_qr(pdf_base64: str, order_number: str) -> dict:
    """Submit a print job to PrintNode with the QR code PDF."""
    api_key = os.environ["PRINTNODE_API_KEY"]
    printer_id = int(os.environ["PRINTNODE_PRINTER_ID"])

    payload = {
        "printerId": printer_id,
        "title": f"Order #{order_number}",
        "contentType": "pdf_base64",
        "content": pdf_base64,
    }

    resp = requests.post(
        PRINTNODE_API_URL,
        json=payload,
        auth=(api_key, ""),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
