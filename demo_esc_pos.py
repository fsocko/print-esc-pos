from escpos.printer import Usb

# Initialize the printer (replace with your printer's vendor and product IDs)
PRINTER_VENDOR_ID = 0x0416  # Replace with your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Replace with your printer's product ID

try:
    p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)


      # --- Text formatting ---
    p.set(font='a', align='left', bold=False, underline=0, width=1, height=1)
    p.text("Normal Text\n")

    # Bold
    p.set(bold=True)
    p.text("Bold Text\n")

    # Underline (1-dot and 2-dot)
    p.set(underline=1)
    p.text("Underline 1-dot\n")
    p.set(underline=2)
    p.text("Underline 2-dot\n")
    p.set(underline=0)

    # Font B
    p.set(font='b')
    p.text("Font B Text\n")

    # Double width & height
    p.set(width=2, height=2)
    p.text("Double Width & Height\n")

    # Reset
    p.set()

    # Alignment
    p.set(align='left')
    p.text("Left Aligned\n")
    p.set(align='center')
    p.text("Center Aligned\n")
    p.set(align='right')
    p.text("Right Aligned\n")

    # Line feed
    p.text("Line feed test\n\n\n")

    # --- Barcodes ---
    p.set(align='center')
    p.barcode('123456789012', 'EAN13', width=2, height=100, pos='below', font='a')
    p.barcode('12345', 'CODE39', width=2, height=80, pos='above', font='b')

    # --- QR Code ---
    p.qr("https://example.com", size=6, center=True)

    # --- Cut Paper ---
    p.cut(mode='PART')   # Partial cut
    p.cut(mode='FULL')   # Full cut

    # --- Cash drawer pulse ---
    p.cashdraw(2)  # Pin 2 pulse

except Exception as e:
    print(f"An error occurred: {e}")