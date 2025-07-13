from escpos.printer import Usb

# Initialize the printer (replace with your printer's vendor and product IDs)
PRINTER_VENDOR_ID = 0x0416  # Replace with your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Replace with your printer's product ID

try:
    p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)


     # Initialize printer
    p._raw(b'\x1B\x40')  # ESC @

    # Horizontal tab
    p._raw(b'\x09')
    p.text("Column1\tColumn2\n")

    # Line feed
    p._raw(b'\x0A')

    # Set right-side character spacing
    p._raw(b'\x1B\x20\x05')

    # Print modes
    p._raw(b'\x1B\x21\x20')  # Double-width
    p.text("Double Width\n")
    p._raw(b'\x1B\x21\x10')  # Double-height
    p.text("Double Height\n")
    p._raw(b'\x1B\x21\x00')  # Reset

    # Absolute positioning
    p._raw(b'\x1B\x24\x30\x00')
    p.text("Positioned\n")

    # Bit image (8-dot, simple demo)
    p._raw(b'\x1B\x2A\x00\x02\x00' + b'\xFF\xFF')

    # Underline
    p._raw(b'\x1B\x2D\x01')
    p.text("Underlined\n")
    p._raw(b'\x1B\x2D\x00')

    # Line spacing
    p._raw(b'\x1B\x33\x20')  # Custom
    p._raw(b'\x1B\x32')      # Default

    # Cancel user-defined character
    p._raw(b'\x1B\x3F\x41')  # ESC ? A

    # Emphasized
    p._raw(b'\x1B\x45\x01')
    p.text("Emphasized\n")
    p._raw(b'\x1B\x45\x00')

    # Double-strike
    p._raw(b'\x1B\x47\x01')
    p.text("Double-strike\n")
    p._raw(b'\x1B\x47\x00')

    # Feed paper
    p._raw(b'\x1B\x4A\x10')

    # Font selection
    p._raw(b'\x1B\x4D\x00')  # Font A
    p._raw(b'\x1B\x4D\x01')  # Font B

    # Rotation
    p._raw(b'\x1B\x56\x01')
    p.text("Rotated\n")
    p._raw(b'\x1B\x56\x00')

    # Relative position
    p._raw(b'\x1B\x5C\x20\x00')  # +32

    # Alignment
    p._raw(b'\x1B\x61\x00')
    p.text("Left\n")
    p._raw(b'\x1B\x61\x01')
    p.text("Center\n")
    p._raw(b'\x1B\x61\x02')
    p.text("Right\n")

    # Feed lines
    p._raw(b'\x1B\x64\x03')

    # Cash drawer
    p._raw(b'\x1B\x70\x00\x32\x32')

    # Code page
    p._raw(b'\x1B\x74\x00')

    # Upside-down
    p._raw(b'\x1B\x7B\x01')
    p.text("Upside Down\n")
    p._raw(b'\x1B\x7B\x00')

    # Full and partial cuts
    p._raw(b'\x1D\x56\x00')  # Full
    p._raw(b'\x1D\x56\x01')  # Partial

    # Character size
    p._raw(b'\x1D\x21\x11')  # 2x2
    p.text("Big Text\n")
    p._raw(b'\x1D\x21\x00')  # Reset

    # Reverse printing
    p._raw(b'\x1D\x42\x01')
    p.text("Reverse\n")
    p._raw(b'\x1D\x42\x00')

    # HRI barcode options
    p._raw(b'\x1D\x66\x00')  # Font A
    p._raw(b'\x1D\x48\x02')  # Below

    # Barcode height and width
    p._raw(b'\x1D\x68\x40')
    p._raw(b'\x1D\x77\x03')

    # Print barcode (CODE39)
    p._raw(b'\x1D\x6B\x04')
    p._raw(b'12345\x00')

    # Raster bitmap (dummy)
    p._raw(b'\x1D\x76\x30\x00\x01\x00\x01\x00\xFF')

    # Left margin
    p._raw(b'\x1D\x4C\x10\x00')

    # Done
    p.text("Demo complete\n")
    p.cut()

except Exception as e:
    print(f"An error occurred: {e}")