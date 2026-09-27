#!/usr/bin/env python3
"""gen_splash.py - gera gui/assets/splash.png (tela de carregamento do
SkyForge), mesmo padrao de script reprodutivel usado pelo mod pai
(gen_clouds.py em road-to-nowhere): PIL puro, sem asset externo, resultado
versionado no repo.

Uso: python3 scripts/gen_splash.py
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 800, 450
SEED = 20260927  # fixo: mesma imagem toda vez que se rodar o script

OUT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gui", "assets", "splash.png",
)


def _sky_gradient() -> Image.Image:
    """Gradiente vertical escuro (tempestuoso), coerente com os panoramas
    que ja testamos no projeto."""
    top = (18, 20, 28)
    mid = (48, 46, 52)
    bottom = (74, 66, 60)

    img = Image.new("RGB", (WIDTH, HEIGHT))
    px = img.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        if t < 0.6:
            local_t = t / 0.6
            c = tuple(int(top[i] + (mid[i] - top[i]) * local_t) for i in range(3))
        else:
            local_t = (t - 0.6) / 0.4
            c = tuple(int(mid[i] + (bottom[i] - mid[i]) * local_t) for i in range(3))
        for x in range(WIDTH):
            px[x, y] = c
    return img


def _add_clouds(img: Image.Image, rng: random.Random) -> None:
    """Nuvens simples (blobs suaves), so pra dar atmosfera -- mesma tecnica
    de blob do gen_clouds.py do mod, simplificada."""
    cloud_layer = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(cloud_layer)

    for _ in range(14):
        cx = rng.uniform(0, WIDTH)
        cy = rng.uniform(0, HEIGHT * 0.5)
        for _ in range(rng.randint(5, 9)):
            ox = rng.uniform(-60, 60)
            oy = rng.uniform(-25, 25)
            r = rng.uniform(30, 70)
            alpha = rng.randint(30, 70)
            draw.ellipse(
                [cx + ox - r, cy + oy - r * 0.5, cx + ox + r, cy + oy + r * 0.5],
                fill=alpha,
            )

    cloud_layer = cloud_layer.filter(ImageFilter.GaussianBlur(18))
    cloud_rgb = Image.new("RGB", (WIDTH, HEIGHT), (90, 88, 92))
    img.paste(cloud_rgb, (0, 0), cloud_layer)


def _add_horizon_glow(img: Image.Image) -> None:
    """Um brilho suave no horizonte, como sol atras de nuvem -- mesmo
    elemento visual dos panoramas de teste do projeto."""
    glow = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(glow)
    cx, cy = WIDTH * 0.5, HEIGHT * 0.42
    for r in range(140, 0, -4):
        alpha = int(35 * (1 - r / 140))
        draw.ellipse([cx - r, cy - r * 0.4, cx + r, cy + r * 0.4], fill=alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    glow_rgb = Image.new("RGB", (WIDTH, HEIGHT), (210, 190, 150))
    img.paste(glow_rgb, (0, 0), glow)


def _add_silhouette_hills(img: Image.Image, rng: random.Random) -> None:
    """Silhueta de montanhas na base, ancorando a composicao."""
    draw = ImageDraw.Draw(img)
    base_y = HEIGHT * 0.72
    points = [(0, HEIGHT)]
    x = 0
    y = base_y
    while x < WIDTH:
        x += rng.uniform(40, 90)
        y = base_y + rng.uniform(-35, 35)
        points.append((min(x, WIDTH), y))
    points.append((WIDTH, HEIGHT))
    draw.polygon(points, fill=(12, 12, 14))


def _add_title(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.load_default(size=64)
        subtitle_font = ImageFont.load_default(size=20)
    except TypeError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    title = "SkyForge"
    subtitle = "gerando skyboxes para PrimeXT / Xash3D"

    # sombra leve por baixo do titulo, pra legibilidade sobre o ceu
    draw.text((WIDTH / 2 + 2, HEIGHT * 0.56 + 2), title, font=title_font,
              fill=(0, 0, 0), anchor="mm")
    draw.text((WIDTH / 2, HEIGHT * 0.56), title, font=title_font,
              fill=(235, 230, 215), anchor="mm")

    draw.text((WIDTH / 2 + 1, HEIGHT * 0.68 + 1), subtitle, font=subtitle_font,
               fill=(0, 0, 0), anchor="mm")
    draw.text((WIDTH / 2, HEIGHT * 0.68), subtitle, font=subtitle_font,
               fill=(200, 195, 185), anchor="mm")


def main() -> None:
    rng = random.Random(SEED)

    img = _sky_gradient()
    _add_horizon_glow(img)
    _add_clouds(img, rng)
    _add_silhouette_hills(img, rng)
    _add_title(img)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    print(f"{OUT}: {WIDTH}x{HEIGHT}")


if __name__ == "__main__":
    main()
