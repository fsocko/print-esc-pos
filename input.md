#Heading 1

- list1
- list2
- list3

TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT
TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT TEXT


# Convert Markdown to ESC/POS escape sequences

escpos_sequence = markdown_to_escpos(md_text)

# Output raw ESC/POS commands (can be sent to printer later)
print(repr(escpos_sequence))  # `repr()` ensures escape sequences are visible




-----

*** SPECIAL TEXT ***

***

LINE SHOULD BE ABOVE ME



In Markdown, a horizontal rule (or line) can be created by typing three or more dashes (---), asterisks (***), or underscores (___) on a new line. This will render a horizontal line in the output.

---

1

***

2

___

3
