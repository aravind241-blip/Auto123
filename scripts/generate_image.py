"""
Generates a square (1080x1080) "Breaking News" style image for a given article,
using an original template (gradient background + banner + headline), so we
never depend on downloading/re-using copyrighted news photography.
"""

import os
import textwrap
import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
FONT_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
FONT_REGULAR = os.path.join(FONT_DIR, "DejaVuSans.ttf")

SIZE = 1080

# Category -> (gradient top color, gradient bottom color, accent color, label)
CATEGORY_STYLE = {
    "india": ((20, 30, 55), (10, 15, 30), (255, 153, 51), "INDIA NEWS"),      # saffron accent
    "world": ((15, 25, 50), (8, 12, 25), (66, 165, 245), "WORLD NEWS"),       # blue accent
    "business": ((20, 35, 30), (8, 15, 12), (76, 217, 100), "BUSINESS NEWS"),  # green accent
    "sports": ((45, 20, 20), (18, 8, 8), (255, 87, 51), "SPORTS NEWS"),       # red/orange accent
}


def _vertical_gradient(size, top_color, bottom_color):
    img = Image.new("RGB", size, top_color)
    draw = ImageDraw.Draw(img)
    h = size[1]
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    return img


def _wrap_text(draw, text, font, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def generate(article: dict, output_path: str) -> str:
    category = article.get("category", "world")
    top_color, bottom_color, accent, label = CATEGORY_STYLE.get(
        category, CATEGORY_STYLE["world"]
    )

    img = _vertical_gradient((SIZE, SIZE), top_color, bottom_color)

    # subtle darkening vignette for readability
    overlay = Image.new("L", (SIZE, SIZE), 0)
    odraw = ImageDraw.Draw(overlay)
    odraw.rectangle([0, 0, SIZE, SIZE], fill=40)
    img = Image.composite(Image.new("RGB", (SIZE, SIZE), (0, 0, 0)), img, overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # ---- accent bar (top) ----
    draw.rectangle([0, 0, SIZE, 14], fill=accent)

    # ---- BREAKING banner ----
    banner_font = ImageFont.truetype(FONT_BOLD, 78)
    draw.rectangle([0, 70, SIZE, 190], fill=(255, 255, 255))
    bbox = draw.textbbox((0, 0), "BREAKING", font=banner_font)
    tw = bbox[2] - bbox[0]
    draw.text(((SIZE - tw) / 2, 90), "BREAKING", font=banner_font, fill=(20, 20, 20))

    # ---- category label pill ----
    label_font = ImageFont.truetype(FONT_BOLD, 34)
    lbbox = draw.textbbox((0, 0), label, font=label_font)
    lw, lh = lbbox[2] - lbbox[0], lbbox[3] - lbbox[1]
    pad_x, pad_y = 26, 14
    pill_w, pill_h = lw + pad_x * 2, lh + pad_y * 2
    pill_x = (SIZE - pill_w) / 2
    pill_y = 230
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=pill_h / 2, fill=accent
    )
    draw.text(
        (pill_x + pad_x, pill_y + pad_y - 4), label, font=label_font, fill=(15, 15, 15)
    )

    # ---- headline ----
    headline = article.get("title", "").strip()
    headline_font = ImageFont.truetype(FONT_BOLD, 66)
    max_w = SIZE - 140
    lines = _wrap_text(draw, headline, headline_font, max_w)
    # shrink font if too many lines
    while len(lines) > 6 and headline_font.size > 40:
        headline_font = ImageFont.truetype(FONT_BOLD, headline_font.size - 4)
        lines = _wrap_text(draw, headline, headline_font, max_w)

    line_height = headline_font.size + 14
    total_h = line_height * len(lines)
    start_y = (SIZE - total_h) / 2 + 30

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=headline_font)
        lw = bbox[2] - bbox[0]
        x = (SIZE - lw) / 2
        y = start_y + i * line_height
        draw.text((x, y), line, font=headline_font, fill=(255, 255, 255))

    # ---- source + date footer ----
    footer_font = ImageFont.truetype(FONT_REGULAR, 28)
    date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%d %b %Y")
    source = article.get("source", "News")
    footer_text = f"{source} · {date_str}"
    draw.rectangle([0, SIZE - 90, SIZE, SIZE], fill=(0, 0, 0))
    draw.text((40, SIZE - 62), footer_text, font=footer_font, fill=(220, 220, 220))
    right_label = "AUTO NEWS UPDATE"
    rbbox = draw.textbbox((0, 0), right_label, font=footer_font)
    rw = rbbox[2] - rbbox[0]
    draw.text((SIZE - 40 - rw, SIZE - 62), right_label, font=footer_font, fill=accent)

    img.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    sample = {
        "title": "Sample Breaking News Headline Goes Here For Testing Purposes",
        "category": "india",
        "source": "Sample Source",
    }
    generate(sample, "/tmp/sample.png")
    print("saved /tmp/sample.png")
