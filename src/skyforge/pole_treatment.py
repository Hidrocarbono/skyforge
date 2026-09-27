"""Tratamento de baixa-frequencia para as faixas de zenite/nadir do
panorama equirectangular, ANTES da conversao pelo cmft.

Motivacao (debate completo em docs/DECISOES.md): a projecao equirectangular
diverge nos polos -- uma faixa fina no topo/base da imagem vira uma face
quadrada inteira, entao qualquer ruido de alta frequencia ali produz um
artefato radial ("redemoinho") depois de reprojetado. Ceu real tambem tem
pouco detalhe de alta frequencia bem no zenite (e so gradiente de cor) --
suavizar essa faixa nao e gambiarra, e fisicamente plausivel.

ACHADO DE TESTE REAL (ver docs/DECISOES.md): a primeira versao deste modulo
usava uma faixa de largura fixa com corte reto (band_fraction) misturada
com blend_weight constante -- em fotos ja tratadas por IA (que geralmente
JA vem com pouco detalhe de alta frequencia perto do polo, um efeito
colateral positivo do proprio processo de outpainting), isso criava uma
transicao com BORDA DURA que, depois de reprojetada pelo cmft, aparecia
como um disco solido bem visivel no meio da face `up`/`dn` -- um artefato
pior do que a textura original sem tratamento nenhum. A versao atual troca
o corte reto por uma queda suave (smoothstep) que vai a zero exatamente na
borda da faixa, sem descontinuidade -- isso elimina a borda dura, mas o
fato de precisar disso pra nao piorar sugere que, com fontes ja tratadas
por IA, vale considerar comecar com blend_weight mais baixo que o default,
ou desligar o tratamento e comparar antes/depois (a GUI ja tem esse
checkbox) em vez de aplicar cegamente.

Este modulo trabalha no espaco do equirect (antes do cmft), nao na face `up`
quadrada depois -- e mais simples e evita reimplementar a matematica de
reprojecao que o cmft ja faz.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def _smoothstep_falloff(band_px: int) -> np.ndarray:
    """Peso de blend por linha, de blend_weight (no polo, indice 0) ate 0
    (na borda da faixa, indice band_px-1), com derivada zero nas duas
    pontas -- e o que evita a borda dura que virou disco visivel no teste
    real (ver nota no topo do arquivo).
    """
    t = np.linspace(0.0, 1.0, band_px)
    smoothstep = 3 * t**2 - 2 * t**3
    return 1.0 - smoothstep  # 1 no polo -> 0 na borda da faixa


def apply_pole_treatment(
    equirect: Image.Image,
    band_fraction: float = 0.08,
    blend_weight: float = 0.6,
    blur_radius: float = 12.0,
) -> Image.Image:
    """Suaviza as faixas superior/inferior do equirect e mistura com um
    gradiente solido derivado da cor media daquela faixa, com queda suave
    (sem corte reto) do centro do polo ate a borda da faixa tratada.

    band_fraction: fracao da altura total tratada como "faixa polar" (topo
        e base, separadamente). Default 8% -- ajustar visualmente por caso.
    blend_weight: peso MAXIMO do blend, aplicado bem no polo (0 = mantem so
        o blur, sem gradiente solido; 1 = vira gradiente solido puro no
        polo). O peso real cai suavemente a zero na borda da faixa -- ver
        _smoothstep_falloff.
    blur_radius: raio do blur gaussiano aplicado antes do blend, em pixels.
    """
    arr = np.asarray(equirect.convert("RGBA"), dtype=np.float32)
    height, width = arr.shape[:2]
    band_px = max(1, int(height * band_fraction))

    blurred = np.asarray(
        equirect.convert("RGBA").filter(ImageFilter.GaussianBlur(blur_radius)),
        dtype=np.float32,
    )

    falloff = _smoothstep_falloff(band_px) * blend_weight  # (band_px,)

    out = arr.copy()
    for from_top in (True, False):
        sl = slice(0, band_px) if from_top else slice(height - band_px, height)
        band = arr[sl]
        band_blurred = blurred[sl]

        avg_color = band.reshape(-1, band.shape[-1]).mean(axis=0)
        band_gradient = np.tile(avg_color, (band_px, width, 1))

        weight_per_row = falloff if from_top else falloff[::-1]
        weight = weight_per_row[:, None, None]  # (band_px, 1, 1) p/ broadcast

        out[sl] = (1.0 - weight) * band_blurred + weight * band_gradient

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGBA")
