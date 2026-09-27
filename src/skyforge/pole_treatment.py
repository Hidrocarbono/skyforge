"""Tratamento de baixa-frequencia para as faixas de zenite/nadir do
panorama equirectangular, ANTES da conversao pelo cmft.

Motivacao (debate completo em docs/DECISOES.md): a projecao equirectangular
diverge nos polos -- uma faixa fina no topo/base da imagem vira uma face
quadrada inteira, entao qualquer ruido de alta frequencia ali produz um
artefato radial ("redemoinho") depois de reprojetado. Ceu real tambem tem
pouco detalhe de alta frequencia bem no zenite (e so gradiente de cor) --
suavizar agressivamente essa faixa nao e gambiarra, e fisicamente plausivel.

Este modulo trabalha no espaco do equirect (antes do cmft), nao na face `up`
quadrada depois -- e mais simples e evita reimplementar a matematica de
reprojecao que o cmft ja faz.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def _band_average_color(arr: np.ndarray, band_px: int, from_top: bool) -> np.ndarray:
    band = arr[:band_px] if from_top else arr[-band_px:]
    return band.reshape(-1, band.shape[-1]).mean(axis=0)


def apply_pole_treatment(
    equirect: Image.Image,
    band_fraction: float = 0.08,
    blend_weight: float = 0.6,
    blur_radius: float = 12.0,
) -> Image.Image:
    """Suaviza as faixas superior/inferior do equirect e mistura com um
    gradiente solido derivado da cor media daquela faixa.

    band_fraction: fracao da altura total tratada como "faixa polar" (topo
        e base, separadamente). Default 8% -- ajustar visualmente por caso.
    blend_weight: 0 = mantem o conteudo original (so desfocado), 1 = vira
        gradiente solido puro. 0.6 e um ponto de partida, nao um valor
        definitivo -- ver item pendente 5 em docs/DECISOES.md.
    blur_radius: raio do blur gaussiano aplicado antes do blend, em pixels.
    """
    arr = np.asarray(equirect.convert("RGBA"), dtype=np.float32)
    height = arr.shape[0]
    band_px = max(1, int(height * band_fraction))

    blurred = np.asarray(
        equirect.convert("RGBA").filter(ImageFilter.GaussianBlur(blur_radius)),
        dtype=np.float32,
    )

    out = arr.copy()
    for from_top in (True, False):
        avg_color = _band_average_color(arr, band_px, from_top)
        sl = slice(0, band_px) if from_top else slice(height - band_px, height)

        band_blurred = blurred[sl]
        band_gradient = np.tile(avg_color, (band_px, arr.shape[1], 1))

        out[sl] = (1.0 - blend_weight) * band_blurred + blend_weight * band_gradient

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGBA")
