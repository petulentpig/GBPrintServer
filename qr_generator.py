import base64
import io

import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageDraw, ImageFont


def generate_qr(url: str, order_number: str) -> str:
    """Generate a QR code and Code 128 barcode, return as base64-encoded PDF."""

    # --- QR Code (links to order admin page) ---
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # --- Code 128 Barcode (order number, matching EasyScan style) ---
    code128 = barcode.get("code128", str(order_number), writer=ImageWriter())
    barcode_buffer = io.BytesIO()
    code128.write(barcode_buffer, options={
        "module_width": 0.4,
        "module_height": 20,
        "font_size": 14,
        "text_distance": 5,
        "quiet_zone": 6.5,
    })
    barcode_buffer.seek(0)
    barcode_img = Image.open(barcode_buffer).convert("RGB")

    # --- Compose both onto a single canvas ---
    qr_w, qr_h = qr_img.size
    bc_w, bc_h = barcode_img.size

    padding = 20
    label_height = 50
    canvas_width = max(qr_w, bc_w) + padding * 2
    canvas_height = qr_h + padding + bc_h + padding + label_height

    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")

    # Center QR code at top
    qr_x = (canvas_width - qr_w) // 2
    canvas.paste(qr_img, (qr_x, 0))

    # Order label between QR and barcode
    draw = ImageDraw.Draw(canvas)
    label = f"Order #{order_number}"
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_x = (canvas_width - text_w) // 2
    text_y = qr_h + (label_height - (bbox[3] - bbox[1])) // 2
    draw.text((text_x, text_y), label, fill="black", font=font)

    # Center barcode below label
    bc_x = (canvas_width - bc_w) // 2
    canvas.paste(barcode_img, (bc_x, qr_h + label_height))

    # --- Save as PDF ---
    pdf_buffer = io.BytesIO()
    canvas.save(pdf_buffer, format="PDF", resolution=200)
    pdf_bytes = pdf_buffer.getvalue()
    return base64.b64encode(pdf_bytes).decode("ascii")
