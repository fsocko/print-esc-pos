# 80mm ESC/POS TEST

## Headings

# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6


### Level 3 Heading

Normal paragraph text. This should wrap correctly across multiple lines and demonstrate basic formatting.

---

## Formatting

This is **bold text** and this is *emphasized text*.


Inline code example: `print("hello")`

---

## Lists

• This is not a markdown bullet (should render literally)

- Item one
- Item two with a very long line that should wrap correctly even when it exceeds the printer width significantly
- Item three

---

## URLs (critical test)

https://fsocko.github.io/print-esc-pos/
https://python-escpos.readthedocs.io/en/latest/user/methods.html#escpos-class

---

## Code Block (tab-indented)

    def hello():
        print("This should NOT be truncated")
        print("Long line test: 12345678901234567890123456789012345678901234567890")

---

## Table Test

| Item        | Value  | Price  |
|------------|--------|--------|
| Apple      | 10     | 1.50   |
| Banana     | 2      | 0.30   |
| Watermelon | 100    | 12.99  |

---

## Mixed Content

Some text before list:

- First bullet
- Second bullet

Ending paragraph to ensure spacing works correctly.



## QR and BAR codes


Inline QR code: [qrcode:https://example.com] prints a QR code

[barcode:123456789012]         # defaults to EAN13
[barcode:ABC123:CODE39]        # explicitly use Code39
