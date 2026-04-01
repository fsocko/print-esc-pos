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
        self.printer.text("\n") # Prepend new line for compatibility

    def set_align(self, align):
        self.printer.set(align=align)

    def text(self, txt):
        wrapped = textwrap.wrap(
            txt,
            width=PRINTER_CHAR_WIDTH,
            break_long_words=True,
            break_on_hyphens=False
        ) or [""]
        for line in wrapped:
            clean = ftfy.fix_text(line)
            self.printer.text(clean + "\n")

    def raw_line(self, txt):
        wrapped = textwrap.wrap(
            txt,
            width=PRINTER_CHAR_WIDTH,
            break_long_words=True,
            break_on_hyphens=False
        ) or [""]
        for line in wrapped:
            clean = ftfy.fix_text(line)
            self.printer.text(clean + "\n")
            
    def raw_line_no_wrap(self, txt):
        clean = ftfy.fix_text(txt.ljust(PRINTER_CHAR_WIDTH)[:PRINTER_CHAR_WIDTH])
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
        self._print_inline(text)
        self.p.newline(2)  # add extra line after paragraph for spacing
        return ""
    
    def heading(self, text, level):
        if level == 1:
            self.p.hr()
            self.p.bold(True)
            self.p.size(2, 2)
            self.p.set_align("center")
            self.p.text(text.upper())
            self.p.hr()

        elif level == 2:
            self.p.bold(True)
            self.p.size(2, 1)
            self.p.text(text.upper())
            self.p.hr()

        elif level == 3:
            self.p.bold(True)
            self.p.size(1, 1)
            self.p.text(text)

        elif level == 4:
            self.p.text(f"# {text}")

        elif level == 5:
            self.p.text(f"- {text}")

        elif level == 6:
            self.p.text(f"--- {text}")
        
        self.p.size(1, 1)
        self.p.bold(False)
        self.p.set_align("left")
        self.p.newline()
        return ""

    def strong(self, text):
        return f"<b>{text or ''}</b>"

    def emphasis(self, text):
        return f"<i>{text or ''}</i>"
    
    def codespan(self, text):
        return f"<code>{text or ''}</code>"

    def block_code(self, code, info=None):
        self.p.hr()
        for line in code.splitlines():
            self.p.text(line)  # instead of raw_line
        self.p.hr()
        return ""

    def list_item(self, text):
        prefix = "• "
        indent = "  "

        wrapped = textwrap.wrap(
            text,
            width=PRINTER_CHAR_WIDTH - len(prefix),
            break_long_words=True
        )

        if not wrapped:
            return ""

        self.p.raw_line(prefix + wrapped[0])

        for line in wrapped[1:]:
            self.p.raw_line(indent + line)
        return ""

    def _print_inline(self, text):
        i = 0
        buffer = ""
        bold = False
        italic = False
        code = False

        def flush_buffer():
            nonlocal buffer
            if not buffer:
                return
            font = 'b' if italic else 'a'
            self.p.printer.set(font=font, bold=bold)
            self.p.printer.text(buffer)
            buffer = ""
            if italic:
                self.p.printer.set(font='a', bold=bold)

        while i < len(text or ""):
            if text.startswith("<b>", i):
                flush_buffer()
                bold = True
                i += 3
            elif text.startswith("</b>", i):
                flush_buffer()
                bold = False
                i += 4
            elif text.startswith("<i>", i):
                flush_buffer()
                italic = True
                i += 3
            elif text.startswith("</i>", i):
                flush_buffer()
                italic = False
                i += 4
            elif text.startswith("<code>", i):
                flush_buffer()
                code = True
                i += 6
            elif text.startswith("</code>", i):
                flush_buffer()
                code = False
                i += 7
            elif text.startswith("<br>", i) or text.startswith("\n", i):
                flush_buffer()
                self.p.newline()
                i += 4 if text.startswith("<br>", i) else 1
            elif text.startswith("[qrcode:", i):
                #example: "[qrcode:https://example.com]"
                flush_buffer()
                end = text.find("]", i)
                if end != -1:
                    qr_text = text[i+8:end].strip().replace("\n", "")
                    if qr_text:
                        self.p.set_align("center")
                        self.p.printer.qr(qr_text, size=8)
                        self.p.newline()
                        self.p.set_align("left")
                    i = end + 1
                else:
                    buffer += text[i]
                    i += 1
            elif text.startswith("[barcode:", i):
                
                #example: "[barcode:123456789012]"        # defaults to EAN13
                #example: "[barcode:ABC123:CODE39]"       # explicitly use Code39
                
                flush_buffer()
                end = text.find("]", i)
                if end != -1:
                    # Extract content between [barcode: and ]
                    content = text[i+9:end].strip().replace("\n", "")
                    if content:
                        parts = content.split(":")
                        code_text = parts[0]
                        code_type = parts[1].upper() if len(parts) > 1 else "EAN13"
                        self.p.set_align("center")
                        self.p.printer.barcode(
                            code_text,
                            code_type,     # barcode type, optional
                            width=2,
                            height=100,
                            pos='below',
                            font='a'
                        )
                        self.p.newline()
                        self.p.set_align("left")
                    i = end + 1
                else:
                    buffer += text[i]
                    i += 1
            else:
                if code:
                    buffer += f"[{text[i]}]"
                else:
                    buffer += text[i]
                i += 1

        flush_buffer()
        self.p.newline()  # ensure paragraph spacing after last inline

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
        if not rows:
            return ""

        col_count = max(len(r) for r in rows)

        # Normalize row lengths
        for r in rows:
            while len(r) < col_count:
                r.append("")

        col_info = analyze_decimal_columns(rows, col_count)

        # Add spacing between columns
        padding = 2
        col_width = (PRINTER_CHAR_WIDTH - (col_count - 1) * padding) // col_count
        col_widths = [col_width] * col_count

        def wrap_cell(text, width):
            return textwrap.wrap(
                text,
                width=width,
                break_long_words=True,
                break_on_hyphens=False
            ) or [""]

        # Wrap all cells
        wrapped_rows = []
        for row in rows:
            wrapped_row = []
            for i, cell in enumerate(row):
                wrapped_row.append(wrap_cell(cell, col_widths[i]))
            wrapped_rows.append(wrapped_row)

        self.p.hr()

        for row_idx, row in enumerate(wrapped_rows):
            max_height = max(len(cell) for cell in row)

            for line_idx in range(max_height):
                line = ""

                for col_idx, cell_lines in enumerate(row):
                    cell = cell_lines[line_idx] if line_idx < len(cell_lines) else ""
                    width = col_widths[col_idx]
                    ci = col_info[col_idx]

                    if is_number(cell):
                        if ci["decimal"]:
                            left, right = split_decimal(cell)
                            left = left.rjust(ci["left"])
                            right = right.ljust(ci["right"])
                            formatted = (
                                f"{left}.{right}" if ci["right"] > 0 else left
                            ).rjust(width)
                        else:
                            formatted = cell.rjust(width)
                    else:
                        formatted = cell.ljust(width)

                    line += formatted

                    # add spacing between columns (except last)
                    if col_idx < col_count - 1:
                        line += " " * padding

                # CRITICAL: no wrapping here
                self.p.raw_line_no_wrap(line)

            # Draw separator after header
            if header and row_idx == len(header) - 1:
                self.p.hr()

        self.p.hr()
        
    def qr(self, text):
        # Uses your ESC/POS printer to print a QR code
        self.p.printer.qr(text, size=6, center=True)
        self.p.newline()
        return ""

    def barcode(self, text, type="EAN13"):
        self.p.printer.barcode(text, type, width=2, height=100, pos='below', font='a')
        self.p.newline()
        return ""

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