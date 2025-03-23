import usb.core
import usb.util
import usb.backend.libusb1
from escpos.printer import Usb
from PIL import Image
import sys
import argparse

def find_printer():
    backend = usb.backend.libusb1.get_backend()
    devices = usb.core.find(find_all=True, backend=backend)
    if not devices:
        print("No USB devices found.")
        return None
    
    for device in devices:
        try:
            vendor_id = device.idVendor
            product_id = device.idProduct
            device_class = device.bDeviceClass
            
            if device_class == 7 or usb.util.get_string(device, 256, device.iProduct):
                print(f"Printer found: Vendor ID = {hex(vendor_id)}, Product ID = {hex(product_id)}")
                return Usb(vendor_id, product_id, backend=backend)
        except usb.core.USBError as e:
            print(f"USB error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    print("No USB printers found.")
    return None

def print_text(printer, cut):
    try:
        text = sys.stdin.read().strip()
        if text:
            printer.text(text + "\n")
        if cut:
            printer.cut()
        print("Text print successful.")
    except Exception as e:
        print(f"Failed to print text: {e}")

def print_image(printer, image_path, cut, scale_width, scale_height):
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Use user-defined scaling if provided, else use the default max width
        img_width, img_height = img.size
        new_width = scale_width if scale_width else 384  # Default to 384px width
        new_height = scale_height if scale_height else int(img_height * (new_width / img_width))

        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        printer.image(img)
        
        # Perform a cut if requested
        if cut:
            printer.cut()
        
        print("Image print successful.")
    except Exception as e:
        print(f"Failed to print image: {e}")

def print_raw(printer, cut):
    try:
        raw_data = sys.stdin.buffer.read()  # Read raw bytes from stdin
        if raw_data:
            printer._raw(raw_data)  # Send raw bytes to the printer
        print("Raw data sent successfully.")
        
        if cut:
            printer.cut()
            
    except Exception as e:
        print(f"Failed to send raw data: {e}")

def cut_paper(printer):
    printer.cut()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print text, images, or raw ESC/POS data to a USB POS printer.")
    
    parser.add_argument("-c", "--cut", action="store_true", help="Cut paper after printing.")
    parser.add_argument("-r", "--raw", action="store_true", help="Read raw bytes from stdin and send to printer. Example: cat raw_escpos.bin | python print.py -r")
    
    parser.add_argument("-i", "--image", type=str, help="Path to the image file. If omitted, reads text from stdin.")
    parser.add_argument("--scale-width", type=int, help="Specify width for image scaling.")
    parser.add_argument("--scale-height", type=int, help="Specify height for image scaling.")
    
    args = parser.parse_args()
    
    printer = find_printer()
    if printer:
        if args.raw:
            print_raw(printer, args.cut)

        elif args.image:
            print_image(printer, args.image, args.cut, args.scale_width, args.scale_height)

        elif not sys.stdin.isatty():
            print_text(printer, args.cut)

        elif args.cut:
            cut_paper(printer)
            print("Forced paper cut.")