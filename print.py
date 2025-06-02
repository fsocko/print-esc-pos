from PIL import Image
import sys
import argparse
import printer_utils
import textwrap

PRINTER_CHAR_WIDTH  = 48
PRINTER_WIDTH_PX    = 640


def print_text(printer, cut):
    """Prints text from stdin with automatic line wrapping."""
    try:
        text = sys.stdin.read().strip()
        if text:
            wrapped_text = textwrap.fill(text, width=PRINTER_CHAR_WIDTH)
            printer.text(wrapped_text + "\n")
        if cut:
            printer.cut()
        print("Text print successful.")
    except Exception as e:
        print(f"Failed to print text: {e}")
        

def print_image(printer, image_path, cut, scale_width_percentage=None, align_param="left"):
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Scale the image if a percentage is provided
        if scale_width_percentage:
            if scale_width_percentage <= 0 or scale_width_percentage > 100:
                raise ValueError("Scale percentage must be between 1 and 100.")
            
            orig_width, orig_height = img.size
            target_width = int((scale_width_percentage / 100) * PRINTER_WIDTH_PX)
            target_height = int((target_width / orig_width) * orig_height)
            
            # Resize the image with aspect ratio preserved
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        printer.set(align=align_param)
        printer.image(img)
        
        # Perform a cut if requested
        if cut:
            printer.cut()

        print("Image print successful.")
    
    except Exception as e:
        print(f"Failed to print image: {e}")
        

def print_raw(printer, cut):
    """Sends raw ESC/POS data from stdin."""
    try:
        raw_data = sys.stdin.buffer.read()
        if raw_data:
            printer._raw(raw_data)
        if cut:
            printer.cut()
        print("Raw data sent successfully.")
    except Exception as e:
        print(f"Failed to send raw data: {e}")

def cut_paper(printer):
    """Cuts paper if printer supports it."""
    printer.cut()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print text, images, or raw ESC/POS data to a USB POS printer.")
    
    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing.")
    parser.add_argument("-r", "--raw", action="store_true", help="Read raw bytes from stdin and send to printer.")
    parser.add_argument("-i", "--image", type=str, help="Path to the image file. If omitted, reads text from stdin.")
    parser.add_argument("-w", "--scale-width", type=int, help="Percentage of the printer's width to scale the image to (1-100).")
    parser.add_argument( "-x", "--align", type=str, choices=["left", "center", "right", "l", "c", "r"], default="left", help="Horizontal alignment: left (l), center (c), right (r).")
    
    args = parser.parse_args()
    
    # Normalize shorthand alignment options
    if args.align == "l":
        args.align = "left"
    elif args.align == "c":
        args.align = "center"
    elif args.align == "r":
        args.align = "right"
        
    printer = printer_utils.find_printer()
    printer_utils.initialize_printer(printer)
    
    if printer:
        if args.raw:
            print_raw(printer, args.cut)
        elif args.image:
            print_image(printer, args.image, args.cut, args.scale_width, args.align)
        elif not sys.stdin.isatty():
            print_text(printer, args.cut)
        elif args.cut:
            cut_paper(printer)
            print("Forced paper cut.")

    printer.close()