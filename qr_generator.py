import base64
import io
from datetime import datetime

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

# Letter page at 200 DPI: 8.5" x 11"
PAGE_WIDTH = int(8.5 * 200)   # 1700 px
PAGE_HEIGHT = int(11 * 200)   # 2200 px
MARGIN = 150


def _load_fonts():
    """Load fonts with fallbacks."""
    try:
        title_font = ImageFont.truetype("arial.ttf", 56)
        label_font = ImageFont.truetype("arial.ttf", 36)
        detail_font = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        title_font = ImageFont.load_default()
        label_font = title_font
        detail_font = title_font
    return title_font, label_font, detail_font


def _format_date(date_str: str) -> str:
    """Parse Shopify ISO date and return a clean formatted string."""
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y  %I:%M %p")
    except (ValueError, TypeError):
        return date_str


def _draw_separator(draw, y, width, margin):
    """Draw a thin horizontal rule."""
    draw.line([(margin, y), (width - margin, y)], fill="#CCCCCC", width=2)


def _render_label(order_number: str, customer_name: str = "", order_date: str = "") -> Image.Image:
    """Render the label canvas with order details and barcode."""
    title_font, label_font, detail_font = _load_fonts()

    canvas = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    usable_width = PAGE_WIDTH - 2 * MARGIN
    y = MARGIN

    # ── Store name ──
    store_name = "THE GYPSY BELLE BOUTIQUE"
    bbox = draw.textbbox((0, 0), store_name, font=title_font)
    draw.text(((PAGE_WIDTH - (bbox[2] - bbox[0])) // 2, y), store_name, fill="black", font=title_font)
    y += (bbox[3] - bbox[1]) + 40

    # ── Separator ──
    _draw_separator(draw, y, PAGE_WIDTH, MARGIN)
    y += 30

    # ── Order number ──
    order_label = f"Order  #{order_number}"
    bbox = draw.textbbox((0, 0), order_label, font=label_font)
    draw.text(((PAGE_WIDTH - (bbox[2] - bbox[0])) // 2, y), order_label, fill="black", font=label_font)
    y += (bbox[3] - bbox[1]) + 20

    # ── Date & Time ──
    formatted_date = _format_date(order_date)
    if formatted_date:
        bbox = draw.textbbox((0, 0), formatted_date, font=detail_font)
        draw.text(((PAGE_WIDTH - (bbox[2] - bbox[0])) // 2, y), formatted_date, fill="#444444", font=detail_font)
        y += (bbox[3] - bbox[1]) + 20

    # ── Customer name ──
    if customer_name:
        cust_label = f"Customer:  {customer_name}"
        bbox = draw.textbbox((0, 0), cust_label, font=detail_font)
        draw.text(((PAGE_WIDTH - (bbox[2] - bbox[0])) // 2, y), cust_label, fill="#444444", font=detail_font)
        y += (bbox[3] - bbox[1]) + 20

    # ── Separator ──
    y += 10
    _draw_separator(draw, y, PAGE_WIDTH, MARGIN)
    y += 50

    # ── Code 128 Barcode ──
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

    bc_w, bc_h = barcode_img.size
    if bc_w > usable_width:
        scale = usable_width / bc_w
        barcode_img = barcode_img.resize(
            (int(bc_w * scale), int(bc_h * scale)), Image.LANCZOS
        )
    bc_w, bc_h = barcode_img.size
    canvas.paste(barcode_img, ((PAGE_WIDTH - bc_w) // 2, y))

    return canvas


def generate_label_png(order_number: str, customer_name: str = "", order_date: str = "") -> bytes:
    """Generate the label as PNG bytes (for Slack upload)."""
    canvas = _render_label(order_number, customer_name, order_date)
    png_buffer = io.BytesIO()
    canvas.save(png_buffer, format="PNG")
    return png_buffer.getvalue()


def generate_qr(url: str, order_number: str, customer_name: str = "", order_date: str = "") -> str:
    """Generate a single-page PDF with order details and barcode, return as base64."""
    canvas = _render_label(order_number, customer_name, order_date)
    pdf_buffer = io.BytesIO()
    canvas.save(pdf_buffer, format="PDF", resolution=200)
    return base64.b64encode(pdf_buffer.getvalue()).decode("ascii")
