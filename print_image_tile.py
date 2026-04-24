import argparse
import math
import os
from PIL import Image
import printer_utils

PRINTER_DPI = printer_utils.PRINTER_DPI
PRINTER_MAX_WIDTH_MM = 72.0

TEMP_DIR = "./tile_debug"


# ---------------------------
# Helpers
# ---------------------------

def mm_to_px(mm):
    return int(mm * (PRINTER_DPI / 25.4))


def px_to_mm(px):
    return (px / PRINTER_DPI) * 25.4


def _open(path):
    return Image.open(path).convert("RGB")


def _ensure_temp():
    os.makedirs(TEMP_DIR, exist_ok=True)


# ---------------------------
# CORE TILE ENGINE
# ---------------------------

def print_image_tile(
    image_path,
    segment_length_mm,
    mode="v",
    cut=False,
    align="left",
    save_debug=True,
    printer=None,
):

    if printer is None:
        printer = printer_utils.find_printer(verbose=False)

    printer_utils.reset_formatting(printer)

    _ensure_temp()

    img = _open(image_path)

    print(f"[DEBUG] original={img.size}, mode={mode}")

    # ----------------------------------------------------
    # ORIENTATION
    # ----------------------------------------------------
    if mode == "h":
        img = img.rotate(-90, expand=True)

    # ----------------------------------------------------
    # SEGMENT GRID SIZE
    # ----------------------------------------------------
    segment_px = mm_to_px(segment_length_mm)
    max_width_px = mm_to_px(PRINTER_MAX_WIDTH_MM)

    # ----------------------------------------------------
    # PHYSICAL ESTIMATE
    # ----------------------------------------------------
    img_w_mm = px_to_mm(img.width)
    img_h_mm = px_to_mm(img.height)

    print(f"[DEBUG] image_mm={img_w_mm:.2f} x {img_h_mm:.2f}")

    # ----------------------------------------------------
    # GRID COMPUTATION (NO ARTIFICIAL MINIMUMS)
    # ----------------------------------------------------
    x_segments = max(1, math.ceil(img.width / max_width_px))
    y_segments = max(1, math.ceil(img.height / segment_px))

    print(f"[DEBUG] grid={x_segments} x {y_segments}")

    # ----------------------------------------------------
    # SCALE TO ALIGN CLEANLY WITH GRID
    # (prevents partial pixel tiles)
    # ----------------------------------------------------
    target_w = x_segments * max_width_px
    target_h = y_segments * segment_px

    scale_x = target_w / img.width
    scale_y = target_h / img.height

    scale = max(scale_x, scale_y)

    if abs(scale - 1.0) > 0.001:
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.Resampling.LANCZOS
        )
        print(f"[DEBUG] scaled={img.size}")

    # ----------------------------------------------------
    # TILE GENERATION (2D GRID)
    # ----------------------------------------------------
    tiles = []

    for y in range(y_segments):
        for x in range(x_segments):

            x0 = x * max_width_px
            y0 = y * segment_px

            tile = img.crop((
                x0,
                y0,
                min(x0 + max_width_px, img.width),
                min(y0 + segment_px, img.height)
            ))

            tiles.append(tile)

            if save_debug:
                tile.save(f"{TEMP_DIR}/tile_{y}_{x}.png")

    print(f"[DEBUG] tiles={len(tiles)}")

    # ----------------------------------------------------
    # PRINT
    # ----------------------------------------------------
    printer.set(align=(align or "left").lower())

    for t in tiles:

        printer.image(t)

        if cut:
            try:
                printer.cut()
            except Exception:
                printer._raw(b'\x1d\x56\x00')


# ---------------------------
# CLI
# ---------------------------

def main(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("image")
    parser.add_argument("--segment-length-mm", type=float, required=True)

    parser.add_argument("-m", "--mode", choices=["v", "h"], default="v")
    parser.add_argument("-c", "--cut", action="store_true")

    args = parser.parse_args(argv)

    print_image_tile(
        image_path=args.image,
        segment_length_mm=args.segment_length_mm,
        mode=args.mode,
        cut=args.cut,
    )


if __name__ == "__main__":
    main()