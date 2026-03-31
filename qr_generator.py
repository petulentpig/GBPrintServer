import base64
import io

import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image, ImageDraw, ImageFont

# Letter page at 200 DPI: 8.5" x 11"
PAGE_WIDTH = int(8.5 * 200)   # 1700 px
PAGE_HEIGHT = int(11 * 200)   # 2200 px
MARGIN = 100  # px


def generate_qr(url: str, order_number: str) -> str:
    """Generate a single-page PDF with QR code and Code 128 barcode."""

    # --- Create letter-sized canvas ---
    canvas = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)

    # --- Font ---
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()

    usable_width = PAGE_WIDTH - 2 * MARGIN
    y_cursor = MARGIN

    # --- Order label at top ---
    label = f"Order #{order_number}"
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(((PAGE_WIDTH - text_w) // 2, y_cursor), label, fill="black", font=font)
    y_cursor += text_h + 60

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

    # Scale QR to fit within usable width, max 800px
    max_qr = min(usable_width, 800)
    qr_img = qr_img.resize((max_qr, max_qr), Image.NEAREST)
    qr_x = (PAGE_WIDTH - max_qr) // 2
    canvas.paste(qr_img, (qr_x, y_cursor))
    y_cursor += max_qr + 60

    # --- Code 128 Barcode (order number) ---
    code128 = barcode.get("code128", str(order_number), writer=ImageWriter())
    barcode_buffer = io.BytesIO()
    code128.write(barcode_buffer, options={
        "module_width": 0.5,
        "module_height": 25,
        "font_size": 18,
        "text_distance": 5,
        "quiet_zone": 6.5,
    })
    barcode_buffer.seek(0)
    barcode_img = Image.open(barcode_buffer).convert("RGB")

    # Scale barcode to fit usable width if needed
    bc_w, bc_h = barcode_img.size
    if bc_w > usable_width:
        scale = usable_width / bc_w
        barcode_img = barcode_img.resize(
            (int(bc_w * scale), int(bc_h * scale)), Image.LANCZOS
        )
    bc_w, bc_h = barcode_img.size
    bc_x = (PAGE_WIDTH - bc_w) // 2
    canvas.paste(barcode_img, (bc_x, y_cursor))

    # --- Save as single-page PDF ---
    pdf_buffer = io.BytesIO()
    canvas.save(pdf_buffer, format="PDF", resolution=200)
    pdf_bytes = pdf_buffer.getvalue()
    return base64.b64encode(pdf_bytes).decode("ascii")
