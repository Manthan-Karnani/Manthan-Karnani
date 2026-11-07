"""Render the README banner with Pillow: python3 scripts/generate_banner.py."""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, SCALE = 1000, 300, 2
FPS, SECONDS = 20, 12
GREETING = "Hey, I'm Manthan!"
# Brief, irregular brightness dips give the complete greeting a neon flicker.
FLICKERS = [(0.85, 0.10, 0.55), (1.05, 0.05, 0.72), (3.40, 0.10, 0.65),
            (5.80, 0.05, 0.50), (5.95, 0.10, 0.70), (8.30, 0.15, 0.62),
            (10.65, 0.05, 0.55), (10.80, 0.10, 0.75)]


def font(name, size):
    candidates = {
        "sans": ["/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
        "mono": ["/System/Library/Fonts/Supplemental/Courier New Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"],
    }
    for path in candidates[name]:
        if Path(path).exists():
            return ImageFont.truetype(path, size * SCALE)
    raise FileNotFoundError("Install Arial/Courier New or DejaVu Sans/DejaVu Sans Mono.")


SANS, MONO, SMALL, ROLE = font("sans", 18), font("mono", 45), font("sans", 14), font("sans", 21)


def greeting_brightness(time):
    time %= SECONDS
    for start, duration, brightness in FLICKERS:
        if start <= time < start + duration:
            return brightness
    return 0.97 + 0.03 * math.cos(math.tau * time / SECONDS)


def background():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            glow = max(0, 1 - ((x - 500) / 580) ** 2 - ((y - 150) / 260) ** 2)
            pixels[x, y] = (int(5 + 33 * glow), 3, int(3 + 3 * glow))
    image = image.resize((WIDTH * SCALE, HEIGHT * SCALE))
    draw = ImageDraw.Draw(image)
    draw.arc((-150 * SCALE, 230 * SCALE, 340 * SCALE, 380 * SCALE), 195, 315, fill="#70121d", width=SCALE)
    draw.arc((740 * SCALE, -140 * SCALE, 1120 * SCALE, 45 * SCALE), 15, 155, fill="#70121d", width=SCALE)
    heading = "WELCOME TO MY GITHUB"
    widths = [draw.textlength(c, font=SANS) for c in heading]
    x = (WIDTH * SCALE - sum(widths) - 5 * SCALE * (len(heading) - 1)) / 2
    for char, width in zip(heading, widths):
        draw.text((x, 92 * SCALE), char, font=SANS, fill="#ff4b56", anchor="ls")
        x += width + 5 * SCALE
    draw.text((500 * SCALE, 210 * SCALE), "Java Backend", font=ROLE, fill="#ff5b63", anchor="ms")
    draw.text((500 * SCALE, 251 * SCALE), "building things, one commit at a time", font=SMALL, fill="#a58e8e", anchor="ms")
    return image


def leaf_shape():
    # A tapered almond outline has pointed ends instead of a heart's lobes.
    points = []
    for a, b, c, d in [((-22, 0), (-9, -13), (10, -10), (22, 0)),
                       ((22, 0), (9, 12), (-11, 9), (-22, 0))]:
        for step in range(16):
            t, u = step / 15, 1 - step / 15
            points.append((u**3 * a[0] + 3 * u*u*t * b[0] + 3*u*t*t * c[0] + t**3*d[0],
                           u**3 * a[1] + 3 * u*u*t * b[1] + 3*u*t*t * c[1] + t**3*d[1]))
    return points


RNG = random.Random(42)
LEAF_MARGIN = 60
WIND_WIDTH = WIDTH + 2 * LEAF_MARGIN
LEAF_SPACING = WIND_WIDTH / 3
WIND_SPEED = LEAF_SPACING / SECONDS
# Repeating lanes let the breeze move slowly and still loop seamlessly.
LEAF_LANES = [(22 + index * 42, RNG.uniform(.65, 1.0),
               RNG.uniform(0, math.tau), RNG.uniform(0, LEAF_SPACING))
              for index in range(7)]
LEAF = leaf_shape()
BASE = background()


def frame(time):
    image = BASE.copy()
    draw = ImageDraw.Draw(image)
    for index, (y, size, phase, offset) in enumerate(LEAF_LANES):
        for column in range(3):
            cx = (offset + column * LEAF_SPACING + WIND_SPEED * time) % WIND_WIDTH - LEAF_MARGIN
            spatial_phase = phase + math.tau * (cx + LEAF_MARGIN) / WIND_WIDTH
            breeze_phase = phase + math.tau * time / SECONDS
            cy = y + 9 * math.sin(spatial_phase) + 4 * math.sin(breeze_phase)
            angle = -.25 + .22 * math.sin(spatial_phase) + .12 * math.sin(breeze_phase)
            flutter = .8 + .2 * math.sin(breeze_phase + spatial_phase)

            def transform(point):
                px, py = point[0], point[1] * flutter
                return ((cx + size * (px * math.cos(angle) - py * math.sin(angle))) * SCALE,
                        (cy + size * (px * math.sin(angle) + py * math.cos(angle))) * SCALE)

            draw.polygon([transform(point) for point in LEAF],
                         fill=["#e72a3c", "#c5192c", "#ff4753"][index % 3])
            draw.line([transform((-27, 0)), transform((18, 0))], fill="#821323", width=SCALE)
            for vein_x in (-10, -2, 6):
                for side in (-1, 1):
                    draw.line([transform((vein_x - 4, 0)), transform((vein_x + 2, side * 5))],
                              fill="#a51b2d", width=SCALE)
    brightness = greeting_brightness(time)
    text_color = tuple(round(channel * brightness) for channel in (255, 245, 245))
    draw.text((500 * SCALE, 159 * SCALE), GREETING, font=MONO, fill=text_color, anchor="ms")
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main():
    # One shared palette prevents colors from jumping between GIF frames.
    palette = frame(3.5).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [frame(index / FPS).quantize(palette=palette, dither=Image.Dither.NONE)
              for index in range(FPS * SECONDS)]
    output = ROOT / "assets" / "red-black-banner.gif"
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=1000 // FPS,
                   loop=0, disposal=1, optimize=False)
    print(f"Wrote {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes, {len(frames)} frames)")


if __name__ == "__main__":
    main()
