"""Orquestra o fluxo completo: checagem de costura -> tratamento de polo
-> conversao via cmft -> exportacao na convencao GoldSrc.

E a unica funcao que a GUI chama; cada etapa continua utilizavel isolada
(scripts, testes) pelos modulos individuais.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .cmft_wrapper import CmftResult, convert_equirect_to_facelist, find_cmft_binary
from .goldsrc_export import export_to_goldsrc
from .pole_treatment import apply_pole_treatment
from .seam_check import SeamReport, check_longitude_seam


@dataclass
class PipelineResult:
    seam_report: SeamReport
    cmft_result: CmftResult
    goldsrc_faces: dict[str, Path]


def run_pipeline(
    input_equirect: Path,
    output_dir: Path,
    sky_name: str,
    face_size: int = 1024,
    apply_pole_fix: bool = True,
    cmft_binary_path: str | Path | None = None,
) -> PipelineResult:
    equirect = Image.open(input_equirect)

    seam_report = check_longitude_seam(equirect)

    if apply_pole_fix:
        equirect = apply_pole_treatment(equirect)

    cmft_binary = find_cmft_binary(cmft_binary_path)

    with tempfile.TemporaryDirectory(prefix="skyforge_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        prepared_input = tmp_path / "prepared_equirect.tga"
        equirect.convert("RGB").save(prepared_input)

        cmft_result = convert_equirect_to_facelist(
            input_tga=prepared_input,
            output_dir=tmp_path / "cmft_out",
            face_size=face_size,
            cmft_binary=cmft_binary,
        )

        goldsrc_faces = export_to_goldsrc(
            cmft_face_paths=cmft_result.face_paths,
            output_dir=output_dir,
            sky_name=sky_name,
        )

    return PipelineResult(
        seam_report=seam_report,
        cmft_result=cmft_result,
        goldsrc_faces=goldsrc_faces,
    )
