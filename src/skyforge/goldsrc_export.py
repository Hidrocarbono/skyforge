"""Renomeia a saida do cmft (posx/negx/posy/negy/posz/negz) para a convencao
GoldSrc/PrimeXT (ft/bk/up/dn/rt/lf), aplicando flip/rotacao por face quando
necessario.

STATUS DA VALIDACAO -- LEIA ANTES DE USAR EM PRODUCAO
-------------------------------------------------------
O mapeamento de EIXO abaixo (GOLDSRC_FACE_MAPPING) foi validado em jogo de
verdade (PrimeXT, nao so screenshot solto de arquivo): `ft`/`bk`/`rt`/`lf`
fecham sem emenda entre si, confirmando o mapeamento X/Z que antes era so
hipotese. `up` e `dn` (eixo Y) ja tinham confirmacao numerica desde antes
(ver historico em docs/DECISOES.md).

ROTACAO (FACE_TRANSFORMS) -- `up` confirmado, `dn` ainda pendente:
No primeiro teste em jogo, `up` sem transformacao mostrava uma costura
diagonal visivel nas nuvens (o anel ft/bk/rt/lf fechava certo, so a
transicao pra `up` estava errada -- ou seja, era rotacao, nao eixo nem
conteudo). Testado com as 8 variacoes possiveis de orientacao de um
quadrado, `ROTATE_270` foi confirmado em jogo como a correta.

`dn` usa a mesma logica de eixo que `up` e nunca foi testado em jogo
(raramente visivel, coberto por terreno) -- e PROVAVEL que precise da
mesma rotacao ou de uma relacionada, mas isso ainda e hipotese ate
confirmar visualmente. Nao copiar o valor de `up` as cegas.

Antes de confiar num skybox novo gerado pelo SkyForge:
1. Rode o pipeline completo com a foto/panorama real.
2. Carregue em gfx/env/ e confira NO JOGO (nao por screenshot isolado de
   arquivo -- ja causou leitura errada aqui antes) se cada face fecha sem
   costura visivel, principalmente em `dn`, que ainda nao foi validado.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

# Validado em jogo (PrimeXT) -- ver status de validacao no topo do arquivo.
GOLDSRC_FACE_MAPPING: dict[str, str] = {
    "posx": "rt",
    "negx": "lf",
    "posz": "bk",
    "negz": "ft",
    "posy": "up",
    "negy": "dn",
}

# Transformacoes por face (aplicadas ANTES de salvar). Chaves sao o sufixo
# GoldSrc de destino. Valores sao metodos de PIL.Image.transpose ou None.
# `up` confirmado em jogo com ROTATE_270 -- ver status de validacao no topo
# do arquivo. `dn` continua None (hipotese nao testada, nao copiar de `up`
# as cegas).
FACE_TRANSFORMS: dict[str, Image.Transpose | None] = {
    "ft": None,
    "bk": None,
    "up": Image.Transpose.ROTATE_270,
    "dn": None,
    "rt": None,
    "lf": None,
}


def export_to_goldsrc(
    cmft_face_paths: dict[str, Path],
    output_dir: Path,
    sky_name: str,
    mapping: dict[str, str] | None = None,
    transforms: dict[str, Image.Transpose | None] | None = None,
) -> dict[str, Path]:
    """Copia/transforma as 6 faces do cmft para gfx/env/<sky_name>_<suffix>.tga.

    Retorna o mapeamento sufixo GoldSrc -> caminho final, para a GUI exibir
    preview ou a chamada seguinte do pipeline reusar.
    """
    mapping = mapping or GOLDSRC_FACE_MAPPING
    transforms = transforms or FACE_TRANSFORMS

    missing = set(mapping) - set(cmft_face_paths)
    if missing:
        raise ValueError(f"Faces do cmft ausentes para exportar: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Path] = {}

    for cmft_suffix, goldsrc_suffix in mapping.items():
        src_path = cmft_face_paths[cmft_suffix]
        dst_path = output_dir / f"{sky_name}_{goldsrc_suffix}.tga"

        transform = transforms.get(goldsrc_suffix)
        if transform is None:
            shutil.copyfile(src_path, dst_path)
        else:
            img = Image.open(src_path)
            img.transpose(transform).save(dst_path)

        result[goldsrc_suffix] = dst_path

    return result
