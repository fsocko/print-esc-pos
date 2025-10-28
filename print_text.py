# printer/print_text.py
import sys
import textwrap
import time
import printer_utils
from itertools import cycle

PRINTER_CHAR_WIDTH = 48
FLUSH_LINES = 20
FLUSH_INTERVAL = 4

spinner_cycle = cycle(['|', '/', '-', '\\'])

def spinner_print():
    sys.stdout.write(next(spinner_cycle))
    sys.stdout.flush()
    sys.stdout.write('\b')

def get_printer(stream_mode=False):
    printer = printer_utils.find_printer(verbose=not stream_mode)
    printer_utils.initialize_printer(printer, verbose=not stream_mode)
    return printer

def print_buffer(printer, lines):
    for line in lines:
        wrapped_lines = textwrap.wrap(line.strip(), width=PRINTER_CHAR_WIDTH)
        for wrapped in wrapped_lines:
            printer.text(wrapped + "\n")

def print_text_simple(cut=False):
    printer = get_printer()
    for line in sys.stdin:
        if len(line.rstrip()) > PRINTER_CHAR_WIDTH:
            wrapped_lines = textwrap.wrap(line.rstrip(), width=PRINTER_CHAR_WIDTH)
            for wl in wrapped_lines:
                printer.text(wl + "\n")
        else:
            printer.text(line.rstrip() + "\n")
    if cut:
        printer.cut()
    printer.close()

def print_text_buffered(cut=False):
    printer_container = [get_printer(stream_mode=True)]
    buffer, last_flush = [], time.time()

    def flush():
        nonlocal buffer, last_flush
        if buffer:
            print_buffer(printer_container[0], buffer)
            buffer.clear()
            last_flush = time.time()
            printer_container[0].close()
            printer_container[0] = get_printer(stream_mode=True)
            spinner_print()

    try:
        for line in sys.stdin:
            if line.strip():
                buffer.append(line)
            now = time.time()
            if len(buffer) >= FLUSH_LINES or (now - last_flush) >= FLUSH_INTERVAL:
                flush()
    except KeyboardInterrupt:
        flush()
        if cut:
            printer_container[0].cut()
        printer_container[0].close()
        sys.exit(0)

    flush()
    if cut:
        printer_container[0].cut()
    printer_container[0].close()

def main(args=None):
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Print text to ESC/POS printer.")
    parser.add_argument("file", nargs="?", help="File to print (defaults to stdin)")
    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing")
    parser.add_argument("-s", "--stream", action="store_true", help="Enable streaming mode")
    parsed = parser.parse_args(args)

    # Read from file if provided, otherwise stdin
    if parsed.file:
        if not os.path.exists(parsed.file):
            print(f"Error: file not found: {parsed.file}", file=sys.stderr)
            sys.exit(1)
        with open(parsed.file, "r", encoding="utf-8", errors="replace") as f:
            sys.stdin = f  # redirect file to stdin
            if parsed.stream:
                print_text_buffered(parsed.cut)
            else:
                print_text_simple(parsed.cut)
    else:
        # No file → read from stdin directly
        if parsed.stream:
            print_text_buffered(parsed.cut)
        else:
            print_text_simple(parsed.cut)
