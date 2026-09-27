import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skyforge.cmft_wrapper import find_cmft_binary


def test_finds_bundled_binary_when_frozen(tmp_path, monkeypatch):
    """Simula o ambiente de um app empacotado pelo PyInstaller (--onefile):
    sys.frozen=True e sys._MEIPASS apontando pra pasta temporaria onde os
    dados foram descompactados -- o cmft.exe deve ser achado ali sozinho,
    sem precisar de SKYFORGE_CMFT_PATH nem do binario estar no PATH.
    """
    fake_cmft = tmp_path / "cmft.exe"
    fake_cmft.write_bytes(b"fake binary")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    found = find_cmft_binary(explicit_path=None)

    assert found == fake_cmft


def test_explicit_path_takes_priority_over_bundled(tmp_path, monkeypatch):
    bundled = tmp_path / "bundled"
    bundled.mkdir()
    (bundled / "cmft.exe").write_bytes(b"fake bundled")

    explicit = tmp_path / "explicit_cmft.exe"
    explicit.write_bytes(b"fake explicit")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(bundled), raising=False)

    found = find_cmft_binary(explicit_path=explicit)

    assert found == explicit
