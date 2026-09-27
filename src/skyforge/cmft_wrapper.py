"""Wrapper fino em cima do binario cmft (https://github.com/dariomanesku/cmft).

Sintaxe confirmada empiricamente (compilando e rodando o binario, nao so lendo
a documentacao -- a doc do projeto nao mostra --outputType/--outputFormat
separados, que seria a leitura ingenua; a sintaxe real agrupa tudo em
--output0params):

    cmft --input <panorama.tga> \
         --filter none \
         --srcFaceSize <N> --dstFaceSize <N> \
         --output0 <caminho_sem_extensao> \
         --output0params tga,bgra8,facelist

Saida real (testada): 6 arquivos <caminho>_posx.tga, _negx, _posy, _negy,
_posz, _negz -- essa nomeacao NAO e a convencao GoldSrc (ft/bk/up/dn/rt/lf),
por isso existe goldsrc_export.py.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Ordem fixa em que o cmft grava as faces do facelist -- vem de
# s_cubemapFaceIdStr em external/cmft/src/cmft/image.cpp, nao mude sem
# reconferir contra aquele arquivo se o cmft for atualizado.
CMFT_FACE_SUFFIXES = ("posx", "negx", "posy", "negy", "posz", "negz")


class CmftError(RuntimeError):
    pass


@dataclass
class CmftResult:
    face_paths: dict[str, Path]  # ex.: {"posx": Path(...), ...}
    stdout: str


def find_cmft_binary(explicit_path: str | Path | None = None) -> Path:
    """Localiza o binario cmft_cli.

    O alvo de build se chama `cmft_cli` no Makefile/genie, mas o binario
    gerado e nomeado `cmftRelease`/`cmftDebug` (config do genie, nao erro de
    empacotamento -- ver README).
    """
    if explicit_path:
        p = Path(explicit_path)
        if not p.is_file():
            raise CmftError(f"Binario do cmft nao encontrado em: {p}")
        return p

    found = shutil.which("cmft") or shutil.which("cmftRelease") or shutil.which("cmft_cli")
    if found:
        return Path(found)

    raise CmftError(
        "Binario do cmft nao encontrado. Compile external/cmft (ver README) "
        "e informe o caminho explicitamente, ou defina SKYFORGE_CMFT_PATH."
    )


def convert_equirect_to_facelist(
    input_tga: Path,
    output_dir: Path,
    face_size: int,
    cmft_binary: Path,
    output_basename: str = "sky",
) -> CmftResult:
    """Roda o cmft convertendo um panorama equirectangular TGA em 6 faces TGA.

    Nao faz nenhum tratamento de conteudo (polo/costura) -- isso e
    responsabilidade de pole_treatment.py e seam_check.py, chamados antes
    (checagem) ou depois (tratamento) desta conversao.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_prefix = output_dir / output_basename

    cmd = [
        str(cmft_binary),
        "--input", str(input_tga),
        "--filter", "none",
        "--srcFaceSize", str(face_size),
        "--dstFaceSize", str(face_size),
        "--output0", str(output_prefix),
        "--output0params", "tga,bgra8,facelist",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise CmftError(
            f"cmft terminou com codigo {proc.returncode}.\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )

    face_paths: dict[str, Path] = {}
    for suffix in CMFT_FACE_SUFFIXES:
        face_path = output_dir / f"{output_basename}_{suffix}.tga"
        if not face_path.is_file():
            raise CmftError(
                f"cmft reportou sucesso mas o arquivo esperado nao existe: {face_path}\n"
                f"stdout: {proc.stdout}"
            )
        face_paths[suffix] = face_path

    return CmftResult(face_paths=face_paths, stdout=proc.stdout)
