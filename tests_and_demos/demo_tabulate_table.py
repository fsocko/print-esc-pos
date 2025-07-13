from tabulate import tabulate
from PIL import Image, ImageDraw, ImageFont

def markdown_to_rows(markdown: str):
    lines = [line.strip() for line in markdown.strip().splitlines() if line.strip()]
    lines = [line for line in lines if not re.match(r'^\s*\|?\s*-+\s*\|', line)]  # Remove separator lines
    rows = [re.split(r'\s*\|\s*', line.strip('| ')) for line in lines]
    return rows[0], rows[1:]

def text_table_to_image(table_str: str, font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size=20, padding=10, bg_color="white", text_color="black"):
    font = ImageFont.truetype(font_path, font_size)
    lines = table_str.splitlines()
    width = max(int(font.getlength(line)) for line in lines) + 2 * padding
    height = (font_size + 5) * len(lines) + 2 * padding

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill=text_color)
        y += font_size + 5

    return img

# Example markdown input
import re

markdown = """
| Item   | Qty | Price |
|--------|-----|--------|
| Apple  | 2   | 0.50   |
| Banana | 1   | 0.30   |
| Orange | 3   | 1.00   |
"""

headers, data = markdown_to_rows(markdown)

# Format text table using tabulate
text_table = tabulate(data, headers=headers, tablefmt="plain", numalign="right", stralign="left")

# Convert text to image
img = text_table_to_image(text_table)
img.save("text_table.png")
print("Saved table image as text_table.png")
