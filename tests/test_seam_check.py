import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from PIL import Image

from skyforge.seam_check import check_longitude_seam


def test_identical_edges_report_no_seam():
    arr = np.zeros((16, 32, 3), dtype=np.uint8)
    arr[:, 0, :] = 100
    arr[:, -1, :] = 100  # bordas iguais
    img = Image.fromarray(arr)

    report = check_longitude_seam(img)

    assert report.mean_abs_diff == 0
    assert not report.likely_visible


def test_different_edges_report_seam():
    arr = np.zeros((16, 32, 3), dtype=np.uint8)
    arr[:, 0, :] = 0
    arr[:, -1, :] = 255  # bordas bem diferentes
    img = Image.fromarray(arr)

    report = check_longitude_seam(img)

    assert report.mean_abs_diff == 255
    assert report.likely_visible
