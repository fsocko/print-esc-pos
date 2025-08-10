from PIL import Image
import textwrap
import sys
import printer_utils
import argparse
import warnings
import time
import threading
import select
import os
import itertools
import sys

spinner_cycle = itertools.cycle(['|', '/', '-', '\\'])

PRINTER_CHAR_WIDTH = 48
PRINTER_WIDTH_PX = 640
PRINTER_DPI = 203  # Usually 203 DPI = 8 dots/mm

# Correction multipliers for fine-tuning physical accuracy
HORIZONTAL_SCALE_CORRECTION = 1.00
VERTICAL_SCALE_CORRECTION   = 1.012  # increase height ~2% to match ruler due to calibration experiments

def spinner_print():
    sys.stdout.write(next(spinner_cycle))   # print next spinner char
    sys.stdout.flush()
    sys.stdout.write('\b')                   # backspace to overwrite on next print


def mm_to_pixels(mm, dpi=PRINTER_DPI, axis="x"):
    correction = HORIZONTAL_SCALE_CORRECTION if axis == "x" else VERTICAL_SCALE_CORRECTION
    return int((mm / 25.4) * dpi * correction)

def get_printer(stream_mode=False):
    printer = printer_utils.find_printer(verbose=not stream_mode)
    printer_utils.initialize_printer(printer, verbose=not stream_mode)
    return printer

def print_text(cut, stream_mode=False):
    if stream_mode:
        print_text_buffered(cut)
    else:
        print_text_simple(cut)
FLUSH_LINES = 20        # flush after this many lines
FLUSH_INTERVAL = 4      # flush at least every T seconds

def print_text_simple(cut):
    try:
        printer = get_printer()
        text = sys.stdin.read().strip()
        if text:
            wrapped_text = textwrap.fill(text, width=PRINTER_CHAR_WIDTH)
            printer.text(wrapped_text + "\n")
        if cut:
            printer.cut()
        printer.close()
        print("Text print successful (simple mode).")
    except Exception as e:
        print(f"Failed to print text: {e}")

def print_buffer(printer, lines):
    if not lines:
        return
    for line in lines:
        clean_line = line.rstrip("\n")
        wrapped_lines = textwrap.wrap(clean_line, width=PRINTER_CHAR_WIDTH)
        for wrapped_line in wrapped_lines:
            printer.text(wrapped_line + "\n")

def print_text_buffered(cut):
    try:
        printer_container = [get_printer(stream_mode=True)]
        buffer = []
        last_flush_time = time.time()

        def flush_buffer():
            nonlocal buffer, last_flush_time, printer_container
            if buffer:
                print_buffer(printer_container[0], buffer)
                buffer.clear()
                last_flush_time = time.time()
                printer_container[0].close()
                printer_container = [get_printer(stream_mode=True)]
                spinner_print()

        try:
            for line in sys.stdin:
                if line.strip() != "":
                    buffer.append(line)

                now = time.time()
                if len(buffer) >= FLUSH_LINES or (now - last_flush_time) >= FLUSH_INTERVAL:
                    flush_buffer()

        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Flushing buffer.")
            flush_buffer()
            if cut:
                printer_container[0].cut()
            printer_container[0].close()
            sys.exit(0)

        # Normal end of input
        flush_buffer()
        if cut:
            printer_container[0].cut()
        printer_container[0].close()
        print("Text print successful (stream mode).")

    except Exception as e:
        print(f"Failed to print text: {e}")



def print_image(image_input, cut, scale_width_percentage=None, align_param="left", target_width_mm=None, target_height_mm=None):
    try:
        printer = get_printer()
        img = Image.open(image_input) if isinstance(image_input, str) else image_input
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width

        # Resize using physical dimensions if any are provided
        if target_width_mm or target_height_mm:
            if target_width_mm and not target_height_mm:
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = int(target_width_px * aspect_ratio)
            elif target_height_mm and not target_width_mm:
                target_height_px = mm_to_pixels(target_height_mm, axis="y")
                target_width_px = int(target_height_px / aspect_ratio)
            else:
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = mm_to_pixels(target_height_mm, axis="y")

            img = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)

        # Fallback: percentage scale
        elif scale_width_percentage:
            if scale_width_percentage <= 0 or scale_width_percentage > 100:
                raise ValueError("Scale percentage must be between 1 and 100.")
            target_width = int((scale_width_percentage / 100) * PRINTER_WIDTH_PX)
            target_height = int(target_width * aspect_ratio)
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Fallback: auto-scale if too wide
        elif orig_width > PRINTER_WIDTH_PX:
            warnings.warn(f"Image width {orig_width}px exceeds printer max width {PRINTER_WIDTH_PX}px. Auto-scaling to 100%.")
            img = img.resize((PRINTER_WIDTH_PX, int(PRINTER_WIDTH_PX * aspect_ratio)), Image.Resampling.LANCZOS)

        printer.set(align=align_param)
        printer.image(img)

        if cut:
            printer.cut()

        print("Image print successful.")
        printer.close()
    except Exception as e:
        print(f"Failed to print image: {e}")


def print_raw(cut):
    try:
        printer = get_printer()
        raw_data = sys.stdin.buffer.read()
        if raw_data:
            printer._raw(raw_data)
        if cut:
            printer.cut()
        print("Raw data sent successfully.")
        printer.close()
    except Exception as e:
        print(f"Failed to send raw data: {e}")

def cut_paper():
    try:
        printer = get_printer()
        printer.cut()
        printer.close()
    except Exception as e:
        print(f"Failed to cut paper: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print text, images, or raw ESC/POS data to a USB POS printer.")

    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing.")
    parser.add_argument("-r", "--raw", action="store_true", help="Read raw bytes from stdin and send to printer.")
    parser.add_argument("-i", "--image", type=str, help="Path to the image file. If omitted, reads text from stdin.")
    parser.add_argument("-w", "--scale-width", type=int, help="Percentage of the printer's width to scale the image to (1-100).")
    parser.add_argument("--width-mm", type=float, help="Target physical width of the image in millimeters (overrides scale-width).")
    parser.add_argument("--height-mm", type=float, help="Target physical height of the image in millimeters.")
    parser.add_argument("-x", "--align", type=str, choices=["left", "center", "right", "l", "c", "r"], default="left", help="Horizontal alignment: left (l), center (c), right (r).")
    parser.add_argument("-s", "--stream", action="store_true", help="Use continuous stream buffered printing (flush every N lines or T seconds).")

    args = parser.parse_args()

    # Normalize shorthand alignment options
    if args.align == "l":
        args.align = "left"
    elif args.align == "c":
        args.align = "center"
    elif args.align == "r":
        args.align = "right"

    if args.raw:
        print_raw(args.cut)
    elif args.image:
        print_image(
            args.image,
            args.cut,
            scale_width_percentage=args.scale_width,
            align_param=args.align,
            target_width_mm=args.width_mm,
            target_height_mm=args.height_mm
        )
    elif not sys.stdin.isatty():
        print_text(args.cut, stream_mode=args.stream)
    elif args.cut:
        cut_paper()
        print("Forced paper cut.")