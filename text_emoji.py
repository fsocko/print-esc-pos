#!/usr/bin/env python3
# text_emoji.py — hybrid text + emoji printing

import sys
import os
import re
import textwrap
import printer_utils
from PIL import Image, ImageDraw, ImageFont
import argparse

# ESC/POS settings
PRINTER_CHAR_WIDTH = 48   # columns per line
CHAR_PIXELS = 8           # pixels per character
EMOJI_COLUMNS = 4         # width in columns for emojis

# ESC/POS code pages
CODEPAGE_CANDIDATES = [
    (16, "cp1252", "Western Europe + €"),
    (2, "cp850", "Western Europe"),
    (18, "cp852", "Polish / Central Europe"),
    (5, "cp865", "Nordic"),
    (17, "cp866", "Cyrillic / Russian"),
    (0, "cp437", "Box-drawing / Graphics"),
]

# Emoji detection regex
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "]", flags=re.UNICODE
)

def get_printer(stream_mode=False):
    printer = printer_utils.find_printer(verbose=not stream_mode)
    printer_utils.initialize_printer(printer, verbose=not stream_mode)
    return printer

def find_compatible_codepage(text):
    for n, codec, desc in CODEPAGE_CANDIDATES:
        try:
            text.encode(codec)
            return n, codec, desc
        except UnicodeEncodeError:
            continue
    return None, None, None

def split_text_and_emoji(line):
    result = []
    idx = 0
    for match in EMOJI_PATTERN.finditer(line):
        start, end = match.span()
        if start > idx:
            result.append(("text", line[idx:start]))
        result.append(("emoji", line[start:end]))
        idx = end
    if idx < len(line):
        result.append(("text", line[idx:]))
    return result

def render_emoji_image(echar, text_width_cols=EMOJI_COLUMNS, padding=2):
    pixel_width = text_width_cols * CHAR_PIXELS
    img = Image.new("RGB", (pixel_width, pixel_width), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("seguiemj.ttf", pixel_width)
    except OSError:
        font = ImageFont.load_default()

    baseline_offset = 2
    draw.text((0, baseline_offset), echar, font=font, fill="black")

    bbox = img.getbbox()
    if bbox:
        left, upper, right, lower = bbox
        left = max(0, left - padding)
        upper = max(0, upper - padding)
        right = min(img.width, right + padding)
        lower = min(img.height, lower + padding)
        img = img.crop((left, upper, right, lower))

    img = img.resize((pixel_width, pixel_width), Image.Resampling.LANCZOS)
    return img

def print_text_hybrid(lines, cut=False):
    printer = get_printer()
    MAX_PIXEL_WIDTH = PRINTER_CHAR_WIDTH * CHAR_PIXELS

    for line in lines:
        line = line.rstrip("\n")
        segments = split_text_and_emoji(line)

        for kind, content in segments:
            if kind == "text" and content:
                wrapped = textwrap.wrap(content, width=PRINTER_CHAR_WIDTH) \
                         if len(content) > PRINTER_CHAR_WIDTH else [content]
                for wl in wrapped:
                    n, codec, desc = find_compatible_codepage(wl)
                    if n is None:
                        encoded = wl.encode("ascii", errors="replace")
                        printer.text(encoded.decode("ascii") + "\n")
                    else:
                        printer._raw(b"\x1B\x74" + bytes([n]))
                        printer._raw(wl.encode(codec) + b"\n")
            elif kind == "emoji":
                img = render_emoji_image(content)
                if img.width > MAX_PIXEL_WIDTH:
                    img = img.resize((MAX_PIXEL_WIDTH, img.height), Image.Resampling.LANCZOS)
                printer.image(img)

    if cut:
        printer.cut()
    printer.close()

def main():
    parser = argparse.ArgumentParser(description="Hybrid ESC/POS print: text + emojis as images")
    parser.add_argument("file", nargs="?", help="Text file to print (UTF-8), defaults to stdin")
    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing")
    args = parser.parse_args()

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.read().splitlines()

    print_text_hybrid(lines, cut=args.cut)

if __name__ == "__main__":
    main()
