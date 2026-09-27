# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller para o executavel unico "for dummies" do SkyForge.

Empacota main.py + o pacote skyforge + a GUI + o splash.png + um cmft.exe
JA COMPILADO (nao compila ele aqui -- precisa existir em ./cmft.exe antes
de rodar o pyinstaller; ver .github/workflows/build-skyforge-windows.yml
para o fluxo completo automatizado).

Uso local (depois de ter um cmft.exe compilado na raiz do repo):
    pip install -r requirements-build.txt
    pyinstaller --noconfirm build_windows.spec

Resultado: dist/SkyForge.exe -- um unico arquivo, sem instalar Python nem
configurar nada, e sem precisar do SKYFORGE_CMFT_PATH (cmft_wrapper.py
acha o cmft.exe embutido sozinho -- ver _bundled_cmft_dir()).
"""

from pathlib import Path

repo_root = Path(SPECPATH)
cmft_binary = repo_root / "cmft.exe"

if not cmft_binary.is_file():
    raise SystemExit(
        f"cmft.exe nao encontrado em {cmft_binary} -- compile/baixe o binario "
        "e coloque na raiz do repo antes de rodar o pyinstaller (ver README)."
    )

a = Analysis(
    ["main.py"],
    pathex=[str(repo_root / "src"), str(repo_root / "gui")],
    binaries=[(str(cmft_binary), ".")],
    datas=[(str(repo_root / "gui" / "assets" / "splash.png"), "gui/assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SkyForge",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
