import sys
import os
import subprocess
import print_text
import print_image
import print_raw

def is_image_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    return ext in (".png", ".jpg", ".jpeg", ".bmp", ".gif")

def detect_input_type(argv):
    """Detects whether input is text, image, or raw binary."""
    if len(argv) >= 1 and os.path.exists(argv[0]):
        if is_image_file(argv[0]):
            return "image", argv[0]
        else:
            with open(argv[0], "rb") as f:
                data = f.read(512)
                try:
                    data.decode("utf-8")
                    return "text_file", argv[0]
                except UnicodeDecodeError:
                    return "raw_file", argv[0]

    if not sys.stdin.isatty():
        peek = sys.stdin.buffer.peek(512)
        try:
            peek.decode("utf-8")
            return "text_stdin", None
        except UnicodeDecodeError:
            return "raw_stdin", None

    return "none", None


def show_help():
    """Print top-level help and subcommand helps (via argparse)."""
    print("Usage:")
    print("  print.py [options] [file]\n")
    print("Automatically detects input type (text/image/raw).")
    print("Examples:")
    print("  echo 'Hello world' | python print.py")
    print("  python print.py receipt.txt")
    print("  python print.py logo.png")
    print("  cat data.escpos | python print.py\n")

    print("Global options:")
    print("  -h, --help        Show this help message")
    print("  --mode {text,image,raw}  Force mode detection\n")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))

    def run_help(module, name=None):
        if name is None:
            name = module.__name__
        print(f"\n\n[ {name} options ]\n")
        try:
            module.main(["-h"])
        except SystemExit:
            pass  # ignore sys.exit() from argparse

    run_help(print_text, "print_text")
    run_help(print_image, "print_image")
    run_help(print_raw, "print_raw")
    

def main():
    argv = sys.argv[1:]

    if "-h" in argv or "--help" in argv:
        show_help()
        return

    mode = None
    if "--mode" in argv:
        i = argv.index("--mode")
        if i + 1 < len(argv):
            mode = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]

    if not mode:
        mode, target = detect_input_type(argv)
    else:
        target = argv[0] if argv else None

    if mode in ("text_stdin", "text_file") or mode == "text":
        print_text.main(argv)
    elif mode in ("image",):
        print_image.main(argv)
    elif mode in ("raw_stdin", "raw_file") or mode == "raw":
        print_raw.main(argv)
    else:
        show_help()


if __name__ == "__main__":
    main()
