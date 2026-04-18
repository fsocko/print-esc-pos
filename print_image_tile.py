import argparse
from PIL import Image
import printer_utils

PRINTER_DPI = printer_utils.PRINTER_DPI
PRINTER_MAX_WIDTH_MM = 72.0


def mm_to_px(mm, dpi=PRINTER_DPI):
    return int((mm / 25.4) * dpi)


def _open_image(path):
    return Image.open(path).convert("RGB")


def _norm_align(a):
    return (a or "left").lower()


# ---------------------------
# CORE TILE ENGINE
# ---------------------------

def print_image_tile(
    image_path,
    segment_length_mm,
    mode="v",
    cut=False,
    align="left",
    printer=None,
):

    if printer is None:
        printer = printer_utils.find_printer(verbose=False)

    printer_utils.reset_formatting(printer)

    img = _open_image(image_path)

    segment_px = mm_to_px(segment_length_mm, PRINTER_DPI)

    print(f"[DEBUG] original={img.size}, segment_px={segment_px}, mode={mode}")

    segments = []

    # ----------------------------------------------------
    # VERTICAL MODE (NO ROTATION)
    # correct behavior: slice left → right
    # ----------------------------------------------------
    if mode == "v":

        axis_len = img.width

        if axis_len <= segment_px:
            scale = (segment_px * 2) / axis_len
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.Resampling.LANCZOS
            )

        for x in range(0, img.width, segment_px):
            segments.append(
                img.crop((x, 0, min(x + segment_px, img.width), img.height))
            )

    # ----------------------------------------------------
    # HORIZONTAL MODE (ROTATE -90° FIRST)
    # correct behavior: landscape assembly
    # ----------------------------------------------------
    elif mode == "h":

        img = img.rotate(-90, expand=True)

        axis_len = img.width

        if axis_len <= segment_px:
            scale = (segment_px * 2) / axis_len
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.Resampling.LANCZOS
            )

        for x in range(0, img.width, segment_px):
            segments.append(
                img.crop((x, 0, min(x + segment_px, img.width), img.height))
            )

    else:
        raise ValueError("mode must be 'v' or 'h'")

    print(f"[DEBUG] segments={len(segments)}")

    # ----------------------------------------------------
    # PRINTER CONSTRAINT (final stage only)
    # ----------------------------------------------------
    max_width_px = mm_to_px(PRINTER_MAX_WIDTH_MM, PRINTER_DPI)

    printer.set(align=_norm_align(align))

    for seg in segments:

        if seg.width > max_width_px:
            scale = max_width_px / seg.width
            seg = seg.resize(
                (int(seg.width * scale), int(seg.height * scale)),
                Image.Resampling.LANCZOS
            )

        printer.image(seg)

        if cut:
            try:
                printer.cut()
            except Exception:
                printer._raw(b'\x1d\x56\x00')


# ---------------------------
# CLI
# ---------------------------

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("image")
    parser.add_argument("--segment-length-mm", type=float, required=True)

    parser.add_argument(
        "-m", "--mode",
        choices=["v", "h"],
        default="v"
    )

    parser.add_argument("-c", "--cut", action="store_true")
    parser.add_argument("--align", default="left")

    args = parser.parse_args()

    print_image_tile(
        image_path=args.image,
        segment_length_mm=args.segment_length_mm,
        mode=args.mode,
        cut=args.cut,
        align=args.align,
    )


if __name__ == "__main__":
    main()