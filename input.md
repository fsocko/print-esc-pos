# 80mm ESC/POS TEST

# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6



## Formatting

This is **bold text** and this is *emphasized text*.

Inline code example: `print("hello")`

This is a simple paragraph with **bold text**, *emphasis*, and inline code like `ESC/POS`.


## Centered Heading Example

> Thank you for shopping with us!


# Shopping List

- **Fruits**: apples, bananas, oranges
- *Vegetables*: carrots, broccoli, spinach
- Mixed **bold** and *italic* text in one item
- Very long item that should wrap correctly to the next line without losing the bullet alignment or formatting, second very long item that should wrap correctly to the next line without losing the bullet alignment or formatting.


## URLs (critical test)

https://fsocko.github.io/print-esc-pos/
https://python-escpos.readthedocs.io/en/latest/user/methods.html#escpos-class


## Code Block (tab-indented)

    def hello():
        print("This should NOT be truncated")
        print("Long line test: 12345678901234567890123456789012345678901234567890")



## Table Test

| Item        | Value  | Price  |
|------------|--------|--------|
| Apple      | 10     | 1.50   |
| Banana     | 2      | 0.30   |
| Watermelon | 100    | 12.99  |


## Table with Auto Alignment + Decimal Alignment

| Item                      | Qty | Price |
| :------------------------ | :-- | ----: |
| Apple                     |   2 |   1.0 |
| Banana                    |  10 | 12.50 |
| Chocolate Bar Extra Large |   3 | 123.4 |

## Table with RIGHT Alignment + Decimal Alignment

| Item                      | Qty | Price |
| ------------------------: | --: | ----: |
| Apple                     |   2 |   1.0 |
| Banana                    |  10 | 12.50 |
| Chocolate Bar Extra Large |   3 | 123.4 |


## Multiline Cell Demonstration

| Product Description                                                  | Qty | Unit Price |
| :------------------------------------------------------------------- | --: | ---------: |
| Very long product name that should wrap nicely across multiple lines |   1 |       9.99 |
| Another extremely long product description to test wrapping behavior |  12 |     123.45 |


## Mixed Content Table

| Name   | Notes                                                                                       | Value |
| :----- | :------------------------------------------------------------------------------------------ | ----: |
| Test A | Short note                                                                                  |  1.00 |
| Test B | This is a much longer note that should wrap into multiple lines properly without truncation |  25.5 |
| Test C | Inline `code` example inside table                                                          |   300 |


## Code Block

```
for i in range(3):
    print("Receipt line", i)
```


## Final Totals

| Label     | Amount |
| :-------- | -----: |
| Subtotal  | 137.94 |
| Tax (23%) |  31.73 |
| Total     | 169.67 |



## Mixed Content

Some text before list:

- First bullet
- Second bullet

Ending paragraph to ensure spacing works correctly.



## QR and BAR codes


Inline QR code: [qrcode:https://example.com] prints a QR code

[barcode:123456789012]         # defaults to EAN13
[barcode:ABC123:CODE39]        # explicitly use Code39
