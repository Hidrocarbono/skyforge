"""Gera um panorama equirectangular sintetico com cor + rotulo de texto
distintos por eixo do cubo (+X/-X/+Y/-Y/+Z/-Z).

Objetivo: rodar esse panorama pelo pipeline completo do SkyForge e carregar
o resultado em jogo (gfx/env/) para confirmar visualmente qual sufixo do
cmft (posx/negx/...) corresponde a qual face GoldSrc (ft/bk/up/dn/rt/lf) --
isso e o que falta pra validar GOLDSRC_FACE_MAPPING em goldsrc_export.py.
Ver aviso em goldsrc_export.py.

NOTA DE IMPLEMENTACAO: as cores usam a convencao esferica padrao SEM
nenhuma rotacao -- isso importa de verdade, nao e detalhe cosmetico. Uma
versao anterior deste arquivo rotacionava as proprias cores em 45 graus so
pra tirar o rotulo da costura de wraparound, e isso descolou a paleta da
convencao de eixo que o teste existe pra validar: toda face equatorial saia
com duas cores partidas na diagonal, porque o eixo que o cmft usa
internamente nao tinha essa rotacao. A costura e resolvida do jeito certo
abaixo: gira-se a IMAGEM (nao a definicao de cor) por meia largura soh na
hora de desenhar o texto, desenha-se os rotulos, e gira-se de volta -- um
rotulo que cairia em cima da costura passa a cair no centro da copia
girada, onde da pra desenhar inteiro sem cortar.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Cor distinta por eixo dominante, so pra reconhecimento visual rapido.
AXIS_COLORS = {
    "posx": (220, 60, 60),
    "negx": (60, 220, 60),
    "posy": (60, 60, 220),
    "negy": (220, 220, 60),
    "posz": (220, 60, 220),
    "negz": (60, 220, 220),
}


def generate_test_equirect(width: int = 1024, height: int = 512) -> Image.Image:
    """Gera o equirect colorindo cada pixel pelo eixo dominante da direcao
    3D correspondente aquele (u, v) -- mesma logica de eixo dominante que
    projecoes de cubemap usam, calculada aqui direto por vetor.
    """
    u = np.linspace(0.0, 2.0 * np.pi, width, endpoint=False)
    v = np.linspace(0.0, np.pi, height, endpoint=False)
    uu, vv = np.meshgrid(u, v)

    # Convencao esferica padrao: theta = longitude, phi = colatitude.
    # SEM rotacao -- ver nota no topo do arquivo.
    x = np.sin(vv) * np.cos(uu)
    y = np.cos(vv)
    z = np.sin(vv) * np.sin(uu)

    ax, ay, az = np.abs(x), np.abs(y), np.abs(z)

    axis_key = np.empty((height, width), dtype=object)
    axis_key[(ax >= ay) & (ax >= az) & (x >= 0)] = "posx"
    axis_key[(ax >= ay) & (ax >= az) & (x < 0)] = "negx"
    axis_key[(ay >= ax) & (ay >= az) & (y >= 0)] = "posy"
    axis_key[(ay >= ax) & (ay >= az) & (y < 0)] = "negy"
    axis_key[(az >= ax) & (az >= ay) & (z >= 0)] = "posz"
    axis_key[(az >= ax) & (az >= ay) & (z < 0)] = "negz"

    rgb = np.zeros((height, width, 3), dtype=np.uint8)
    for key, color in AXIS_COLORS.items():
        rgb[axis_key == key] = color

    try:
        font = ImageFont.load_default(size=max(12, height // 20))
    except TypeError:
        font = ImageFont.load_default()

    # Desenha os rotulos numa copia girada por meia largura, pra nenhum
    # rotulo cair em cima da costura (coluna 0 / coluna width-1) -- ver nota
    # no topo do arquivo.
    half = width // 2
    rolled = np.roll(rgb, half, axis=1)
    draw_img = Image.fromarray(rolled, mode="RGB")
    draw = ImageDraw.Draw(draw_img)

    for key in AXIS_COLORS:
        mask = axis_key == key
        if not mask.any():
            continue

        # Longitude usa media circular (atan2 de seno/cosseno medios) por
        # causa do wraparound -- uma media aritmetica simples de angulos
        # perto de 0/2pi da um resultado sem sentido (ex.: media de 359 e 1
        # grau "deveria" ser 0, nao 180).
        mean_sin_u = float(np.sin(uu[mask]).mean())
        mean_cos_u = float(np.cos(uu[mask]).mean())
        centroid_u = np.arctan2(mean_sin_u, mean_cos_u) % (2.0 * np.pi)

        mean_v = float(vv[mask].mean())
        # Afasta o rotulo do polo exato (v=0 ou v=pi) pra continuar legivel
        # apos a reprojecao -- perto do polo a distorcao e maxima.
        pole_margin = 0.15 * np.pi
        mean_v = min(max(mean_v, pole_margin), np.pi - pole_margin)

        px = int((centroid_u / (2.0 * np.pi)) * width)
        py = int((mean_v / np.pi) * height)

        # Mesmo deslocamento de meia largura aplicado a imagem, pra desenhar
        # na posicao equivalente da copia girada.
        px_rolled = (px + half) % width
        draw.text((px_rolled, py), key.upper(), fill=(0, 0, 0), font=font, anchor="mm")

    final = np.roll(np.asarray(draw_img), -half, axis=1)
    return Image.fromarray(final, mode="RGB")


if __name__ == "__main__":
    import sys

    out_path = sys.argv[1] if len(sys.argv) > 1 else "testpattern.tga"
    generate_test_equirect().save(out_path)
    print(f"Padrao de teste salvo em: {out_path}")
