import base64
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr(url: str, order_number: str) -> str:
    """Generate a QR code with an order label, return as base64-encoded PDF."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_w, qr_h = qr_img.size

    # Add order number label below the QR code
    label_height = 60
    canvas = Image.new("RGB", (qr_w, qr_h + label_height), "white")
    canvas.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(canvas)
    label = f"Order #{order_number}"
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (qr_w - text_w) // 2
    text_y = qr_h + (label_height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), label, fill="black", font=font)

    # Save as PDF and return base64
    pdf_buffer = io.BytesIO()
    canvas.save(pdf_buffer, format="PDF", resolution=200)
    pdf_bytes = pdf_buffer.getvalue()
    return base64.b64encode(pdf_bytes).decode("ascii")
