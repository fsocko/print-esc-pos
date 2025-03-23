#!/bin/bash

# Loop through ASCII values 32 to 126 (printable characters)
for i in {32..126}; do
    # Print the character corresponding to the ASCII value
    printf "%b" "\x$(printf '%02x' $i)"
done

echo  # Newline at the end
