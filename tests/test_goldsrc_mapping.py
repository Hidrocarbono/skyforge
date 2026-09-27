"""Testa a integridade da exportacao cmft -> GoldSrc (nenhuma face perdida ou
duplicada), usando o pipeline completo de verdade.

NAO tenta validar QUAL face fisica (frente/tras/etc.) vira QUAL sufixo
GoldSrc -- essa correspondencia semantica so pode ser confirmada carregando
o resultado no jogo (ver aviso grande em goldsrc_export.py). Uma tentativa
anterior de validar isso com um panorama sintetico rotulado (testpattern.py)
descobriu que o `cmft` usa uma convencao de eixo X/Z diferente da formula
esferica ingenua usada aqui para gerar cores -- ver nota em testpattern.py.
Isso quebra a premissa de "cor dominante = eixo esperado" para fins de
validar o mapeamento GoldSrc, entao esse teste automatizado se limita a
checar que a exportacao em si (copia/renomeacao dos 6 arquivos) esta
correta, nao a semantica de orientacao.

Requer um binario cmft compilado -- pula automaticamente se
SKYFORGE_CMFT_PATH nao estiver definido. Ver README para compilar o cmft.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pytest
from PIL import Image

from skyforge.pipeline import run_pipeline
from skyforge.testpattern import AXIS_COLORS, generate_test_equirect

CMFT_PATH = os.environ.get("SKYFORGE_CMFT_PATH")

pytestmark = pytest.mark.skipif(
    not CMFT_PATH, reason="SKYFORGE_CMFT_PATH nao definido -- binario cmft nao disponivel"
)


def _dominant_color(image_path: Path) -> tuple[int, int, int]:
    arr = np.asarray(Image.open(image_path).convert("RGB"))
    pixels = arr.reshape(-1, 3)
    values, counts = np.unique(pixels, axis=0, return_counts=True)
    return tuple(int(c) for c in values[np.argmax(counts)])


def test_all_six_faces_exported_without_loss_or_duplication(tmp_path):
    """As 6 faces exportadas devem ter 6 cores dominantes DISTINTAS entre si
    (uma por eixo do testpattern) -- se duas faces saem com a mesma cor
    dominante, alguma etapa do pipeline esta copiando o arquivo errado ou
    perdendo uma face.
    """
    equirect_path = tmp_path / "testpattern.tga"
    generate_test_equirect(width=256, height=128).save(equirect_path)

    result = run_pipeline(
        input_equirect=equirect_path,
        output_dir=tmp_path / "output",
        sky_name="check",
        face_size=64,
        apply_pole_fix=False,
        cmft_binary_path=CMFT_PATH,
    )

    assert set(result.goldsrc_faces.keys()) == {"ft", "bk", "up", "dn", "rt", "lf"}

    dominant_colors = [_dominant_color(p) for p in result.goldsrc_faces.values()]
    assert len(set(dominant_colors)) == 6, (
        f"Esperava 6 cores dominantes distintas (uma por face), mas achei "
        f"repeticao: {dominant_colors}"
    )

    known_colors = set(AXIS_COLORS.values())
    for color in dominant_colors:
        assert color in known_colors, f"Cor dominante {color} nao e nenhuma das cores do testpattern"
