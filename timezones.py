from escpos.printer import Usb

# Initialize the printer (replace with your printer's vendor and product IDs)
PRINTER_VENDOR_ID = 0x0416  # Replace with your printer's vendor ID
PRINTER_PRODUCT_ID = 0x5011  # Replace with your printer's product ID

col_width = 15

def rpad(s):
    return f"{s:-<{col_width}}"

try:
    printer = Usb(PRINTER_VENDOR_ID, PRINTER_PRODUCT_ID)

 
    lines = []

    header = "{:<{w}} | {:<{w}} | {:<{w}}".format("LIS", "ATL", "SEA", w=col_width)
    separator = "\n" + "-" * (col_width-1) + "+" + "-" * (col_width) + "+" + "-" * (col_width + 1)
    empty_separator = "\n" + ("-" * 48) + "\n"
    
    printer.set(align="left")
    printer.set(invert=False)
    printer.set(underline=1)
    printer.set(bold=1)
    printer.text(header)
    printer.set(underline=0)
    printer.set(bold=0)

    for i in range(0, 24):
        
        if((i) % 24 < 9 or (i) % 24 > 22):
            printer.set(invert=True)
        time_str_lis = rpad("{:02d}:00".format(i % 24))
        printer.text(time_str_lis);
        
        if((i - 5) % 24 < 9 or (i - 5) % 24 > 22):
            printer.set(invert=True)
        time_str_atl = rpad("{:02d}:00".format((i - 5) % 24))
        printer.text(time_str_atl);
        
        printer.set(invert=False)        
        if((i - 8) % 24 < 9 or (i - 8) % 24 > 22):
            printer.set(invert=True)
        time_str_sea = rpad("{:02d}:00".format((i - 8) % 24))
        printer.text(time_str_sea);

        printer.text("\n");
                
    printer.set(invert=False)
    printer.text(empty_separator)
    
    lis_dst = "LIS: DST STARTS on the last Sunday of March .\n DST ENDS on the last Sunday of October."
    us_dst = "US: DST STARTS on the second Sunday of March.\nUS DST Ends Daylight Saving Time on the first Sunday of November."
    
    printer.text(lis_dst)
    printer.text(empty_separator)
    printer.text(us_dst)
    
    printer.cut()
    printer.close()

except Exception as e:
    print(f"An error occurred: {e}")