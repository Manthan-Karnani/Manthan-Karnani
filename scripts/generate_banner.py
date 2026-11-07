"""Render the README banner with Pillow: python3 scripts/generate_banner.py."""

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT, SCALE = 1000, 300, 2
FPS, SECONDS = 20, 8
GREETING = "Hey, I'm Manthan!"
TYPE_START, LETTER_TIME, HOLD_TIME, ERASE_TIME = 0.3, 0.18, 2.4, 0.09


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


def visible_characters(time):
    typed_at = TYPE_START + len(GREETING) * LETTER_TIME
    erase_at = typed_at + HOLD_TIME
    if time < TYPE_START:
        return 0
    if time < typed_at:
        return min(len(GREETING), int((time - TYPE_START) / LETTER_TIME))
    if time < erase_at:
        return len(GREETING)
    return max(0, len(GREETING) - int((time - erase_at) / ERASE_TIME))


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


def petal_shape():
    points = []
    for a, b, c, d in [((0, 0), (-12, -13), (-17, -2), (0, 12)), ((0, 12), (17, -2), (12, -13), (0, 0))]:
        for step in range(16):
            t, u = step / 15, 1 - step / 15
            points.append((u**3 * a[0] + 3 * u*u*t * b[0] + 3*u*t*t * c[0] + t**3*d[0],
                           u**3 * a[1] + 3 * u*u*t * b[1] + 3*u*t*t * c[1] + t**3*d[1]))
    return points


RNG = random.Random(42)
PETALS = [(RNG.uniform(0, WIDTH), RNG.uniform(0, HEIGHT + 40), RNG.uniform(.35, .8), RNG.uniform(0, math.tau)) for _ in range(28)]
PETAL = petal_shape()
BASE = background()


def frame(time):
    image = BASE.copy()
    draw = ImageDraw.Draw(image)
    for index, (x, y, size, phase) in enumerate(PETALS):
        angle = phase + time / SECONDS * math.tau
        cx = x + 22 * math.sin(angle)
        cy = (y + time / SECONDS * (HEIGHT + 40)) % (HEIGHT + 40) - 20
        points = [((cx + size * (px * math.cos(angle) - py * math.sin(angle))) * SCALE,
                   (cy + size * (px * math.sin(angle) + py * math.cos(angle))) * SCALE) for px, py in PETAL]
        draw.polygon(points, fill=["#e72a3c", "#c5192c", "#ff4753"][index % 3])
    count = visible_characters(time)
    # Fixed character cells keep the greeting and caret stationary as letters appear.
    for index, char in enumerate(GREETING[:count]):
        draw.text(((270 + index * 27) * SCALE, 159 * SCALE), char, font=MONO, fill="#fff5f5", anchor="ls")
    if time % .8 < .4:
        x = (270 + count * 27) * SCALE
        draw.rectangle((x, 121 * SCALE, x + 2 * SCALE, 165 * SCALE), fill="#ff4753")
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def main():
    # One shared palette prevents colors from jumping between GIF frames.
    palette = frame(3.5).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    frames = [frame(index / FPS).quantize(palette=palette, dither=Image.Dither.NONE)
              for index in range(FPS * SECONDS)]
    output = ROOT / "assets" / "red-black-typing.gif"
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=1000 // FPS,
                   loop=0, disposal=1, optimize=False)
    print(f"Wrote {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes, {len(frames)} frames)")


if __name__ == "__main__":
    main()
