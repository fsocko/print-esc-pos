from escpos.printer import Usb
import printer_utils

def get_printer(stream_mode=False):
    printer = printer_utils.find_printer(verbose=not stream_mode)
    printer_utils.initialize_printer(printer, verbose=not stream_mode)
    return printer

from escpos.printer import Usb
import printer_utils

test_texts = {
    "Western Europe": "Olá, café com pão e açúcar! 123 €",
    "Nordic": "ÆØÅ æøå øl smør",
    "Polish": "Zażółć gęślą jaźń",
    "Cyrillic": "Привет мир"
}

def find_compatible_codepage(text):

    # ESC/POS codepage candidates: (n, python_codec, description)
    candidates = [
        (2, "cp850", "Western Europe"),
        (16, "cp1252", "Western Europe + €"),
        (5, "cp865", "Nordic"),
        (18, "cp852", "Polish / Central Europe"),
    ]

    for n, codec, desc in candidates:
        try:
            text.encode(codec)
            return n, codec, desc
        except UnicodeEncodeError:
            continue
    return None, None, None

# Open printer once
p = printer_utils.find_printer(verbose=True)
printer_utils.initialize_printer(p, verbose=True)

for label, text in test_texts.items():
    n, codec, desc = find_compatible_codepage(text)
    if n is None:
        print(f"No compatible code page found for {label}")
        continue

    print(f"Printing {label} text using ESC/POS codepage {n} ({desc}, codec={codec})")
    p._raw(b"\x1B\x74" + bytes([n]))
    encoded_text = text.encode(codec)
    p._raw(encoded_text + b"\n")

p.cut()
p.close()