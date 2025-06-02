import pandas as pd
import dataframe_image as dfi
import re
from PIL import Image


def parse_markdown_table(md: str) -> pd.DataFrame:
    """
    Parses a markdown table string into a pandas DataFrame.
    Supports header separators and trims pipes/spaces.
    Leaves text like fractions as strings and formats them as such.
    """
    lines = [line.strip() for line in md.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        raise ValueError("Markdown table must have at least a header and separator line")

    # Find separator line (---|---) and split input into header and data
    sep_index = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*\|?\s*-+', line):
            sep_index = i
            break
    if sep_index is None:
        raise ValueError("Markdown table missing separator line")

    header_lines = lines[:sep_index]
    data_lines = lines[sep_index+1:]

    # Handle multiline headers
    headers_split = [re.split(r'\s*\|\s*', line.strip('| ')) for line in header_lines]
    headers = [" ".join(col).strip() for col in zip(*headers_split)]

    # Parse data rows
    rows = [re.split(r'\s*\|\s*', line.strip('| ')) for line in data_lines]

    # Build DataFrame
    df = pd.DataFrame(rows, columns=headers)

    # Try to convert cells to float, or leave as-is if not possible
    def try_parse(val):
        try:
            cleaned = val.replace(',', '').replace('€', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return val.strip()

    for col in df.columns:
        df[col] = df[col].apply(try_parse)

    return df


def style_df(df):
    """
    Style DataFrame with alternating row colors, centered text, and formatted floats.
    """
    return (
        df.style
        .set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-size', '14pt')]},
            {'selector': 'td', 'props': [('font-size', '12pt'), ('padding', '8px')]},
            {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]},
        ])
        .set_properties(**{
            'text-align': 'center',
            'border': '1px solid black'
        })
        .format(lambda x: f"{x:.2f}" if isinstance(x, float) else str(x))
    )


# Example markdown table input
markdown_table = """
| 1:1 Volume (oz) |  1:1 Volume (ml) | Weight of sugar in 2:1 per volume (g)  |  2:2 Volume required (ml) Per 1:1 recipe |
|-----------------|------------------|----------------------------------------|------------------------------------------|
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

# Process and export
df = parse_markdown_table(markdown_table)
styled_df = style_df(df)
dfi.export(styled_df, "styled_table.png")

# Rotate the image if needed
img = Image.open("styled_table.png")
rotated_img = img.rotate(90, expand=True)
rotated_img.save("styled_table.png")

print("Table image saved as styled_table.png")
