# printer/print_image.py
from PIL import Image
import warnings
import printer_utils
import os

# Printer constants (kept in sync with your original file)
PRINTER_CHAR_WIDTH = 48
PRINTER_WIDTH_PX = 640
PRINTER_DPI = 203  # Usually 203 DPI = 8 dots/mm

# Correction multipliers for fine-tuning physical accuracy
HORIZONTAL_SCALE_CORRECTION = 1.00
VERTICAL_SCALE_CORRECTION = 1.012  # increase height ~2% to match ruler due to calibration experiments

def mm_to_pixels(mm, dpi=PRINTER_DPI, axis="x"):
    """
    Convert millimetres to pixels using printer DPI and axis-specific correction.
    axis: "x" or "y" (horizontal/vertical).
    """
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
    # fallback
    return "left"

def _open_image(image_input):
    """
    Accept either a path (str) or a PIL.Image.Image instance.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image file not found: {image_input}")
        return Image.open(image_input)
    elif isinstance(image_input, Image.Image):
        return image_input
    else:
        raise TypeError("image_input must be a filename or PIL.Image.Image instance")

def print_image(
    image_input,
    cut=False,
    scale_width_percentage=None,
    align_param="left",
    target_width_mm=None,
    target_height_mm=None,
    stream_mode=False,
):
    """
    Print an image, supporting:
      - physical sizing via target_width_mm/target_height_mm
      - percentage width scaling via scale_width_percentage (1-100)
      - auto-scaling if image too wide for PRINTER_WIDTH_PX
      - alignment: left/center/right (or l/c/r)
    """
    try:
        # Initialize printer (respecting stream mode parameter if you use that in printer_utils)
        printer = printer_utils.find_printer(verbose=not stream_mode)

        img = _open_image(image_input)
        orig_width, orig_height = img.size
        aspect_ratio = orig_height / orig_width if orig_width != 0 else 1.0

        # Resize using physical dimensions if any are provided
        if target_width_mm or target_height_mm:
            if target_width_mm and not target_height_mm:
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = int(target_width_px * aspect_ratio)
            elif target_height_mm and not target_width_mm:
                target_height_px = mm_to_pixels(target_height_mm, axis="y")
                target_width_px = int(target_height_px / aspect_ratio)
            else:
                # both provided: use them directly (may distort if aspect differs)
                target_width_px = mm_to_pixels(target_width_mm, axis="x")
                target_height_px = mm_to_pixels(target_height_mm, axis="y")

            if target_width_px <= 0 or target_height_px <= 0:
                raise ValueError("Computed target pixel dimensions are invalid.")
            img = img.resize((target_width_px, target_height_px), Image.Resampling.LANCZOS)

        # Fallback: percentage scale
        elif scale_width_percentage:
            if scale_width_percentage <= 0 or scale_width_percentage > 100:
                raise ValueError("Scale percentage must be between 1 and 100.")
            target_width = int((scale_width_percentage / 100.0) * PRINTER_WIDTH_PX)
            target_height = int(target_width * aspect_ratio)
            if target_width <= 0 or target_height <= 0:
                raise ValueError("Computed target pixel dimensions are invalid.")
            img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)

        # Fallback: auto-scale if too wide
        elif orig_width > PRINTER_WIDTH_PX:
            warnings.warn(
                f"Image width {orig_width}px exceeds printer max width {PRINTER_WIDTH_PX}px. "
                "Auto-scaling to printer width."
            )
            img = img.resize((PRINTER_WIDTH_PX, int(PRINTER_WIDTH_PX * aspect_ratio)), Image.Resampling.LANCZOS)

        # Set alignment and send image
        align = _normalize_align(align_param)
        printer.set(align=align)
        printer.image(img)

        if cut:
            printer.cut()

        printer.close()
        return True

    except Exception:
        # Let caller decide how to handle exceptions; re-raise for visibility in CLI usage.
        raise

def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(description="Print image to ESC/POS printer.")
    parser.add_argument("image", help="Path to image file.")
    parser.add_argument("-c", "--cut", action="store_true", help="Cut after printing.")
    parser.add_argument("-w", "--scale-width", type=int, dest="scale_width", help="Percentage of printer width (1-100).")
    parser.add_argument("--width-mm", type=float, dest="width_mm", help="Target physical width in millimetres.")
    parser.add_argument("--height-mm", type=float, dest="height_mm", help="Target physical height in millimetres.")
    parser.add_argument("-x", "--align", type=str, choices=["left", "center", "right", "l", "c", "r"], default="left", help="Alignment.")
    parser.add_argument("--stream", action="store_true", help="Use stream/quiet printer initialization (internal).")
    parsed = parser.parse_args(args)

    # Normalize shorthand alignment options inside print_image call (function will normalize as well).
    try:
        print_image(
            parsed.image,
            cut=parsed.cut,
            scale_width_percentage=parsed.scale_width,
            align_param=parsed.align,
            target_width_mm=parsed.width_mm,
            target_height_mm=parsed.height_mm,
            stream_mode=parsed.stream,
        )
        print("Image print successful.")
    except Exception as e:
        print(f"Failed to print image: {e}")
        raise
