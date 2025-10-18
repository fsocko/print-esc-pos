# printer/print_raw.py
import sys
import printer_utils

def print_raw(cut=False):
    printer = printer_utils.find_printer()
    printer_utils.initialize_printer(printer)
    data = sys.stdin.buffer.read()
    if data:
        printer._raw(data)
    if cut:
        printer.cut()
    printer.close()

def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(description="Send raw ESC/POS bytes to printer.")
    parser.add_argument("-c", "--cut", action="store_true")
    parsed = parser.parse_args(args)
    print_raw(parsed.cut)
