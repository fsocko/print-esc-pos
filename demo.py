from escpos.printer import Usb

# Initialize the printer (replace with your printer's vendor and product IDs)
PRINTER_VENDOR_ID = 0x0416  # Replace with your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Replace with your printer's product ID

try:
    printer = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)

    # Print basic text
    printer.text("Hello World\n")
    printer.text("This is a demo of python-escpos.\n\n")

    # Print text with alignment
    # printer.set(align="center")
    # printer.text("This text is center aligned.\n")
    # printer.set(align="right")
    # printer.text("This text is right aligned.\n")
    # printer.set(align="left")
    # printer.text("This text is left aligned.\n\n")

    # # Print bold text
    # printer.set(bold=True)
    # printer.text("This text is bold.\n")
    # printer.set(bold=False)
    # printer.text("This text is not bold.\n\n")

    # # Print underlined text
    # printer.set(underline=1)
    # printer.text("This text is underlined.\n")
    # printer.set(underline=2)
    # printer.text("This text is double underlined.\n")
    # printer.set(underline=0)
    # printer.text("This text is not underlined.\n\n")

    # # Print double height and double width text
    # printer.set(double_height=True)
    # printer.text("This text is double height.\n")
    # printer.set(double_width=True)
    # printer.text("This text is double height and width.\n")
    # printer.set(double_height=False, double_width=False)
    # printer.text("This text is normal size.\n\n")

    # # Print a barcode
    # printer.barcode("123456789012", "EAN13", width=2, height=100, pos="below", font="A")
    # printer.text("\n")

    # # Print a QR code
    # printer.qr("https://github.com/python-escpos/python-escpos", size=8)
    # printer.text("\n")

    # # Print inverted text
    # printer.set(invert=True)
    # printer.text("This text is inverted.\n")
    # printer.set(invert=False)
    # printer.text("This text is normal.\n\n")

    printer.buzzer(times=4, duration=8)
    

    # Cut the paper
    printer.cut()

    # Open the cash drawer
    printer.cashdraw(2)

    print("Demo completed successfully.")
    printer.close()

except Exception as e:
    print(f"An error occurred: {e}")