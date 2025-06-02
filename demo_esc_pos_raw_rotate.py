from escpos.printer import Usb

# Initialize the printer (replace with your printer's vendor and product IDs)
PRINTER_VENDOR_ID = 0x0416  # Replace with your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Replace with your printer's product ID

try:
    p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)


     # Initialize printer
    p._raw(b'\x1B\x40')  # ESC @

    
    # Set left alignment
    p._raw(bytes([0x1B, 0x61, 0x00]))

    # Optional: select font A (standard width)
    p._raw(bytes([0x1B, 0x4D, 0x00]))  # ESC M 0 = Font A

    # Rotation
    p._raw(b'\x1B\x56\x01')
    # Print table header
    p.text(f"{'Name':<10}{'Qty':>5}{'Price':>8}\n")

    # Print table rows
    p.text(f"{'Apple':<10}{2:>5}{'€0.50':>8}\n")
    p.text(f"{'Banana':<10}{1:>5}{'€0.30':>8}\n")
    p.text(f"{'Orange':<10}{3:>5}{'€1.00':>8}\n")
    p._raw(b'\x1B\x56\x00')
    p.text("\n")    

    p.cut()

except Exception as e:
    print(f"An error occurred: {e}")