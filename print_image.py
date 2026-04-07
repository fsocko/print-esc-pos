from PIL import Image
import warnings
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
):
    """
    SAFE image printing:
    - uses shared printer instance
    - resets ESC/POS state before printing
    - does NOT close printer
    """

    try:
        if printer is None:
            printer = printer_utils.find_printer(verbose=False)

        # ---- CRITICAL: reset printer state ----
        printer_utils.reset_formatting(printer)

        img = _open_image(image_input)
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width if orig_width else 1.0

        # ---- Resize logic ----
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

            img = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)

        elif scale_width_percentage:
            if not (1 <= scale_width_percentage <= 100):
                raise ValueError("Scale percentage must be between 1 and 100.")

            target_width = int((scale_width_percentage / 100.0) * PRINTER_WIDTH_PX)
            target_height = int(target_width * aspect_ratio)

            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        elif orig_width > PRINTER_WIDTH_PX:
            warnings.warn("Image too wide, auto-scaling.")
            img = img.resize(
                (PRINTER_WIDTH_PX, int(PRINTER_WIDTH_PX * aspect_ratio)),
                Image.Resampling.LANCZOS
            )

        # ---- Alignment AFTER reset ----
        align = _normalize_align(align_param)
        printer.set(align=align)

        # ---- Print ----
        printer.image(img)

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
            )
        else:
            core_print_image(
                image_paths[0],
                scale_width_percentage=scale_width,
                target_width_mm=width_mm,
                target_height_mm=height_mm,
                align_param=align,
                printer=printer,
            )

        # ---- isolate after image ----
        printer.text("\n\n")

    except Exception as e:
        printer_utils.reset_printer()
        raise RuntimeError(f"Failed to print image(s): {e}")