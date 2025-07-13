from PIL import Image, ImageDraw, ImageFont

# Sample table data
headers = ["Name", "Qty", "Price"]
rows = [
    ["Apple", "2", "€0.50"],
    ["Banana", "1", "€0.30"],
    ["Orange", "3", "€1.00"]
]

# Configuration
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"  # Adjust path for Windows/Mac
font_size = 20
padding = 10
col_spacing = 30

# Load font
font = ImageFont.truetype(font_path, font_size)

# Determine column widths
col_widths = [max(font.getlength(cell) for cell in col) for col in zip(headers, *rows)]

# Calculate image size
image_width = int(sum(col_widths) + col_spacing * (len(headers) - 1) + 2 * padding)
image_height = (len(rows) + 1) * (font_size + 10) + 2 * padding

# Create image
img = Image.new("RGB", (image_width, image_height), color="white")
draw = ImageDraw.Draw(img)

# Draw header and rows
y = padding
for i, row in enumerate([headers] + rows):
    x = padding
    for j, cell in enumerate(row):
        draw.text((x, y), cell, font=font, fill="black")
        x += col_widths[j] + col_spacing
    y += font_size + 10

img = img.rotate(90, expand=True)

# Save image or return it
img.save("table.png")
