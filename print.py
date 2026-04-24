#!/c/Users/fsock/AppData/Local/Programs/Python/Python310/python

import sys
import argparse
import print_text
import print_image
import print_raw
import printer_utils
import print_markdown
import print_image_tile

def is_image_file(path: str) -> bool:
    ext = path.lower().rsplit(".", 1)[-1]
    return ext in ("png", "jpg", "jpeg", "bmp", "gif")

def is_markdown_file(path: str) -> bool:
    ext = path.lower().rsplit(".", 1)[-1]
    return ext in ("md", "mkd")

def detect_input_type(file_path=None):
    if file_path:
        if is_image_file(file_path):
            return "image"
        elif is_markdown_file(file_path):
            return "markdown"
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

def split_args(argv):
    """
    Extract known print.py args.
    Everything else is forwarded untouched.
    """

    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--mode")
    parser.add_argument("-c", "--cut", action="store_true")
    parser.add_argument("--help-all", action="store_true")

    args, remaining = parser.parse_known_args(argv)

    file = None
    extras = []

    for arg in remaining:
        if file is None and not arg.startswith("-"):
            file = arg
        else:
            extras.append(arg)

    return args, file, extras

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
    
    print("\n=== print_image_tile options ===")
    try:
        print_image_tile.main(["-h"])
    except SystemExit:
        pass

    print("\n=== print markdown options ===")
    try:
        print_markdown.main(["-h"])
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
    elif mode == "markdown":
        print_markdown.main(submodule_args)
    elif mode == "image":
        print_image.main(submodule_args)
    elif mode == "image-tile":
        print_image_tile.main(submodule_args)
    elif mode == "raw":
        print_raw.main(submodule_args)
    else:
        raise ValueError(f"Invalid mode: {mode}")

    if cut:
        printer_utils.cut_paper()

def main_with_args(argv):

    args, file, extras = split_args(argv)

    if args.help_all:
        show_all_help()
        return

    mode = args.mode or detect_input_type(file)

    if not mode:
        if args.cut:
            printer_utils.cut_paper()
            return
        else:
            parser = argparse.ArgumentParser()
            parser.print_help()
            return

    core_print(
        file=file,
        mode=mode,
        cut=args.cut,
        extra_args=extras
    )
                            
def main():
    main_with_args(sys.argv[1:])            
        
if __name__ == "__main__":
    main()
