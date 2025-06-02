from escpos.printer import Usb
import time

PRINTER_VENDOR_ID = 0x0416  # Change to your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Change to your printer's product ID

try:
    p = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)

    # Initialize printer
    p._raw(b'\x1B\x40')  # ESC @

    # Print and line feed
    p._raw(b'\x0A')  # LF
    p.text("Line feed test\n")

    # Print and feed paper (feed 5 lines)
    p._raw(bytes([0x1B, 0x4A, 5]))  # ESC J 5
    p.text("Feed paper 5 lines\n")

    # Self test (usually prints test page)
    p._raw(b'\x1F\x00\x04')  # US VT EOT (might vary by model)
    time.sleep(1)

    # Beep command: beep 3 times, 5 time units each
    p._raw(bytes([0x1B, 0x42, 3, 5]))

    # Cut paper (partial cut)
    p._raw(bytes([0x1D, 0x56, 1]))  # GS V 1

    # Open cash drawer
    p._raw(bytes([0x1B, 0x70, 0, 25, 250]))  # ESC p m=0 t1=25 t2=250

    # Set absolute print position to 50
    p._raw(bytes([0x1B, 0x24, 50 & 0xFF, (50 >> 8) & 0xFF]))

    p.text("Absolute position at 50\n")

    # Set relative print position to 30
    p._raw(bytes([0x1B, 0x5C, 30 & 0xFF, (30 >> 8) & 0xFF]))

    p.text("Relative position 30\n")

    # Set left margin to 20
    p._raw(bytes([0x1D, 0x4C, 20 % 100, 20 // 100]))

    p.text("Left margin 20\n")

    # Set alignment: 0-left, 1-center, 2-right
    for align, name in [(0, "Left"), (1, "Center"), (2, "Right")]:
        p._raw(bytes([0x1B, 0x61, align]))
        p.text(f"Aligned {name}\n")

    # Set print area width 80
    p._raw(bytes([0x1D, 0x57, 80 % 100, 80 // 100]))
    p.text("Width set to 80\n")

    # Reset to full print width (usually 0 disables area limit)
    FULL_WIDTH = 384  # depends on your printer
    p._raw(bytes([0x1D, 0x57, FULL_WIDTH % 256, FULL_WIDTH // 256]))


    # Default line spacing
    p._raw(b'\x1B\x32')
    p.text("Default line spacing\n")

    # Set line spacing to 50
    p._raw(bytes([0x1B, 0x33, 50]))
    p.text("Line spacing 50\n")

    # Select character code page (437 = USA: Standard Europe)
    p._raw(bytes([0x1B, 0x74, 0x00]))
    p.text("Code page 0 (USA)\n")

    # Bold on / off
    p._raw(bytes([0x1B, 0x45, 1]))
    p.text("Bold ON\n")
    p._raw(bytes([0x1B, 0x45, 0]))
    p.text("Bold OFF\n")

    # Invert printing on/off
    p._raw(bytes([0x1B, 0x7B, 1]))
    p.text("Invert ON\n")
    p._raw(bytes([0x1B, 0x7B, 0]))
    p.text("Invert OFF\n")

    # Underline: 0-off, 1-1 dot, 2-2 dot
    for u in range(3):
        p._raw(bytes([0x1B, 0x2D, u]))
        p.text(f"Underline {u}\n")

    # Font size double width and height example: 1,1
    p._raw(bytes([0x1D, 0x21, 0x11]))
    p.text("Double width and height\n")
    p._raw(bytes([0x1D, 0x21, 0x00]))  # Reset font size

    # Inverse print (GS B)
    p._raw(bytes([0x1D, 0x42, 1]))
    p.text("Inverse ON\n")
    p._raw(bytes([0x1D, 0x42, 0]))
    p.text("Inverse OFF\n")

    # Rotate 90 degrees print on/off (ESC V 0 or 1)
    p._raw(bytes([0x1B, 0x56, 1]))
    p.text("Rotate ON\n")
    p._raw(bytes([0x1B, 0x56, 0]))
    p.text("Rotate OFF\n")

    # Select font (0 or 1)
    for font in (0, 1):
        p._raw(bytes([0x1B, 0x4D, font]))
        p.text(f"Font {font}\n")

    # Cut paper full cut
    p.cut()

except Exception as e:
    print(f"An error occurred: {e}")
