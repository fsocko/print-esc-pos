#!/bin/bash

# Select Font A (0)
echo -e "\x1Bt0"  # Font A (Default)

# Print some text
echo -e "This is Font A"

# Select Font B (1)
echo -e "\x1Bt1"  # Font B
echo -e "This is Font B"

# Enable Bold (ESC E 1)
echo -e "\x1BE\x01"  # Enable Bold
echo -e "This is bold text"

# Disable Bold (ESC E 0)
echo -e "\x1BE\x00"  # Disable Bold
echo -e "This is normal text"

# Enable Underline (ESC - 1)
echo -e "\x1B-\x01"  # Enable Underline
echo -e "This text is underlined"

# Disable Underline (ESC - 0)
echo -e "\x1B-\x00"  # Disable Underline
echo -e "This text is not underlined"
