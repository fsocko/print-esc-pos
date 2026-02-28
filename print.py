#!/c/Users/fsock/AppData/Local/Programs/Python/Python310/python

import sys
import argparse
import print_text
import print_image
import print_raw
import printer_utils

def is_image_file(path: str) -> bool:
    ext = path.lower().rsplit(".", 1)[-1]
    return ext in ("png", "jpg", "jpeg", "bmp", "gif")

def detect_input_type(file_path=None):
    if file_path:
        if is_image_file(file_path):
            return "image"
        try:
            with open(file_path, "rb") as f:
                f.read(512).decode("utf-8")
            return "text"
        except Exception:
            return "raw"
    # stdin autodetect
    if not sys.stdin.isatty():
        peek = sys.stdin.buffer.peek(512)
        try:
            peek.decode("utf-8")
            return "text"
        except Exception:
            return "raw"
    return None

def show_all_help():
    print("\n=== print_text options ===")
    try:
        print_text.main(["-h"])
    except SystemExit:
        pass
    print("\n=== print_image options ===")
    try:
        print_image.main(["-h"])
    except SystemExit:
        pass
    print("\n=== print_raw options ===")
    try:
        print_raw.main(["-h"])
    except SystemExit:
        pass
    
def core_print(file=None, mode=None, cut=False, extra_args=None):
    """
    Pure print executor.
    No autodetection.
    No CLI behavior.
    Raises exceptions on error.
    """

    if extra_args is None:
        extra_args = []

    if not mode:
        raise ValueError("Mode must be explicitly provided")

    submodule_args = []
    if file:
        submodule_args.append(file)
    submodule_args.extend(extra_args)

    if mode == "text":
        print_text.main(submodule_args)
    elif mode == "image":
        print_image.main(submodule_args)
    elif mode == "raw":
        print_raw.main(submodule_args)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    if cut:
        printer_utils.cut_paper()

def main_with_args(argv):

    parser = argparse.ArgumentParser(
        description="Print text, images, or raw ESC/POS data."
    )

    parser.add_argument("file", nargs="?", help="File to print")
    parser.add_argument("--mode", choices=["text", "image", "raw"])
    parser.add_argument("-c", "--cut", action="store_true")
    parser.add_argument("--help-all", action="store_true")

    args, extras = parser.parse_known_args(argv)

    if args.help_all:
        show_all_help()
        return

    # CLI autodetect logic
    mode = args.mode or detect_input_type(args.file)

    if not mode:
        if args.cut:
            try:
                printer_utils.cut_paper()
            except Exception as e:
                print(f"Failed to cut paper: {e}")
            return
        else:
            parser.print_help()
            print("\nUse --help-all to see full submodule help")
            return

    try:
        core_print(
            file=args.file,
            mode=mode,
            cut=args.cut,
            extra_args=extras
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
                        
def main():
    main_with_args(sys.argv[1:])            
        
if __name__ == "__main__":
    main()
