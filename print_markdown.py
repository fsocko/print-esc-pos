import sys
import textwrap
import mistune
import printer_utils
import ftfy
import re

PRINTER_CHAR_WIDTH = printer_utils.PRINTER_CHAR_WIDTH

# ---------------------------
# Helpers
# ---------------------------

def is_number(text):
    return bool(re.match(r"^-?\d+(\.\d+)?$", text.strip()))

def split_decimal(value):
    if "." in value:
        left, right = value.split(".", 1)
        return left, right
    return value, ""

def analyze_decimal_columns(rows, col_count):
    col_info = []
    for col in range(col_count):
        left_max = 0
        right_max = 0
        has_decimal = False
        for row in rows:
            cell = row[col].strip()
            if is_number(cell):
                left, right = split_decimal(cell)
                left_max = max(left_max, len(left))
                right_max = max(right_max, len(right))
                if right:
                    has_decimal = True
        col_info.append({"left": left_max, "right": right_max, "decimal": has_decimal})
    return col_info

# ---------------------------
# ESC/POS Printer Wrapper
# ---------------------------

class EscPosPrinter:
    def __init__(self):
        self.printer = printer_utils.find_printer()

    def set_align(self, align):
        self.printer.set(align=align)

    def text(self, txt):
        wrapped = textwrap.wrap(txt, width=PRINTER_CHAR_WIDTH) or [""]
        for line in wrapped:
            clean = ftfy.fix_text(line)
            self.printer.text(clean + "\n")

    def raw_line(self, txt):
        clean = ftfy.fix_text(txt[:PRINTER_CHAR_WIDTH])
        self.printer.text(clean + "\n")

    def bold(self, on=True):
        self.printer.set(bold=on)

    def size(self, w=1, h=1):
        self.printer.set(width=w, height=h)

    def hr(self):
        self.raw_line("-" * PRINTER_CHAR_WIDTH)

    def newline(self, n=1):
        self.printer.text("\n" * n)

    def cut(self):
        self.printer.cut()

    def close(self):
        self.printer.close()

# ---------------------------
# Markdown Renderer
# ---------------------------

class EscPosRenderer(mistune.HTMLRenderer):
    def __init__(self, printer):
        super().__init__()
        self.p = printer
        # table state
        self._current_row = []
        self._header = []
        self._body = []
        self._in_header = False

    # Basic
    def paragraph(self, text):
        self.p.text(text)
        self.p.newline()
        return ""

    def heading(self, text, level):
        sizes = {1: (2, 2), 2: (2, 1), 3: (1, 1)}
        w, h = sizes.get(level, (1, 1))
        self.p.bold(True)
        self.p.size(w, h)
        self.p.set_align("center")
        self.p.text(text)
        self.p.set_align("left")
        self.p.size(1, 1)
        self.p.bold(False)
        self.p.newline()
        return ""

    def strong(self, text):
        self.p.bold(True)
        self.p.text(text)
        self.p.bold(False)
        return ""

    def emphasis(self, text):
        self.p.text(f"/{text}/")
        return ""

    def codespan(self, text):
        self.p.text(f"[{text}]")
        return ""

    def block_code(self, code, info=None):
        self.p.hr()
        for line in code.splitlines():
            self.p.raw_line("  " + line)
        self.p.hr()
        return ""

    def list_item(self, text):
        self.p.text(f"• {text}")
        return ""

    def thematic_break(self):
        self.p.hr()
        return ""

    # Table building
    def table_head(self, text):
        self._in_header = True
        return text

    def table_body(self, text):
        self._in_header = False
        return text

    def table_row(self, content):
        if self._in_header:
            self._header.append(self._current_row)
        else:
            self._body.append(self._current_row)
        self._current_row = []
        return content

    def table_cell(self, content, align=None, head=False):
        self._current_row.append(content.strip())
        return content

    def table(self, header):
        self._render_table(self._header, self._body)
        # reset state
        self._header = []
        self._body = []
        self._current_row = []
        return ""

    # Table rendering
    def _render_table(self, header, body):
        rows = header + body
        col_count = max(len(r) for r in rows)
        for r in rows:
            while len(r) < col_count:
                r.append("")
        col_info = analyze_decimal_columns(rows, col_count)
        col_width = PRINTER_CHAR_WIDTH // col_count
        col_widths = [col_width] * col_count

        def wrap_cell(text, width):
            return textwrap.wrap(text, width=width - 1) or [""]

        wrapped = []
        for row in rows:
            wrapped.append([wrap_cell(cell, col_widths[i]) for i, cell in enumerate(row)])

        self.p.hr()
        for i, row in enumerate(wrapped):
            max_h = max(len(cell) for cell in row)
            for line_idx in range(max_h):
                line = ""
                for col_idx, cell_lines in enumerate(row):
                    cell = cell_lines[line_idx] if line_idx < len(cell_lines) else ""
                    width = col_widths[col_idx]
                    align = "right" if is_number(cell) else "left"
                    ci = col_info[col_idx]

                    if align == "right" and ci["decimal"] and is_number(cell):
                        left, right = split_decimal(cell)
                        left = left.rjust(ci["left"])
                        right = right.ljust(ci["right"])
                        formatted = (f"{left}.{right}" if ci["right"] > 0 else left).rjust(width)
                    elif align == "right":
                        formatted = cell.rjust(width)
                    else:
                        formatted = cell.ljust(width)
                    line += formatted
                self.p.raw_line(line)
            if i == len(header) - 1:
                self.p.hr()
        self.p.hr()

# ---------------------------
# Entry Point
# ---------------------------

def render_markdown(md_text, cut=False):
    printer = EscPosPrinter()
    renderer = EscPosRenderer(printer)

    md = mistune.create_markdown(renderer=renderer, plugins=["table"])
    md(md_text)  # Let Mistune call the renderer hooks

    if cut:
        printer.cut()
    printer.close()

def main(args=None):
    import argparse
    import os
    parser = argparse.ArgumentParser(description="Print Markdown to ESC/POS printer.")
    parser.add_argument("file", nargs="?", help="Markdown file")
    parser.add_argument("-c", "--cut", action="store_true")
    parsed = parser.parse_args(args)

    if parsed.file:
        if not os.path.exists(parsed.file):
            print(f"File not found: {parsed.file}")
            sys.exit(1)
        with open(parsed.file, "r", encoding="utf-8") as f:
            md = f.read()
    else:
        md = sys.stdin.read()

    render_markdown(md, cut=parsed.cut)

if __name__ == "__main__":
    main()