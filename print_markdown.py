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
# Printer Wrapper (CLEAN)
# ---------------------------

class EscPosPrinter:
    def __init__(self):
        self.printer = printer_utils.find_printer()
        self.printer.text("\n")

    def set_align(self, align):
        self.printer.set(align=align)

    def set_style(self, bold=False, italic=False):
        self.printer.set(
            bold=bold,
            font='b' if italic else 'a'
        )

    def write(self, txt):
        self.printer.text(ftfy.fix_text(txt))

    def newline(self, n=1):
        self.printer.text("\n" * n)

    def wrapped_text(self, txt, indent=0):
        wrapped = textwrap.wrap(
            txt,
            width=PRINTER_CHAR_WIDTH - indent,
            break_long_words=True,
            break_on_hyphens=False
        ) or [""]

        for i, line in enumerate(wrapped):
            prefix = " " * indent if i > 0 else ""
            self.printer.text(ftfy.fix_text(prefix + line) + "\n")

    def raw_line(self, txt):
        clean = ftfy.fix_text(txt.ljust(PRINTER_CHAR_WIDTH)[:PRINTER_CHAR_WIDTH])
        self.printer.text(clean + "\n")

    def raw_line_no_wrap(self, txt):
        self.raw_line(txt)

    def bold(self, on=True):
        self.printer.set(bold=on)

    def font(self, font):
        self.printer.set(font=font)

    def size(self, w=1, h=1):
        self.printer.set(width=w, height=h)

    def hr(self):
        self.raw_line("-" * PRINTER_CHAR_WIDTH)

    def qr(self, text):
        self.set_align("center")
        self.printer.qr(text, size=8)
        self.newline()
        self.set_align("left")

    def barcode(self, code, code_type="EAN13"):
        self.set_align("center")
        self.printer.barcode(code, code_type, width=2, height=100, pos='below', font='a')
        self.newline()
        self.set_align("left")

    def cut(self):
        self.printer.cut()

    def close(self):
        self.printer.close()


# ---------------------------
# AST Renderer (CLEAN)
# ---------------------------

class AstPrinter:
    def __init__(self, printer):
        self.p = printer
        self.bold = False
        self.italic = False
        self.buffer = ""

    # ---------------------------
    # Inline handling
    # ---------------------------

    def _append(self, text):
        if text:
            self.buffer += text

    def _flush(self):
        if not self.buffer:
            return
        self.p.set_style(self.bold, self.italic)
        self._print_with_commands(self.buffer)
        self.buffer = ""

    def _print_with_commands(self, text):
        i = 0
        buf = ""

        def flush_buf():
            nonlocal buf
            if buf:
                self.p.write(buf)
                buf = ""

        while i < len(text):
            if text.startswith("[qrcode:", i):
                flush_buf()
                end = text.find("]", i)
                if end != -1:
                    qr = text[i+8:end].strip()
                    if qr:
                        self.p.qr(qr)
                    i = end + 1
                    continue

            elif text.startswith("[barcode:", i):
                flush_buf()
                end = text.find("]", i)
                if end != -1:
                    content = text[i+9:end].strip()
                    if content:
                        parts = content.split(":")
                        code = parts[0]
                        code_type = parts[1].upper() if len(parts) > 1 else "EAN13"
                        self.p.barcode(code, code_type)
                    i = end + 1
                    continue

            buf += text[i]
            i += 1

        flush_buf()

    # ---------------------------
    # AST walking
    # ---------------------------

    def render(self, ast):
        for node in ast:
            self._node(node)

    def _children(self, node):
        for c in node.get("children", []):
            self._node(c)

    def _node(self, node):
        t = node["type"]

        if t == "text":
            self._append(node.get("raw", ""))

        elif t == "strong":
            prev = self.bold
            self.bold = True
            self._children(node)
            self.bold = prev

        elif t == "emphasis":
            prev = self.italic
            self.italic = True
            self._children(node)
            self.italic = prev

        elif t == "codespan":
            self._append(f"[{node.get('raw','')}]")

        elif t == "linebreak":
            self._flush()

        elif t == "softbreak":
            self._append(" ")

        elif t == "paragraph":
            self._children(node)
            self._flush()
            self.p.newline()

        elif t == "heading":
            level = node["attrs"]["level"]
            self._flush()

            text = self._capture_text(node)

            if level == 1:
                self.p.hr()
                self.p.set_align("center")
                self.p.bold(True)
                self.p.size(2, 2)
                self.p.wrapped_text(text.upper())
                self.p.hr()

            elif level == 2:
                self.p.bold(True)
                self.p.size(2, 1)
                self.p.wrapped_text(text.upper())
                self.p.hr()
                
            elif level == 3:
                self.p.bold(True)
                self.p.size(1, 1)
                self.p.wrapped_text(text)

            elif level == 4:
                self.p.wrapped_text(f"# {text}")

            elif level == 5:
                self.p.wrapped_text(f"- {text}")

            elif level == 6:
                self.p.wrapped_text(f"  {text}")

            else:
                self.p.bold(True)
                self.p.wrapped_text(text)

            self.p.size(1, 1)
            self.p.bold(False)
            self.p.set_align("left")
            self.p.newline()

        elif t == "block_code":
            self._flush()
            self.p.hr()
            for line in node["raw"].splitlines():
                self.p.wrapped_text(line)
            self.p.hr()

        elif t == "thematic_break":
            self._flush()
            self.p.hr()

        elif t == "list":
            for item in node.get("children", []):
                self._node(item)

        elif t == "list_item":
            self._flush()

            # Recursively collect all text inside this list_item, preserving formatting
            def capture_list_item_text(node):
                texts = []
                for c in node.get("children", []):
                    if c["type"] == "text":
                        texts.append(c.get("raw", ""))
                    elif c["type"] in ("strong", "emphasis", "codespan"):
                        # Temporarily apply formatting
                        prev_bold, prev_italic = self.bold, self.italic
                        if c["type"] == "strong":
                            self.bold = True
                        elif c["type"] == "emphasis":
                            self.italic = True
                        texts.append(capture_list_item_text(c))
                        self.bold, self.italic = prev_bold, prev_italic
                    else:
                        texts.append(capture_list_item_text(c))
                return "".join(texts)

            text = capture_list_item_text(node)
            wrapped = textwrap.wrap(text, width=PRINTER_CHAR_WIDTH - 2)
            if wrapped:
                self.p.raw_line("• " + wrapped[0])
                for line in wrapped[1:]:
                    self.p.raw_line("  " + line)
        
        elif t == "table":
            self._flush()
            header = []
            body = []

            for child in node["children"]:
                if child["type"] == "table_head":
                    header = self._extract_rows(child)
                elif child["type"] == "table_body":
                    body = self._extract_rows(child)

            self._render_table(header, body)

    # ---------------------------
    # Safe capture
    # ---------------------------

    def _capture_text(self, node):
        saved_buffer = self.buffer
        saved_bold = self.bold
        saved_italic = self.italic

        self.buffer = ""
        self.bold = False
        self.italic = False

        self._children(node)
        text = self.buffer.strip()

        self.buffer = saved_buffer
        self.bold = saved_bold
        self.italic = saved_italic

        return text

    def _extract_rows(self, node):
        rows = []
        for row in node["children"]:
            r = []
            for cell in row["children"]:
                r.append(self._capture_text(cell))
            rows.append(r)
        return rows

    def _render_table(self, header, body):
        rows = header + body
        if not rows:
            return

        col_count = max(len(r) for r in rows)

        for r in rows:
            while len(r) < col_count:
                r.append("")

        col_info = analyze_decimal_columns(rows, col_count)

        padding = 2
        col_width = (PRINTER_CHAR_WIDTH - (col_count - 1) * padding) // col_count

        self.p.hr()

        for row_idx, row in enumerate(rows):
            line = ""
            for col_idx, cell in enumerate(row):
                width = col_width
                ci = col_info[col_idx]

                if is_number(cell):
                    if ci["decimal"]:
                        left, right = split_decimal(cell)
                        left = left.rjust(ci["left"])
                        right = right.ljust(ci["right"])
                        formatted = f"{left}.{right}".rjust(width)
                    else:
                        formatted = cell.rjust(width)
                else:
                    formatted = cell.ljust(width)

                line += formatted
                if col_idx < col_count - 1:
                    line += " " * padding

            self.p.raw_line_no_wrap(line)

            if header and row_idx == len(header) - 1:
                self.p.hr()

        self.p.hr()


# ---------------------------
# Entry Point
# ---------------------------

def render_markdown(md_text, cut=False):
    printer = EscPosPrinter()
    renderer = AstPrinter(printer)

    md = mistune.create_markdown(renderer=None, plugins=["table"])
    ast = md(md_text)

    renderer.render(ast)
    renderer._flush()

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