import subprocess
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image

# --------------------------
# Configuration
# --------------------------
LATEX_FILE = "test.tex"  # your LaTeX source
OUTPUT_DIR = Path("output")
PRINTER_WIDTH_PX = 576  # typical 80mm thermal printer at 203dpi
DPI = 203  # printer resolution

OUTPUT_DIR.mkdir(exist_ok=True)

# --------------------------
# Compile LaTeX to PDF
# --------------------------
def compile_latex_to_pdf(latex_file: str, output_dir: Path) -> Path:
    latex_file = Path(latex_file)
    subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(latex_file)],
        check=True
    )
    pdf_file = output_dir / (latex_file.stem + ".pdf")
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not generated: {pdf_file}")
    return pdf_file

# --------------------------
# Convert PDF to image
# --------------------------
def pdf_to_image(pdf_file: Path, width_px: int, dpi: int) -> list:
    pages = convert_from_path(str(pdf_file), dpi=dpi)
    images = []
    for page in pages:
        ratio = width_px / page.width
        new_height = int(page.height * ratio)
        img = page.resize((width_px, new_height), Image.LANCZOS)
        img = img.convert("1")  # monochrome for ESC/POS
        images.append(img)
    return images

# --------------------------
# Save images
# --------------------------
def save_images(images: list, output_dir: Path, base_name: str):
    for idx, img in enumerate(images):
        output_img_file = output_dir / f"{base_name}_page{idx+1}.png"
        img.save(output_img_file)
        print(f"Saved: {output_img_file}")

# --------------------------
# Main
# --------------------------
def main():
    pdf_file = compile_latex_to_pdf(LATEX_FILE, OUTPUT_DIR)
    images = pdf_to_image(pdf_file, PRINTER_WIDTH_PX, DPI)
    save_images(images, OUTPUT_DIR, pdf_file.stem)

if __name__ == "__main__":
    main()
