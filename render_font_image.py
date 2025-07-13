# render_font_image.py

import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from print import print_image

DEFAULT_OUTPUT_PATH = "font_print.png"


def create_text_image(text, font_path, font_size, max_chars_per_line=40, invert=False, rotate=0,
                      padding_top=10, padding_bottom=10, padding_left=10, padding_right=10):
    lines = []
    for paragraph in text.split("\n"):
        lines.extend([paragraph[i:i+max_chars_per_line] for i in range(0, len(paragraph), max_chars_per_line)])

    font = ImageFont.truetype(font_path, font_size)

    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 5  # optional line spacing

    img_height = line_height * len(lines)
    img_width = max(font.getlength(line) for line in lines)

    img = Image.new("L", (int(img_width), int(img_height)), color=255)
    draw = ImageDraw.Draw(img)

    y = 0
    for line in lines:
        draw.text((0, y), line, font=font, fill=0)
        y += line_height

    # Rotate first
    if rotate:
        img = img.rotate(rotate, expand=True)

    # Remap padding based on rotation angle so it visually stays consistent
    def remap_padding(t, r, b, l, rot):
        if rot == 0:
            return t, r, b, l
        elif rot == 90:  # 90° CCW
            return r, b, l, t
        elif rot == 180:
            return b, l, t, r
        elif rot == 270:
            return l, t, r, b
        else:
            return t, r, b, l # no rotation

    pad_top, pad_right, pad_bottom, pad_left = remap_padding(
        padding_top, padding_right, padding_bottom, padding_left, rotate
    )

    new_width = img.width + pad_left + pad_right
    new_height = img.height + pad_top + pad_bottom

    padded_img = Image.new("L", (new_width, new_height), color=255)
    padded_img.paste(img, (pad_left, pad_top))

    if invert:
        padded_img = Image.eval(padded_img, lambda px: 255 - px)

    return padded_img.convert("RGB")



def main():
    parser = argparse.ArgumentParser(description="Render text into an image using a TTF font.")
    parser.add_argument("font", help="Path to the .ttf font file.")
    parser.add_argument("-s", "--font-size", type=int, default=24, help="Font size in points (default: 24).")
    parser.add_argument("-sw", "--scale-width", type=int, help="Percentage of printer width to scale image when printing (1-100).")
    parser.add_argument("-w", "--wrap", type=int, default=40, help="Max characters per line (default: 40).")
    parser.add_argument("-i", "--invert", action="store_true", help="Invert the image (white on black).")
    parser.add_argument("-r", "--rotate", type=int, choices=[0, 90, 180, 270], default=0, help="Rotate image by degrees.")
    parser.add_argument("--pad-top", type=int, default=10, help="Top padding in pixels (default: 10)")
    parser.add_argument("--pad-bottom", type=int, default=10, help="Bottom padding in pixels (default: 10)")
    parser.add_argument("--pad-left", type=int, default=10, help="Left padding in pixels (default: 10)")
    parser.add_argument("--pad-right", type=int, default=10, help="Right padding in pixels (default: 10)")
    parser.add_argument("-o", "--output", type=str, help="Output PNG file path.")
    parser.add_argument("-p", "--print", action="store_true", help="Print the rendered image directly.")

    args = parser.parse_args()

    text = sys.stdin.read().strip()
    if not text:
        print("No input text detected on stdin.")
        sys.exit(1)
        

    img = create_text_image(
        text=text,
        font_path=args.font,
        font_size=args.font_size,
        max_chars_per_line=args.wrap,
        invert=args.invert,
        rotate=args.rotate,
        padding_top=args.pad_top,
        padding_bottom=args.pad_bottom,
        padding_left=args.pad_left,
        padding_right=args.pad_right
    )

    if args.output:
        img.save(args.output)
        print(f"Saved image to {args.output}")
    elif not args.print:
        print(f"No output path provided. Saved to default: {DEFAULT_OUTPUT_PATH}")
        img.save(DEFAULT_OUTPUT_PATH)

    if args.print:
        print_image(image_input=img, cut=True, scale_width_percentage=args.scale_width)


if __name__ == "__main__":
    main()
