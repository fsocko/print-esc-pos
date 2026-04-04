import sys
import textwrap
import printer_utils
import ftfy
import re

from marko import Markdown
from marko.ext.gfm import GFM

PRINTER_CHAR_WIDTH = printer_utils.PRINTER_CHAR_WIDTH
DEBUG_AST = False

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
            cell_node = row[col]
            text = getattr(cell_node, "children", str(cell_node))
            if isinstance(text, list):
                text = "".join(str(c.children) if hasattr(c, "children") else str(c) for c in text)
            cell = text.strip()
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
            break_long_words=False,
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

    def size(self, w=1, h=1):
        self.printer.set(width=w, height=h)

    def hr(self):
        self.raw_line("-" * PRINTER_CHAR_WIDTH)

    def qr(self, text):
        # Stub: implement printer-specific QR code
        self.set_align("center")
        self.printer.qr(text, size=8)
        self.newline()
        self.set_align("left")
        
    def draw_table_border(self, col_widths):
        self.p.write("+")
        for w in col_widths:
            self.p.write("-" * (w + 2))
            self.p.write("+")
        self.p.newline()

    def barcode(self, code, code_type="EAN13"):
        # Stub: implement printer-specific barcode
        self.set_align("center")
        self.printer.barcode(code, code_type, width=2, height=100, pos='below', font='a')
        self.newline()
        self.set_align("left")

    def cut(self):
        self.printer.cut()

    def close(self):
        self.printer.close()

# ---------------------------
# AST Renderer (Marko)
# ---------------------------

class AstPrinter:
    def __init__(self, printer):
        self.p = printer
        self.bold = False
        self.italic = False

    # ---------------------------
    # Streaming text writer
    # ---------------------------

    def _write_text(self, text):
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

    # ---------------------------
    # Plain text extractor
    # ---------------------------

    def _capture_text(self, node):
        parts = []

        def walk(n):
            t = n.__class__.__name__
            if t == "RawText":
                parts.append(n.children)
            else:
                for c in getattr(n, "children", []):
                    walk(c)

        walk(node)
        return "".join(parts).strip()

    # ---------------------------
    # Segment extractor for inline formatting
    # ---------------------------

    def _collect_segments(self, node, bold=False, italic=False):
        segments = []

        def walk(n, b, i):
            t = n.__class__.__name__

            if t == "RawText":
                segments.append((n.children, b, i))

            elif t == "Strong":
                for c in n.children:
                    walk(c, True, i)

            elif t == "Emphasis":
                for c in n.children:
                    walk(c, b, True)

            elif t == "CodeSpan":
                segments.append((f"[{n.children}]", b, i))

            elif t == "Link":
                text = self._capture_text(n)
                segments.append((f"{text} ({n.dest})", b, i))

            elif hasattr(n, "children"):
                for c in n.children:
                    walk(c, b, i)

        walk(node, bold, italic)
        return segments

    # ---------------------------
    # Wrap segments
    # ---------------------------

    def _wrap_segments(self, segments, width):
        lines = []
        current = []
        length = 0

        for text, b, i in segments:
            words = text.split(" ")

            for w_idx, word in enumerate(words):
                part = word
                if w_idx < len(words) - 1:
                    part += " "

                if length + len(part) > width and current:
                    lines.append(current)
                    current = []
                    length = 0

                current.append((part, b, i))
                length += len(part)

        if current:
            lines.append(current)

        return lines or [[]]

    # ---------------------------
    # Render a segment line with alignment
    # ---------------------------

    def _render_segment_line(self, segments, width, align):
        text_len = sum(len(t) for t, _, _ in segments)
        text_len = min(text_len, width)

        if align == "right":
            pad_left = width - text_len
            pad_right = 0
        elif align == "center":
            pad_left = (width - text_len) // 2
            pad_right = width - text_len - pad_left
        else:
            pad_left = 0
            pad_right = width - text_len

        line = []

        if pad_left > 0:
            line.append((" " * pad_left, False, False))

        line.extend(segments)

        if pad_right > 0:
            line.append((" " * pad_right, False, False))

        for txt, b, i in line:
            self.p.set_style(b, i)
            self.p.write(txt)

    # ---------------------------
    # Node traversal
    # ---------------------------

    def _node(self, node):
        t = node.__class__.__name__

        # --- Inline ---
        if t == "RawText":
            self._write_text(node.children)

        elif t == "CodeSpan":
            self._write_text(f"[{node.children}]")

        elif t == "LineBreak":
            self.p.newline()

        elif t == "Strong":
            prev = self.bold
            self.bold = True
            for c in node.children:
                self._node(c)
            self.bold = prev

        elif t == "Emphasis":
            prev = self.italic
            self.italic = True
            for c in node.children:
                self._node(c)
            self.italic = prev

        # --- Blocks ---
        elif t == "Paragraph":
            for c in node.children:
                self._node(c)
            self.p.newline()

        elif t == "Heading":
            level = node.level
            text = self._capture_text(node)

            if level == 1:
                self.p.hr()
                self.p.set_align("center")
                self.p.bold(True)
                self.p.size(2, 2)
                self.p.wrapped_text(text.upper())
                self.p.hr()

            elif level == 2:
                self.p.newline(2)
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

            self.p.size(1, 1)
            self.p.bold(False)
            self.p.set_align("left")
            self.p.newline()

        elif t == "FencedCode":
            self.p.hr()

            content = node.children
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts = []
                for c in content:
                    if hasattr(c, "children"):
                        parts.append(str(c.children))
                    else:
                        parts.append(str(c))
                text = "".join(parts)
            else:
                text = str(content)

            for line in text.splitlines():
                self.p.wrapped_text(line)

            self.p.hr()

        elif t == "ThematicBreak":
            self.p.hr()

        elif t == "List":
            for item in node.children:
                self._node(item)

        elif t == "Link":
            text = self._capture_text(node)
            url = node.dest
            self._write_text(f"{text} ({url})")

        elif t == "AutoLink":
            self._write_text(node.dest)

        elif t == "ListItem":
            bullet = "• "
            indent = len(bullet)

            segments = self._collect_segments(node)
            wrapped = self._wrap_segments(segments, PRINTER_CHAR_WIDTH - indent)

            for i, line in enumerate(wrapped):
                prefix = bullet if i == 0 else " " * indent
                self.p.write(prefix)
                self._render_segment_line(line, PRINTER_CHAR_WIDTH - indent, "left")
                self.p.newline()

            self.p.newline()

        elif t in ("Table", "TableBlock"):
            self._render_marko_table(node, borders=True)

        elif hasattr(node, "children"):
            for c in node.children:
                self._node(c)

    # ---------------------------
    # Table rendering
    # ---------------------------

    def _log_table(self, col_widths, alignments):
        print("TABLE DEBUG")
        print("Widths:", col_widths)
        print("Align :", alignments)
    
    def _render_marko_table(self, node, borders=True, truncate_fallback=True):
        header = []
        body = []
        alignments = getattr(node, "align", None)

        # Extract rows
        if hasattr(node, "header") and node.header:
            header.append([c for c in node.header.children])

        for row in getattr(node, "children", []):
            if getattr(row, "is_header", False):
                continue
            body.append([c for c in row.children])

        if not header and not body:
            return

        col_count = max(
            max(len(r) for r in header) if header else 0,
            max(len(r) for r in body) if body else 0
        )

        # Normalize alignments
        norm_align = []
        for i in range(col_count):
            if alignments and i < len(alignments):
                a = alignments[i]
                norm_align.append(a if a in ("left", "center", "right") else None)
            else:
                norm_align.append(None)

        # Compute column widths
        col_widths = []
        for col in range(col_count):
            max_len = 0
            for row in header + body:
                if col >= len(row):
                    continue
                segs = self._collect_segments(row[col])
                text = "".join(t for t, _, _ in segs)
                max_len = max(max_len, len(text))
            col_widths.append(min(max_len, 30))  # cap width

        # Overflow handling
        total_width = sum(col_widths) + (col_count - 1)  # only separators count

        if total_width > PRINTER_CHAR_WIDTH:
            if truncate_fallback:
                self.p.bold(True)
                self.p.wrapped_text("TABLE TRUNCATED")
                self.p.bold(False)

                scale = (PRINTER_CHAR_WIDTH - (col_count - 1)) / sum(col_widths)
                col_widths = [max(5, int(w * scale)) for w in col_widths]
            else:
                return

        # Border drawing
        def draw_border():
            if not borders:
                return
            for i, w in enumerate(col_widths):
                self.p.write("-" * w)
                if i < len(col_widths) - 1:
                    self.p.write("+")
            self.p.newline()

        # Render table
        draw_border()
        if header:
            self._render_row(header[0], col_widths, norm_align, borders)
            draw_border()

        for row in body:
            self._render_row(row, col_widths, norm_align, borders)

        draw_border()

        if DEBUG_AST:
            self._log_table(col_widths, norm_align)



    def _render_row(self, row_nodes, col_widths, alignments, borders):
        col_count = len(col_widths)

        wrapped_cols = []
        max_lines = 0

        # Wrap all columns
        for col_idx in range(col_count):
            if col_idx < len(row_nodes):
                segments = self._collect_segments(row_nodes[col_idx])
            else:
                segments = []

            wrapped = self._wrap_segments(segments, col_widths[col_idx])
            wrapped_cols.append(wrapped)
            max_lines = max(max_lines, len(wrapped))

        # Normalize height
        for col_idx in range(col_count):
            while len(wrapped_cols[col_idx]) < max_lines:
                wrapped_cols[col_idx].append([])

        # Render lines
        for line_idx in range(max_lines):
            for col_idx in range(col_count):
                segs = wrapped_cols[col_idx][line_idx]
                width = col_widths[col_idx]

                align_mode = alignments[col_idx]

                # Auto-align numbers ONLY if no explicit alignment
                cell_text = "".join(t for t, _, _ in segs).strip()
                if align_mode is None:
                    align_mode = "right" if is_number(cell_text) else "left"

                # CONTENT (exact width, no extra padding)
                text = "".join(t for t, _, _ in segs)
                text = ftfy.fix_text(text)

                if len(text) > width:
                    text = text[:width]

                if align_mode == "right":
                    text = text.rjust(width)
                elif align_mode == "center":
                    text = text.center(width)
                else:
                    text = text.ljust(width)

                self.p.write(text)

                # Internal separator
                if col_idx < col_count - 1:
                    self.p.write("|")

            self.p.newline()

    # ---------------------------
    # Render entry
    # ---------------------------

    def render(self, ast):
        if DEBUG_AST:
            self._debug_node(ast)
        for node in ast.children:
            self._node(node)

    def _debug_node(self, node, depth=0):
        indent = "  " * depth
        print(f"{indent}{node.__class__.__name__}")
        for c in getattr(node, "children", []):
            if hasattr(c, "__class__"):
                self._debug_node(c, depth + 1)
            else:
                print(f"{indent}  {repr(c)}")

# ---------------------------
# Entry point
# ---------------------------

def render_markdown(md_text, cut=False):
    printer = EscPosPrinter()
    renderer = AstPrinter(printer)
    md = Markdown(extensions=[GFM])
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
        with open(parsed.file, "r", encoding="utf-8") as f:
            md = f.read()
    else:
        md = sys.stdin.read()

    render_markdown(md, cut=parsed.cut)

if __name__ == "__main__":
    main()