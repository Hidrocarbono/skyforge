"""Renomeia a saida do cmft (posx/negx/posy/negy/posz/negz) para a convencao
GoldSrc/PrimeXT (ft/bk/up/dn/rt/lf), aplicando flip/rotacao por face quando
necessario.

STATUS DA VALIDACAO -- LEIA ANTES DE USAR EM PRODUCAO
-------------------------------------------------------
O mapeamento abaixo AINDA E UMA HIPOTESE, nao uma correspondencia
confirmada -- e o resultado de tentar validar isso de duas formas
diferentes ja mostrou por que nenhum atalho sintetico resolve essa pergunta
sozinho:

1. Primeira tentativa: leitura visual de screenshots das 6 faces. Rendeu
   uma conclusao ERRADA (troquei duas imagens parecidas sem perceber).
2. Segunda tentativa: medir a cor RGB dominante de cada face
   programaticamente (mais confiavel que olho humano) e comparar contra a
   formula esferica padrao usada em testpattern.py. Resultado, reproduzido
   identico em 4 combinacoes de resolucao de entrada/face (nao e ruido):
   o eixo Y bate certinho (posy vira a face `up`, negy vira `dn`), mas os
   eixos X/Z NAO batem com a formula esferica ingenua -- o `cmft` usa
   internamente uma convencao de longitude diferente da nossa pra esses
   dois eixos. Ou seja: nem a medicao numerica resolve a pergunta que
   importa (qual direcao fisica = frente/tras/direita/esquerda no jogo),
   ela so prova que testpattern.py e o `cmft` "falam dialetos diferentes"
   de coordenada -- uma informacao util, mas nao a resposta final.

CONCLUSAO: a correspondencia semantica (qual arquivo do cmft deve virar
`ft`/`bk`/`rt`/`lf`) SO pode ser confirmada carregando o resultado de
verdade no jogo (ou pxmv/pxsv) e olhando pra qual direcao cada face
aparece. Nao existe atalho sintetico pra essa etapa -- os eixos up/dn sao
a excecao, esses dois JA estao confirmados (ver ponto 2 acima).

Antes de usar uma saida real do SkyForge no mod:
1. Rode testpattern.py e passe pelo pipeline completo.
2. Carregue o resultado em gfx/env/ e confira NO JOGO (nao por screenshot
   solto -- olhar a textura fora de contexto e exatamente o que causou o
   erro do item 1 acima) se cada face aparece na direcao certa, sem
   espelhamento/rotacao.
3. Ajuste GOLDSRC_FACE_MAPPING e FACE_TRANSFORMS conforme o que a
   validacao em jogo mostrar, e so entao apague este aviso.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

# HIPOTESE para os eixos X/Z (rt/lf/ft/bk), NAO VALIDADA -- ver aviso no
# topo do arquivo. posy->up e negy->dn SAO confirmados (unica parte que a
# medicao programatica conseguiu provar).
GOLDSRC_FACE_MAPPING: dict[str, str] = {
    "posx": "rt",
    "negx": "lf",
    "posz": "bk",
    "negz": "ft",
    "posy": "up",
    "negy": "dn",
}

# Transformacoes por face (aplicadas ANTES de salvar), caso a validacao em
# jogo mostre que alguma face esta espelhada ou rotacionada. Chaves sao o
# sufixo GoldSrc de destino. Valores sao metodos de PIL.Image.transpose ou
# None.
FACE_TRANSFORMS: dict[str, Image.Transpose | None] = {
    "ft": None,
    "bk": None,
    "up": None,
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
    """Copia/transforma as 6 faces do cmft para gfx/env/<sky_name><suffix>.tga.

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
        dst_path = output_dir / f"{sky_name}{goldsrc_suffix}.tga"

        transform = transforms.get(goldsrc_suffix)
        if transform is None:
            shutil.copyfile(src_path, dst_path)
        else:
            img = Image.open(src_path)
            img.transpose(transform).save(dst_path)

        result[goldsrc_suffix] = dst_path

    return result
