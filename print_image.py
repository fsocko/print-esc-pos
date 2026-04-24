import sys
from PIL import Image
import argparse
import os
import printer_utils

# Printer constants
PRINTER_CHAR_WIDTH  = printer_utils.PRINTER_CHAR_WIDTH
PRINTER_WIDTH_PX    = printer_utils.PRINTER_WIDTH_PX
PRINTER_DPI         = printer_utils.PRINTER_DPI

# Calibration
HORIZONTAL_SCALE_CORRECTION = 1.00
VERTICAL_SCALE_CORRECTION = 1.012


# ---------------------------
# Helpers
# ---------------------------

def mm_to_pixels(mm, dpi=PRINTER_DPI, axis="x"):
    correction = HORIZONTAL_SCALE_CORRECTION if axis == "x" else VERTICAL_SCALE_CORRECTION
    return int((mm / 25.4) * dpi * correction)


def _normalize_align(align_param):
    if not align_param:
        return "left"
    a = align_param.lower()
    if a in ("l", "left"):
        return "left"
    if a in ("c", "center", "centre"):
        return "center"
    if a in ("r", "right"):
        return "right"
    return "left"


def _open_image(image_input):
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image file not found: {image_input}")
        return Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        return image_input
    else:
        raise TypeError("image_input must be a filename or PIL.Image.Image instance")
    
def pil_to_escpos_raster(img):
    """
    Convert 1-bit PIL image to ESC/POS GS v 0 raster format
    """
    if img.mode != "1":
        raise ValueError("Image must be 1-bit")

    width, height = img.size
    width_bytes = (width + 7) // 8

    pixels = img.load()
    data = bytearray()

    for y in range(height):
        for xb in range(width_bytes):
            byte = 0
            for bit in range(8):
                x = xb * 8 + bit
                if x < width and pixels[x, y] == 0:  # black pixel
                    byte |= (1 << (7 - bit))
            data.append(byte)

    header = bytearray([
        0x1D, 0x76, 0x30, 0x00,
        width_bytes & 0xFF,
        (width_bytes >> 8) & 0xFF,
        height & 0xFF,
        (height >> 8) & 0xFF
    ])

    return header + data


# ---------------------------
# Image composition
# ---------------------------

def combine_images_horizontally(image_paths, spacing=0):
    imgs = [Image.open(p).convert("RGBA") for p in image_paths]

    total_width = sum(im.width for im in imgs) + spacing * (len(imgs) - 1)
    max_height = max(im.height for im in imgs)

    combined = Image.new("RGB", (total_width, max_height), color=(255, 255, 255))

    x_offset = 0
    for im in imgs:
        if im.mode == "RGBA":
            combined.paste(im, (x_offset, 0), im)
        else:
            combined.paste(im, (x_offset, 0))
        x_offset += im.width + spacing

    return combined


# ---------------------------
# Core printing
# ---------------------------

def core_print_image(
    image_input,
    scale_width_percentage=None,
    align_param="left",
    target_width_mm=None,
    target_height_mm=None,
    printer=None,
    raw_mode=False
):
    """
    Enhanced image printing with controlled preprocessing and optional RAW mode.
    """

    # ---------------------------
    # TUNING VARIABLES
    # ---------------------------
    USE_RAW_MODE = raw_mode          
    FORCE_FULL_WIDTH = True          # force resize to printer width
    CONTRAST_FACTOR = 1.5            # 1.5–2.5 typical
    SHARPEN = False
    THRESHOLD = 160                 # 160–200 typical
    ENABLE_DITHER = False           # usually False for maps/text

    try:
        if printer is None:
            printer = printer_utils.find_printer(verbose=False)

        printer_utils.reset_formatting(printer)

        img = _open_image(image_input)
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width if orig_width else 1.0

        # ---------------------------
        # RESIZE (CRITICAL)
        # ---------------------------
        if target_width_mm or target_height_mm:
            if target_width_mm and not target_height_mm:
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = int(target_width_px * aspect_ratio)

            elif target_height_mm and not target_width_mm:
                target_height_px = mm_to_pixels(target_height_mm, axis="y")
                target_width_px = int(target_height_px / aspect_ratio)

            else:
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = mm_to_pixels(target_height_mm, axis="y")

            img = img.resize((target_width_px, target_height_px), Image.Resampling.NEAREST)

        elif scale_width_percentage:
            target_width = int((scale_width_percentage / 100.0) * PRINTER_WIDTH_PX)
            target_height = int(target_width * aspect_ratio)

            img = img.resize((target_width, target_height), Image.Resampling.NEAREST)

        elif FORCE_FULL_WIDTH:
            target_width = PRINTER_WIDTH_PX
            target_height = int(target_width * aspect_ratio)

            img = img.resize((target_width, target_height), Image.Resampling.NEAREST)

        elif orig_width > PRINTER_WIDTH_PX:
            img = img.resize(
                (PRINTER_WIDTH_PX, int(PRINTER_WIDTH_PX * aspect_ratio)),
                Image.Resampling.NEAREST
            )

        # ---------------------------
        # PREPROCESSING
        # ---------------------------
        from PIL import ImageEnhance, ImageFilter

        img = img.convert("L")

        img = ImageEnhance.Contrast(img).enhance(CONTRAST_FACTOR)

        if SHARPEN:
            img = img.filter(ImageFilter.SHARPEN)

        if ENABLE_DITHER:
            img = img.convert("1")  # PIL dithering
        else:
            img = img.point(lambda x: 0 if x < THRESHOLD else 255, '1')

        # ---------------------------
        # ALIGNMENT
        # ---------------------------
        align = _normalize_align(align_param)
        printer.set(align=align)

        # ---------------------------
        # PRINT
        # ---------------------------
        if USE_RAW_MODE:
            raster = pil_to_escpos_raster(img)
            printer._raw(raster)
        else:
            printer.image(img, impl='bitImageRaster')

        return True

    except Exception:
        printer_utils.reset_printer()
        raise

# ---------------------------
# Public command
# ---------------------------

def print_image_cmd(
    image_paths,
    scale_width=None,
    width_mm=None,
    height_mm=None,
    align="left",
    spacing=0,
    printer=None,
    raw=False
):
    """
    Entry point used by markdown renderer.

    Guarantees:
    - no printer reopen
    - newline isolation
    - safe state transitions
    """

    if printer is None:
        printer = printer_utils.find_printer(verbose=False)

    # normalize paths
    if isinstance(image_paths, str):
        image_paths = image_paths.split("|")

    try:
        # ---- isolate from previous text ----
        printer.text("\n")

        if len(image_paths) > 1:
            combined = combine_images_horizontally(image_paths, spacing=spacing)
            core_print_image(
                combined,
                scale_width_percentage=scale_width,
                target_width_mm=width_mm,
                target_height_mm=height_mm,
                align_param=align,
                printer=printer,
                raw_mode=raw,
            )
        else:
            core_print_image(
                image_paths[0],
                scale_width_percentage=scale_width,
                target_width_mm=width_mm,
                target_height_mm=height_mm,
                align_param=align,
                printer=printer,
                raw_mode=raw,  
            )

        # ---- isolate after image ----
        printer.text("\n")

    except Exception as e:
        printer_utils.reset_printer()
        raise RuntimeError(f"Failed to print image(s): {e}")
    
    
def main(argv=None):
    
    parser = argparse.ArgumentParser(description="Print image(s) to ESC/POS thermal printer")
    parser.add_argument( "image", help="Image path or multiple paths separated by |")
    parser.add_argument( "--scale", type=int, help="Scale image width as percentage of printer width (1–100)")
    parser.add_argument( "--width-mm", type=float, help="Target width in millimeters")
    parser.add_argument( "--height-mm", type=float, help="Target height in millimeters")
    parser.add_argument( "--align", choices=["left", "center", "right"], default="center")
    parser.add_argument( "--spacing", type=int, default=0, help="Spacing between multiple images")
    parser.add_argument(
        "-r", "--raw",
        action="store_true",
        help="Enable raw ESC/POS raster mode"
    )
    
    args = parser.parse_args(argv)

    print_image_cmd(
        image_paths=args.image,
        scale_width=args.scale,
        width_mm=args.width_mm,
        height_mm=args.height_mm,
        align=args.align,
        spacing=args.spacing,
        raw=args.raw
    )
