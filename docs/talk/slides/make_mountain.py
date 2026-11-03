#!/usr/bin/env python3
"""Renders the deck's mountain: the same 3D terrain as triangles on the left and finished pixels on the right.

usage: python3 make_mountain.py        (needs numpy and Pillow; writes local/visuals/mountain.jpg)

Original artwork for the talk. Nothing here comes from another image.
"""
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'local', 'visuals', 'mountain.jpg')
W, H, SS = 2560, 1440, 2
N = 961
rng = np.random.default_rng(7)


def band(n, freq):
    """Smooth noise around one spatial frequency."""
    fx, fy = np.fft.fftfreq(n)[:, None] * n, np.fft.fftfreq(n)[None, :] * n
    f = np.sqrt(fx * fx + fy * fy)
    field = np.fft.ifft2(np.fft.fft2(rng.standard_normal((n, n))) * np.exp(-((f - freq) / (0.55 * freq)) ** 2)).real
    return field / field.std()


def ridged(n, start, octaves):
    """Sharp ridgelines over broad shoulders, the way real peaks look."""
    total, weight, gain = np.zeros((n, n)), np.ones((n, n)), 1.0
    for o in range(octaves):
        r = (1 - np.abs(band(n, start * 2 ** o)) / 2.4).clip(0, 1) ** 2
        total += r * weight * gain
        weight = np.clip(r * 1.7, 0, 1)
        gain *= 0.52
    return total / 1.9


def terrain():
    x = np.linspace(-1.6, 1.6, N)[None, :]
    z = np.linspace(0, 1, N)[:, None]
    body = ridged(N, 3.2, 7)
    main = np.exp(-((x + 0.32) / 0.55) ** 2) * np.exp(-((z - 0.58) / 0.24) ** 2)
    second = 0.74 * np.exp(-((x - 0.62) / 0.5) ** 2) * np.exp(-((z - 0.7) / 0.22) ** 2)
    low = 0.1 * np.exp(-((z - 0.2) / 0.3) ** 2)
    envelope = main + second + low
    taper = np.clip(z / 0.1, 0, 1)
    return (envelope * (0.46 + 0.66 * body) + 0.035 * body) * taper * taper


def project(x, y, z):
    depth = z + 0.8
    return W * SS / 2 + W * SS * 0.60 * x / depth, H * SS * 1.16 - H * SS * 1.42 * y / depth - H * SS * 0.14 * z


def sky():
    t = np.linspace(0, 1, H * SS)[:, None, None]
    top, low = np.array([24, 58, 112.]), np.array([150, 188, 226.])
    colour = top + (low - top) * np.clip(t / 0.62, 0, 1) ** 1.5
    return Image.fromarray(np.repeat(colour, W * SS, axis=1).astype('uint8'))


def main():
    h = terrain()
    xs = np.linspace(-1.6, 1.6, N)
    zs = np.linspace(0, 2.1, N)
    X, Z = np.meshgrid(xs, zs)
    gz, gx = np.gradient(h, zs, xs)
    normal = np.dstack((-gx * 0.42, np.ones_like(h), -gz * 0.42))
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    sun = np.array([-0.62, 0.55, -0.56])
    sun /= np.linalg.norm(sun)
    light = np.clip((normal * sun).sum(axis=2), 0, 1)
    slope = 1 - normal[:, :, 1]
    speck = band(N, 90)
    snow = np.clip((0.40 - slope + 0.05 * speck) / 0.1, 0, 1)
    rock = np.array([70, 64, 62.]) + 9 * speck[..., None]
    shade = rock * (0.28 + 1.05 * light[..., None])
    lit = np.array([250, 250, 252.])
    dark = np.array([150, 168, 198.])
    white = dark + (lit - dark) * np.clip(light[..., None] * 1.5, 0, 1)
    colour = shade + (white - shade) * snow[..., None]
    sx, sy = project(X, h, Z)

    # Finished pixels, painted from the back to the front.
    shaded = sky()
    draw = ImageDraw.Draw(shaded)
    colour = np.clip(colour, 0, 255).astype(int)
    for i in range(N - 2, -1, -1):
        for j in range(N - 1):
            c = colour[i, j]
            draw.polygon([(sx[i, j], sy[i, j]), (sx[i, j + 1], sy[i, j + 1]), (sx[i + 1, j + 1], sy[i + 1, j + 1]), (sx[i + 1, j], sy[i + 1, j])], fill=(int(c[0]), int(c[1]), int(c[2])))

    # The same terrain as triangles, also from the back to the front, on black.
    wire = Image.new('RGB', (W * SS, H * SS), (6, 7, 9))
    draw = ImageDraw.Draw(wire)
    step = 12
    idx = list(range(0, N, step))
    for a in range(len(idx) - 2, -1, -1):
        i, i2 = idx[a], idx[a + 1]
        for b in range(len(idx) - 1):
            j, j2 = idx[b], idx[b + 1]
            p = [(sx[i, j], sy[i, j]), (sx[i, j2], sy[i, j2]), (sx[i2, j2], sy[i2, j2]), (sx[i2, j], sy[i2, j])]
            hi = min(1, h[i, j] / 0.42)
            line = tuple(int(v) for v in np.array([255, 92, 40]) * (0.5 + 0.5 * hi))
            draw.polygon(p, fill=(6, 7, 9))
            draw.line([p[0], p[1], p[2], p[0], p[3], p[2]], fill=line, width=SS)

    out = Image.new('RGB', (W * SS, H * SS))
    out.paste(wire.crop((0, 0, W * SS // 2, H * SS)), (0, 0))
    out.paste(shaded.crop((W * SS // 2, 0, W * SS, H * SS)), (W * SS // 2, 0))
    out = out.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 50, 2))

    # Darken the top for the title and the bottom for the logo.
    arr = np.asarray(out).astype(float)
    t = np.linspace(0, 1, H)[:, None, None]
    fade = (0.35 + 0.65 * np.clip(t / 0.26, 0, 1)) * (0.08 + 0.92 * np.clip((1 - t) / 0.24, 0, 1))
    out = Image.fromarray((arr * fade).astype('uint8'))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, quality=90, optimize=True)
    print(OUT, os.path.getsize(OUT) // 1024, 'KB')


if __name__ == '__main__':
    main()
