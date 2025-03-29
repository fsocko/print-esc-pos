import usb.core
import usb.util

def find_usb_printer():
    try:
        # Find all USB devices
        devices = usb.core.find(find_all=True)
        if not devices:
            print("No USB devices found.")
            return
        
        found_printer = False
        
        for device in devices:
            try:
                # Get vendor and product ID
                vendor_id = device.idVendor
                product_id = device.idProduct
                
                # Get device class (07h = printers, 03h = HID, etc.)
                device_class = device.bDeviceClass
                
                # Get bus and device address (port)
                bus_number = device.bus
                device_address = device.address
                
                # Check if it's likely a printer (class 07 or known vendor/product ID)
                if device_class == 7 or usb.util.get_string(device, 256, device.iProduct):
                    print(f"Printer found: Vendor ID = {hex(vendor_id)}, Product ID = {hex(product_id)}")
                    print(f"  Connected at Bus {bus_number}, Device {device_address}")
                    found_printer = True
            except usb.core.USBError as e:
                print(f"USB error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")
        
        if not found_printer:
            print("No USB printers found.")
    except usb.core.USBError as e:
        print(f"USB error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    find_usb_printer()
