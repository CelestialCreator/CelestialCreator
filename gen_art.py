"""One-shot: regenerate the ART block in update_profile.py from a photo.

Usage: python3 gen_art.py /path/to/photo.jpg [cols] [rows]
Not needed at runtime -- ART is embedded in update_profile.py like Dietrich's.

Needs Pillow + numpy. Only run locally, never in CI.

How the "3D" look is made:
  equalize/autocontrast flatten a face into an outline, so instead we
  1. flood-fill the white studio background from the border -> subject mask
     (a luminance threshold alone would eat the lit side of the face)
  2. mid-radius local contrast -> keeps cheek/brow/nose shading
  3. directional light falloff, applied to the subject only, normalized so the
     lit corner stays at full brightness, then lifted back into the ramp range
  4. rim shadow just inside the silhouette -> separates head from background
"""
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

RAMP = " .:-=+*#%@"
CELL = 7.8 / 15.0  # monospace char width / line height in the SVG


def _blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def _background(a, thr=0.86):
    """1 where bright pixels are reachable from the border (the studio backdrop)."""
    h, w = a.shape
    m = np.zeros((h, w), bool)
    q = deque()
    edges = [(y, x) for y in range(h) for x in (0, w - 1)] + \
            [(y, x) for x in range(w) for y in (0, h - 1)]
    for y, x in edges:
        if a[y, x] > thr and not m[y, x]:
            m[y, x] = True
            q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not m[ny, nx] and a[ny, nx] > thr:
                m[ny, nx] = True
                q.append((ny, nx))
    return m.astype(np.float32)


def art(path, cols=55, rows=36, crop=(0.13, 0.02, 0.87, 0.79),
        soften=2.0, contrast=1.25, light=0.45, lcr=8, lca=0.9,
        rim=0.22, dy=0.30, lift=0.85, thr=0.86):
    im = Image.open(path).convert("L")
    w, h = im.size
    im = im.crop((int(crop[0] * w), int(crop[1] * h), int(crop[2] * w), int(crop[3] * h)))
    im = im.filter(ImageFilter.MedianFilter(5))  # despeckle skin before downscale
    if rows is None:
        rows = max(1, round(cols * (im.size[1] / im.size[0]) * CELL))
    small = im.resize((cols * 4, rows * 4), Image.LANCZOS).filter(ImageFilter.GaussianBlur(soften))
    a0 = np.asarray(small.resize((cols, rows), Image.LANCZOS)).astype(np.float32) / 255.0

    bg = _blur(_background(a0, thr), 0.8)
    if bg.mean() < 0.05:  # no studio backdrop -> nothing to mask, shade the whole frame
        bg = np.zeros_like(a0)

    a = np.clip(a0 + lca * (a0 - _blur(a0, lcr)), 0, 1)      # mid-scale shading
    a = np.clip((a - 0.5) * contrast + 0.5, 0, 1)

    yy, xx = np.mgrid[0:rows, 0:cols].astype(np.float32)
    g = 1.0 - light * ((xx / (cols - 1) + dy * yy / (rows - 1)) / (1 + dy))
    g /= g.max()                                              # lit corner stays 1.0

    # lift the shaded result back into the ramp's range, or the dark half of the
    # frame quantizes to a single '@' row and the volume disappears
    lit = (a * g) ** lift
    if rim:
        lit = lit - rim * np.clip((1 - bg) - _blur(1 - bg, 2.0), 0, 1)
    out = bg + (1 - bg) * lit                                 # backdrop stays pure white

    idx = np.clip(((1 - np.clip(out, 0, 1)) * 10).astype(int), 0, 9)
    return "\n".join("".join(RAMP[i] for i in row).rstrip() for row in idx).strip("\n")


if __name__ == "__main__":
    print(art(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 55,
              int(sys.argv[3]) if len(sys.argv) > 3 else 36))
