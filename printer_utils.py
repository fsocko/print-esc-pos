import usb.backend.libusb1
from escpos.printer import Usb
import usb.core
import usb.util
import usb.backend.libusb1


#Printer backend, mainly used for finding the correct printer for other classes.

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