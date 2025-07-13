import re
from tabulate import tabulate
from escpos.printer import Usb  # Or use Serial/Network depending on your printer
import printer_utils

def parse_markdown_table(md):
    lines = md.strip().splitlines()
    # Remove separator line
    lines = [line for line in lines if not re.match(r'^\s*\|?[-:\s|]+\|?\s*$', line)]
    table = []
    for line in lines:
        row = [cell.strip() for cell in line.strip('|').split('|')]
        table.append(row)
    return table

def format_table_text(table):
    # Determine max width of each column
    col_widths = [max(len(row[i]) for row in table) for i in range(len(table[0]))]

    # Right-align and join cells
    padded_rows = []
    for i, row in enumerate(table):
        padded_row = [cell.rjust(col_widths[j]) for j, cell in enumerate(row)]
        padded_rows.append(" | ".join(padded_row))

        # After the header row, insert an underline row
        if i == 0:
            # Do something to underline etc:
            # printer.set(underline=1)
            underline = ["-" * col_widths[j] for j in range(len(row))]
            padded_rows.append(" | ".join(underline))

    return padded_rows

def rotate_text_90(text_lines):
    max_len = max(len(line) for line in text_lines)
    padded = [line.ljust(max_len) for line in text_lines]
    rotated_lines = []
    for col in range(max_len):
        line = ''.join(padded[row][col] for row in reversed(range(len(padded))))
        rotated_lines.append(line.rstrip())
    return rotated_lines

def print_rotated_table(markdown_table):

    # Step 1: Parse and format
    table = parse_markdown_table(markdown_table)
    pretty_text = format_table_text(table)

    # Step 2: Rotate 90 degrees
    rotated_lines = rotate_text_90(pretty_text)

    # Debug
    #print("\n".join(rotated_lines))

    # Step 3: Connect to ESC/POS printer    
    printer = printer_utils.find_printer()
    printer_utils.initialize_printer(printer)
    printer.set(align='left', font='a', width=1, height=1)

    printer.set(underline=True) # This does nothing? FIXME:
    for line in rotated_lines:
        printer._raw(b'\x1b\x56\x01')  # ESC V 1 = 90° rotation
        printer.text(line + "\n")
    printer._raw(b'\x1b\x56\x00')  # Reset rotation to 0°
    printer.set(underline=False)
    printer.cut()

# Example markdown input
markdown_table = """
| 1:1 Volume (oz) |  1:1 Volume (ml) | Weight of sugar in 2:1 per volume (g)  |  2:2 Volume required (ml) Per 1:1 recipe |
|-----------------|------------------|----------------------------------------|------------------------------------------|
| 1               | 28.41306         | 26.00                                  |  19.85                                   |
| 1/2             | 14.20653         | 13.00                                  |  9.92                                    |
| 1/4             | 7.103265         | 6.50                                   |  4.96                                    |
| 3/4             | 21.309795        | 19.50                                  |  14.88                                   |
| 1/8             | 3.5516325        | 3.25                                   |  2.48                                    |
| 1/9             | 2.841306         | 2.60                                   |  1.98                                    |
| -               | 1                | 0.92                                   |  0.70                                    |
| -               | 10               | 9.15                                   |  6.98                                    |
| -               | 20               | 18.30                                  |  13.97                                   |
| -               | 30               | 27.45                                  |  20.95                                   |
| -               | 40               | 36.60                                  |  27.94                                   |
| -               | 50               | 45.75                                  |  34.92                                   |
"""

markdown_table_s = """
| Name  | Age | City     |
|-------|-----|----------|
| Alice | 30  | Lisbon   |
| Bob   | 25  | Warsaw   |
| Carol | 40  | Aberdeen |
"""


print_rotated_table(markdown_table)
