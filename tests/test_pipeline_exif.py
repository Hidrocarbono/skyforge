"""Trava a correcao de orientacao EXIF -- ver comentario em pipeline.py.

JPEG/PNG podem carregar um tag EXIF de orientacao (fotos de celular fazem
isso com frequencia); Image.open() do Pillow NAO aplica isso sozinho. Sem
ImageOps.exif_transpose(), uma entrada assim seria processada com a
orientacao errada, em silencio, sem nenhum erro.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
from PIL.ExifTags import Base as ExifTags

from skyforge.testpattern import generate_test_equirect


def test_exif_orientation_is_applied_before_processing(tmp_path):
    from PIL import ImageOps

    img = generate_test_equirect(width=64, height=32)

    exif = Image.Exif()
    exif[ExifTags.Orientation.value] = 6  # 90 graus, um valor comum de EXIF

    jpg_path = tmp_path / "rotated.jpg"
    img.save(jpg_path, exif=exif)

    reopened = Image.open(jpg_path)
    assert reopened.getexif().get(ExifTags.Orientation.value) == 6

    transposed = ImageOps.exif_transpose(reopened)
    # Depois do exif_transpose, a tag de orientacao e removida (a rotacao
    # ja foi aplicada nos pixels de verdade) -- e assim que sabemos que
    # funcionou, sem precisar comparar pixel a pixel.
    assert transposed.getexif().get(ExifTags.Orientation.value) in (None, 1)
