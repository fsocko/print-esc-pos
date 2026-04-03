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
# Printer Wrapper
# ---------------------------

class EscPosPrinter:
    def __init__(self):
        self.printer = printer_utils.find_printer()
        self.printer.text("\n")

    def set_align(self, align):
        self.printer.set(align=align)

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

    def bold(self, on=True):
        self.printer.set(bold=on)

    def font(self, font):
        self.printer.set(font=font)

    def size(self, w=1, h=1):
        self.printer.set(width=w, height=h)

    def hr(self):
        self.raw_line("-" * PRINTER_CHAR_WIDTH)

    def cut(self):
        self.printer.cut()

    def close(self):
        self.printer.close()


# ---------------------------
# AST Renderer
# ---------------------------

class AstPrinter:
    def __init__(self, printer):
        self.p = printer

        # inline state
        self.bold = False
        self.italic = False

        # current text buffer
        self.buffer = ""

    # ---------- Inline helpers ----------

    def _apply_style(self):
        self.p.bold(self.bold)
        self.p.font('b' if self.italic else 'a')

    def _append(self, text):
        if text:
            self.buffer += text

    def _flush(self):
        if self.buffer:
            self._apply_style()
            self.p.wrapped_text(self.buffer)
            self.buffer = ""

    # ---------- AST walking ----------

    def render(self, ast):
        for node in ast:
            self._render_node(node)

    def _render_children(self, node):
        for child in node.get("children", []):
            self._render_node(child)

    def _render_node(self, node):
        t = node["type"]

        # ---------- TEXT ----------
        if t == "text":
            self._append(node.get("raw", ""))

        # ---------- INLINE ----------
        elif t == "strong":
            prev = self.bold
            self.bold = True
            self._render_children(node)
            self.bold = prev

        elif t == "emphasis":
            prev = self.italic
            self.italic = True
            self._render_children(node)
            self.italic = prev

        elif t == "codespan":
            self._append(f"[{node.get('raw','')}]")

        elif t == "linebreak":
            self._flush()

        elif t == "softbreak":
            self._append(" ")

        # ---------- PARAGRAPH ----------
        elif t == "paragraph":
            self._render_children(node)
            self._flush()
            self.p.newline()

        # ---------- HEADINGS ----------
        elif t == "heading":
            level = node["attrs"]["level"]
            self._flush()

            if level == 1:
                self.p.hr()
                self.p.set_align("center")
                self.p.bold(True)
                self.p.size(2, 2)

            elif level == 2:
                self.p.bold(True)
                self.p.size(2, 1)

            else:
                self.p.bold(True)

            self._render_children(node)
            self._flush()

            if level <= 2:
                self.p.hr()

            self.p.size(1, 1)
            self.p.bold(False)
            self.p.set_align("left")
            self.p.newline()

        # ---------- CODE BLOCK ----------
        elif t == "block_code":
            self._flush()
            self.p.hr()
            for line in node["raw"].splitlines():
                self.p.wrapped_text(line)
            self.p.hr()

        # ---------- HR ----------
        elif t == "thematic_break":
            self._flush()
            self.p.hr()

        # ---------- LIST ----------
        elif t == "list":
            for item in node["children"]:
                self._render_node(item)

        elif t == "list_item":
            self._flush()
            prev_buffer = self.buffer
            self.buffer = ""

            self._render_children(node)
            content = self.buffer.strip()
            self.buffer = prev_buffer

            wrapped = textwrap.wrap(content, width=PRINTER_CHAR_WIDTH - 2)

            if wrapped:
                self.p.raw_line("• " + wrapped[0])
                for line in wrapped[1:]:
                    self.p.raw_line("  " + line)

        # ---------- TABLE ----------
        elif t == "table":
            self._flush()

            header = []
            body = []

            for child in node["children"]:
                if child["type"] == "table_head":
                    header = self._extract_table(child)
                elif child["type"] == "table_body":
                    body = self._extract_table(child)

            self._render_table(header, body)

        # ---------- FALLBACK ----------
        else:
            # ignore unknown nodes safely
            pass

    # ---------- TABLE HELPERS ----------

    def _extract_table(self, node):
        rows = []
        for row in node["children"]:
            r = []
            for cell in row["children"]:
                self.buffer = ""
                self._render_children(cell)
                r.append(self.buffer.strip())
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
        col_widths = [col_width] * col_count

        self.p.hr()

        for row_idx, row in enumerate(rows):
            line = ""

            for col_idx, cell in enumerate(row):
                width = col_widths[col_idx]
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

            self.p.raw_line(line)

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