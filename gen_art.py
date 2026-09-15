"""One-shot: regenerate the ART block in update_profile.py from a photo.

Usage: python3 gen_art.py /path/to/photo.jpg [cols] [rows]
Not needed at runtime -- ART is embedded in update_profile.py like Dietrich's.
"""
import sys
from PIL import Image, ImageFilter, ImageOps

RAMP = " .:-=+*#%@"
CELL = 7.8 / 15.0  # monospace char width / line height in the SVG


def art(path, cols=55, rows=36, crop=(0.13, 0.02, 0.87, 0.79), gamma=1.0, contrast=1.4):
    im = Image.open(path).convert("L")
    w, h = im.size
    im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    im = im.filter(ImageFilter.MedianFilter(5))  # flatten skin noise before downscale
    w, h = im.size
    if rows is None:
        rows = max(1, round(cols * (h / w) * CELL))
    im = im.resize((cols, rows), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.4))
    im = ImageOps.equalize(im)
    px = im.load()
    out = []
    for y in range(rows):
        line = ""
        for x in range(cols):
            v = px[x, y] / 255.0
            v = min(1.0, max(0.0, (v - 0.5) * contrast + 0.5)) ** gamma
            line += RAMP[min(9, int((1 - v) * 10))]
        out.append(line.rstrip())
    return "\n".join(out).strip("\n")


if __name__ == "__main__":
    print(art(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 56,
              int(sys.argv[3]) if len(sys.argv) > 3 else None))
