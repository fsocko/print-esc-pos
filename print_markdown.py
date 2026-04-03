import sys
import textwrap
import printer_utils
import ftfy
import re

from marko import Markdown
from marko.ext import gfm
from marko.block import Heading, Paragraph, List, ListItem, FencedCode, ThematicBreak
from marko.inline import Emphasis, CodeSpan, LineBreak, AutoLink, Link


from marko import Markdown
from marko.block import Heading, Paragraph, List, ListItem, FencedCode, ThematicBreak
from marko.ext import gfm

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

def _text(node):
    """
    Recursively extract text from a node.
    Leaf nodes are just strings in Marko 2.2.2.
    """
    if isinstance(node, str):
        return node
    if hasattr(node, "children"):
        return "".join(_text(c) for c in node.children)
    return str(getattr(node, "children", ""))

# ---------------------------
# ESC/POS Printer Wrapper
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
# AST Renderer
# ---------------------------

class AstPrinter:
    def __init__(self, printer):
        self.p = printer
        self.bold = False
        self.italic = False
        self.buffer = ""

    # --- Inline commands QR/Barcode ---
    def _append(self, text):
        if text:
            self.buffer += text

    def _flush(self):
        if not self.buffer:
            return
        self._print_with_commands(self.buffer)
        self.buffer = ""

    def _print_with_commands(self, text):
        i = 0
        buf = ""
        def flush_buf():
            nonlocal buf
            if buf:
                self.p.set_style(self.bold, self.italic)
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
        
    def _text(self, node):
        """
        Recursively extract text from a node.
        """
        if isinstance(node, str):
            return node
        if hasattr(node, "children"):
            return "".join(self._text(c) for c in node.children)
        return str(getattr(node, "children", ""))

    # --- Node traversal ---
    def _node(self, node):
        node_type = node.__class__.__name__

        # --- Inline nodes ---
        if isinstance(node, str):
            self._append(_text(node))
            return

        if node_type == "Strong":
            prev = self.bold
            self.bold = True
            for c in getattr(node, "children", []):
                self._node(c)
            self.bold = prev

        if node_type == "Emphasis":
            prev = self.italic
            self.italic = True
            for c in getattr(node, "children", []):
                self._node(c)
            self.italic = prev
            
        if node_type == "CodeSpan":
            self._append(f"[{_text(node)}]")
            return
        if node_type == "LineBreak":
            self._flush()
            self.p.newline()
            return

        # --- Block nodes ---
        if node_type == "Paragraph":
            self._append(_text(node))
            self._flush()
            self.p.newline()
        elif node_type == "Heading":
            level = getattr(node, "level", 1)
            self._flush()
            text = self._text(node)
            
            if level == 1:
                self.p.hr()
                self.p.set_align("center")
                self.p.bold(True)
                self.p.size(2,2)
                self.p.wrapped_text(text.upper())
                self.p.hr()
            elif level == 2:
                self.p.wrapped_text("\n")
                self.p.bold(True)
                self.p.size(2,1)
                self.p.wrapped_text(text.upper())
                self.p.hr()
            elif level == 3:
                self.p.bold(True)
                self.p.size(1,1)
                self.p.wrapped_text(text)
            else:
                # Levels 4–6
                self.p.bold(True)
                self.p.size(1,1)
                prefix = {4:"# ",5:"- ",6:"  "}.get(level, "")
                self.p.wrapped_text(f"{prefix}{text}")
            self.p.size(1,1)
            self.p.bold(False)
            self.p.set_align("left")
            self.p.newline()
        elif node_type == "FencedCode":
            self._flush()
            self.p.hr()
            code_text = _text(node)
            for line in code_text.splitlines():
                self.p.wrapped_text(line)
            self.p.hr()
        elif node_type == "ThematicBreak":
            self._flush()
            self.p.hr()
        elif node_type == "List":
            for item in getattr(node, "children", []):
                self._node(item)
        elif node_type == "ListItem":
            bullet = "• "
            indent = len(bullet)
            lines = []
            # Capture the text of children without printing
            for c in getattr(node, "children", []):
                lines.append(self._text(c))
            wrapped_lines = textwrap.wrap(" ".join(lines), width=PRINTER_CHAR_WIDTH - indent)
            for i, line in enumerate(wrapped_lines):
                if i == 0:
                    self.p.raw_line(bullet + line)
                else:
                    self.p.raw_line(" " * indent + line)
            self._flush()
            self.p.newline()
        elif node_type in ("Table", "TableBlock"):
            self._flush()
            # header
            header = []
            if hasattr(node, "header") and node.header:
                header_row = [_text(c) for c in getattr(node.header, "children", [])]
                header.append(header_row)
            # body
            body = []
            for row in getattr(node, "children", []):
                # skip header row if already included
                if getattr(row, "is_header", False):
                    continue
                body_row = [_text(c) for c in getattr(row, "children", [])]
                body.append(body_row)
            self._render_table(header, body)

    # --- Render AST ---
    def render(self, ast):
        if hasattr(ast, "children"):
            for node in ast.children:
                self._node(node)
        else:
            self._node(ast)
        self._flush()

    # --- Table rendering ---
    def _render_table(self, header, body):
        if not header and not body:
            return

        col_count = max(
            max(len(r) for r in header) if header else 0,
            max(len(r) for r in body) if body else 0
        )
        for r in header:
            while len(r) < col_count:
                r.append("")
        for r in body:
            while len(r) < col_count:
                r.append("")

        padding = 2
        col_width = (PRINTER_CHAR_WIDTH - (col_count - 1) * padding) // col_count

        col_info = analyze_decimal_columns(header + body, col_count)

        # Print header
        if header:
            wrapped_header = []
            max_lines = 0
            for col_idx in range(col_count):
                cell_text = header[0][col_idx] if col_idx < len(header[0]) else ""
                wrapped = textwrap.wrap(cell_text, width=col_width) or [""]
                wrapped_header.append(wrapped)
                max_lines = max(max_lines, len(wrapped))
            for i in range(max_lines):
                line = ""
                for col_idx, col_lines in enumerate(wrapped_header):
                    cell = col_lines[i] if i < len(col_lines) else ""
                    line += cell.ljust(col_width)
                    if col_idx < col_count - 1:
                        line += " " * padding
                self.p.raw_line_no_wrap(line)
            self.p.hr()

        # Print body
        for row in body:
            wrapped_cols = []
            max_lines = 0
            for col_idx, cell in enumerate(row):
                wrapped = textwrap.wrap(cell, width=col_width) or [""]
                wrapped_cols.append(wrapped)
                max_lines = max(max_lines, len(wrapped))
            for i in range(max_lines):
                line = ""
                for col_idx, col_lines in enumerate(wrapped_cols):
                    cell_text = col_lines[i] if i < len(col_lines) else ""
                    # alignment
                    align = "left"
                    if header:
                        # Try to use alignment from the first header cell
                        header_node = node.header.children[col_idx] if col_idx < len(node.header.children) else None
                        if header_node and getattr(header_node, "align", None):
                            align = header_node.align
                    if align == "right":
                        cell_text = cell_text.rjust(col_width)
                    else:
                        cell_text = cell_text.ljust(col_width)
                    line += cell_text
                    if col_idx < col_count - 1:
                        line += " " * padding
                self.p.raw_line_no_wrap(line)
        self.p.hr()


# ---------------------------
# Entry Point
# ---------------------------

def render_markdown(md_text, cut=False):
    printer = EscPosPrinter()
    renderer = AstPrinter(printer)

    md = Markdown(extensions=["gfm"])
    ast = md.parse(md_text)

    renderer.render(ast)

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
        with open(parsed.file,"r",encoding="utf-8") as f:
            md=f.read()
    else:
        md=sys.stdin.read()

    render_markdown(md, cut=parsed.cut)

if __name__=="__main__":
    main()