#!/usr/bin/env python3
from datetime import datetime
import sys

def timestamp():
    return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

# Check if anything is being piped into stdin
if sys.stdin.isatty():
  # No input piped in
  print(f"{timestamp()} - [no input provided]")
else:
    empty = True
    for line in sys.stdin:
        print(f"{timestamp()} - {line.rstrip()}")
        empty = False
    if empty:
        print(f"{timestamp()} - [no input provided]")
