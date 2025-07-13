from PIL import Image, ImageDraw, ImageFont
import re
import textwrap

def parse_markdown_table(markdown: str):
    lines = [line.strip() for line in markdown.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Markdown table must have at least a header and separator")

    content_lines = [line for line in lines if not re.match(r'^\s*\|?\s*-+\s*\|', line)]
    rows = [re.split(r'\s*\|\s*', line.strip('| ')) for line in content_lines]
    
    headers = rows[0]
    max_columns = len(headers)
    data = [row + [''] * (max_columns - len(row)) for row in rows[1:]]
    return headers, data

def wrap_cell(text, font, max_width):
    """Wrap text for a single cell within max width using the font's metrics."""
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if font.getlength(test_line) <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def render_table_image(headers, rows, font_path, font_size=20, padding=10, col_spacing=30, max_col_width=200, rotate_angle=90, output_file="table.png"):
    font = ImageFont.truetype(font_path, font_size)

    # Determine max text width per column
    all_rows = [headers] + rows
    num_cols = len(headers)
    wrapped_cells = [[wrap_cell(cell, font, max_col_width) for cell in row] for row in all_rows]

    # Compute column widths from the longest line in wrapped content
    col_widths = [
        max(
            font.getlength(line)
            for row in wrapped_cells
            for line in row[col_idx]
        )
        for col_idx in range(num_cols)
    ]

    # Compute row heights from the number of wrapped lines
    line_height = font_size + 4
    row_heights = [
        max(len(cell) for cell in row) * line_height for row in wrapped_cells
    ]

    # Image dimensions
    image_width = int(sum(col_widths) + col_spacing * (num_cols - 1) + 2 * padding)
    image_height = sum(row_heights) + 2 * padding

    # Create image
    img = Image.new("RGB", (image_width, image_height), color="white")
    draw = ImageDraw.Draw(img)

    # Draw content
    y = padding
    for row_idx, row in enumerate(wrapped_cells):
        x = padding
        max_lines = max(len(cell) for cell in row)
        for col_idx, cell_lines in enumerate(row):
            for line_idx, line in enumerate(cell_lines):
                draw.text((x, y + line_idx * line_height), line, font=font, fill="black")
            x += col_widths[col_idx] + col_spacing
        y += row_heights[row_idx]

    # Rotate image
    img = img.rotate(rotate_angle, expand=True)
    img.save(output_file)
    print(f"Saved image: {output_file}")

# Example usage
markdown_table = """
| 1:1 Volume (oz) |  1:1 Volume (ml) | Weight of sugar in 2:1 per volume (g)  |  2:2 Volume required (ml) Per 1:1 recipe |
|-----------------|-------------------------------------------|-----------------------------|
|             1   |        28.41306  |                 26.00  |  19.85                      |
|             1/2 |        14.20653  |                 13.00  |  9.92                       |
|             1/4 |        7.103265  |                 6.50   |  4.96                       |
|             3/4 |        21.309795 |                 19.50  |  14.88                      |
|             1/8 |        3.5516325 |                 3.25   |  2.48                       |
|             1/9 |        2.841306  |                 2.60   |  1.98                       |
|             -   |        1         |                 0.92   |  0.70                       |
|             -   |        10        |                 9.15   |  6.98                       |
|             -   |        20        |                 18.30  |  13.97                      |
|             -   |        30        |                 27.45  |  20.95                      |
|             -   |        40        |                 36.60  |  27.94                      |
|             -   |        50        |                 45.75  |  34.92                      |
"""

font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
headers, rows = parse_markdown_table(markdown_table)
render_table_image(headers, rows, font_path, max_col_width=180)
