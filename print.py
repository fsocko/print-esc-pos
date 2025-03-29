import usb.core
import usb.util
import usb.backend.libusb1
from escpos.printer import Usb
from PIL import Image
import sys
import argparse

import usb.core
import usb.util
import usb.backend.libusb1
from escpos.printer import Usb


PRINTER_VENDOR_ID = 0x0416
PRINTER_PRODUCT_ID = 0x5011
PRINTER_WIDTH_PX = 384

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

            # Only proceed if this is the correct printer
            if vendor_id == PRINTER_VENDOR_ID and product_id == PRINTER_PRODUCT_ID:
                bus_number = device.bus
                device_address = device.address

                print(f"Printer found: Vendor ID = {hex(vendor_id)}, Product ID = {hex(product_id)}")
                #print(f"   Connected at Bus {bus_number}, Device {device_address}")

                device.set_configuration()

                # Look for the correct interface and OUT endpoint
                for cfg in device:
                    for intf in cfg:
                        try:
                            usb.util.claim_interface(device, intf.bInterfaceNumber)

                            endpoint = usb.util.find_descriptor(
                                intf,
                                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
                            )

                            if endpoint:
                            #    print(f" Using OUT endpoint: {hex(endpoint.bEndpointAddress)}")
                                return Usb(vendor_id, product_id, intf.bInterfaceNumber, 0, backend=backend)
                            
                            print(f"Warning: No OUT endpoint found in interface {intf.bInterfaceNumber}. Trying next interface...")

                        except usb.core.USBError as e:
                            print(f"Error: Could not claim interface {intf.bInterfaceNumber}: {e}")

                print("Error: No valid OUT endpoint found!")
                return None

        except usb.core.USBError as e:
            print(f"USB error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    print("Error: No USB printers found.")
    return None



def print_text(printer, cut):
    """Prints text from stdin."""
    try:
        text = sys.stdin.read().strip()
        if text:
            printer.text(text + "\n")
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
            
            # Calculate the target width based on the percentage
            target_width = int((scale_width_percentage / 100) * PRINTER_WIDTH_PX)
            img_width, img_height = img.size

            # Calculate the target height to maintain the aspect ratio
            target_height = int(img_height * (target_width / img_width))

            # Resize the image
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
        
    printer = find_printer()
    
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