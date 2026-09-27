"""Validacao da costura de longitude do panorama equirectangular de entrada.

A coluna mais a esquerda e a mais a direita do equirect representam o mesmo
meridiano -- se a IA que gerou/tratou o panorama deixou uma emenda visivel
ali, ela vira uma costura vertical continua em uma das faces do cubo depois
da conversao. Este modulo so MEDE e relata; nao corrige automaticamente --
corrigir tentando adivinhar conteudo entra na categoria de "mitigacao
heuristica, nunca garantida" (ver docs/DECISOES.md).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass
class SeamReport:
    mean_abs_diff: float  # 0..255, diferenca media de pixel entre as duas bordas
    max_abs_diff: float
    likely_visible: bool  # heuristica: True se mean_abs_diff acima do limiar


def check_longitude_seam(equirect: Image.Image, visible_threshold: float = 12.0) -> SeamReport:
    """Compara a coluna 0 com a coluna W-1 do equirect.

    visible_threshold: diferenca media de pixel (0..255) acima da qual a
    costura provavelmente aparece a olho nu. 12.0 e um chute inicial -- nao
    calibrado contra percepcao humana real, so serve como primeiro filtro
    automatico antes de revisao manual.
    """
    arr = np.asarray(equirect.convert("RGB"), dtype=np.float32)
    left_col = arr[:, 0, :]
    right_col = arr[:, -1, :]

    diff = np.abs(left_col - right_col)
    mean_diff = float(diff.mean())
    max_diff = float(diff.max())

    return SeamReport(
        mean_abs_diff=mean_diff,
        max_abs_diff=max_diff,
        likely_visible=mean_diff > visible_threshold,
    )
