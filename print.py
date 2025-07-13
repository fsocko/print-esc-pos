# print.py — refactored to be the minimal core print handler and handle printer initialization

from PIL import Image
import textwrap
import sys
import printer_utils
import argparse
import warnings

PRINTER_CHAR_WIDTH = 48
PRINTER_WIDTH_PX = 640

def get_printer():
    printer = printer_utils.find_printer()
    printer_utils.initialize_printer(printer)
    return printer

def print_text(cut):
    try:
        printer = get_printer()
        text = sys.stdin.read().strip()
        if text:
            wrapped_text = textwrap.fill(text, width=PRINTER_CHAR_WIDTH)
            printer.text(wrapped_text + "\n")
        if cut:
            printer.cut()
        print("Text print successful.")
        printer.close()
    except Exception as e:
        print(f"Failed to print text: {e}")

def print_image(image_input, cut, scale_width_percentage=None, align_param="left"):
    try:
        printer = get_printer()
        if isinstance(image_input, str):
            img = Image.open(image_input)
        else:
            img = image_input

        orig_width, orig_height = img.size

        # If scale_width_percentage is not provided, check if image too wide and scale automatically
        if scale_width_percentage is None and orig_width > PRINTER_WIDTH_PX:
            warnings.warn(f"Image width {orig_width}px exceeds printer max width {PRINTER_WIDTH_PX}px. Auto-scaling to 100%.")
            scale_width_percentage = 100

        if scale_width_percentage:
            if scale_width_percentage <= 0 or scale_width_percentage > 100:
                raise ValueError("Scale percentage must be between 1 and 100.")

            target_width = int((scale_width_percentage / 100) * PRINTER_WIDTH_PX)
            target_height = int((target_width / orig_width) * orig_height)

            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

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



# Parameters for when called directly from command line
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print text, images, or raw ESC/POS data to a USB POS printer.")
    
    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing.")
    parser.add_argument("-r", "--raw", action="store_true", help="Read raw bytes from stdin and send to printer.")
    parser.add_argument("-i", "--image", type=str, help="Path to the image file. If omitted, reads text from stdin.")
    parser.add_argument("-w", "--scale-width", type=int, help="Percentage of the printer's width to scale the image to (1-100).")
    parser.add_argument("-x", "--align", type=str, choices=["left", "center", "right", "l", "c", "r"], default="left", help="Horizontal alignment: left (l), center (c), right (r).")
    
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
        print_image(args.image, args.cut, args.scale_width, args.align)
    elif not sys.stdin.isatty():
        print_text(args.cut)
    elif args.cut:
        cut_paper()
        print("Forced paper cut.")
