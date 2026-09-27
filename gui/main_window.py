from __future__ import annotations

from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from skyforge.pipeline import PipelineResult, run_pipeline

GOLDSRC_FACE_ORDER = ["up", "ft", "rt", "bk", "lf", "dn"]

# Mantido em sincronia manual com THIRD_PARTY_NOTICES.md na raiz do repo --
# se uma dependencia for adicionada/removida la, atualizar aqui tambem.
ABOUT_TEXT = """\
<h3>SkyForge</h3>
<p>Ferramenta para gerar skyboxes de 6 faces (convencao GoldSrc/Xash3D) a
partir de panoramas equirectangulares.</p>
<p><b>Construido em cima do trabalho de terceiros:</b></p>
<ul>
<li><a href="https://github.com/dariomanesku/cmft">cmft</a> -- Dario Manesku
    (BSD-2-Clause). Motor de reprojecao equirect&rarr;cubemap; o SkyForge
    nao reimplementa essa matematica.</li>
<li><a href="https://pypi.org/project/PySide6/">PySide6</a> -- The Qt
    Company (LGPLv3). Interface grafica.</li>
<li><a href="https://numpy.org/">NumPy</a> -- NumPy Developers
    (BSD-3-Clause).</li>
<li><a href="https://python-pillow.org/">Pillow</a> -- Jeffrey A. Clark e
    colaboradores (HPND).</li>
</ul>
<p>Sucessor espiritual do antigo <b>SkyPaint</b> da comunidade GoldSrc
(inspiracao de fluxo de trabalho, nenhum codigo reaproveitado).</p>
<p>Lista completa de creditos e licencas:
<code>THIRD_PARTY_NOTICES.md</code> no repositorio.</p>
"""


class PipelineWorker(QThread):
    finished_ok = Signal(object)
    finished_error = Signal(str)

    def __init__(self, kwargs: dict):
        super().__init__()
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            result = run_pipeline(**self._kwargs)
            self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001 - reportado na GUI, nao engolido
            self.finished_error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SkyForge")
        self.resize(900, 700)

        self._worker: PipelineWorker | None = None
        self._input_path: Path | None = None

        self._build_ui()
        self._build_menu()

    def _build_menu(self) -> None:
        help_menu = self.menuBar().addMenu("&Ajuda")
        about_action = help_menu.addAction("&Sobre o SkyForge")
        about_action.triggered.connect(self._on_about)

    def _on_about(self) -> None:
        QMessageBox.about(self, "Sobre o SkyForge", ABOUT_TEXT)

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Entrada ---------------------------------------------------
        input_group = QGroupBox("Entrada")
        input_layout = QHBoxLayout(input_group)
        self.input_line = QLineEdit()
        self.input_line.setReadOnly(True)
        browse_btn = QPushButton("Selecionar panorama (.tga)...")
        browse_btn.clicked.connect(self._on_browse_input)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(browse_btn)
        root.addWidget(input_group)

        # --- Parametros --------------------------------------------------
        params_group = QGroupBox("Parametros")
        params_layout = QHBoxLayout(params_group)

        params_layout.addWidget(QLabel("Nome do sky:"))
        self.sky_name_line = QLineEdit("meusky")
        params_layout.addWidget(self.sky_name_line)

        params_layout.addWidget(QLabel("Resolucao por face:"))
        self.face_size_spin = QSpinBox()
        self.face_size_spin.setRange(64, 4096)
        self.face_size_spin.setSingleStep(64)
        self.face_size_spin.setValue(1920)  # default pedido: manter alta resolucao
        params_layout.addWidget(self.face_size_spin)

        self.pole_fix_check = QCheckBox("Tratamento de polo (zenite/nadir)")
        self.pole_fix_check.setChecked(True)
        params_layout.addWidget(self.pole_fix_check)

        root.addWidget(params_group)

        # --- Saida ------------------------------------------------------
        output_group = QGroupBox("Saida")
        output_layout = QHBoxLayout(output_group)
        self.output_line = QLineEdit()
        self.output_line.setReadOnly(True)
        output_browse_btn = QPushButton("Selecionar pasta de saida...")
        output_browse_btn.clicked.connect(self._on_browse_output)
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(output_browse_btn)
        root.addWidget(output_group)

        # --- Acao ---------------------------------------------------------
        self.run_btn = QPushButton("Gerar skybox")
        self.run_btn.clicked.connect(self._on_run)
        root.addWidget(self.run_btn)

        # --- Preview (cross layout simplificado) --------------------------
        preview_group = QGroupBox("Preview das faces")
        preview_layout = QGridLayout(preview_group)
        self.preview_labels: dict[str, QLabel] = {}
        positions = {
            "up": (0, 1), "lf": (1, 0), "ft": (1, 1),
            "rt": (1, 2), "bk": (1, 3), "dn": (2, 1),
        }
        for suffix, (row, col) in positions.items():
            lbl = QLabel(suffix)
            lbl.setFixedSize(96, 96)
            lbl.setStyleSheet("border: 1px solid gray;")
            lbl.setScaledContents(True)
            preview_layout.addWidget(lbl, row, col)
            self.preview_labels[suffix] = lbl
        root.addWidget(preview_group)

        # --- Log ------------------------------------------------------------
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        root.addWidget(self.log_box)

    def _log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

    def _on_browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar panorama equirectangular", "", "TGA (*.tga)"
        )
        if path:
            self._input_path = Path(path)
            self.input_line.setText(path)

    def _on_browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Selecionar pasta de saida")
        if path:
            self.output_line.setText(path)

    def _on_run(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "SkyForge", "Selecione um panorama de entrada primeiro.")
            return
        if not self.output_line.text():
            QMessageBox.warning(self, "SkyForge", "Selecione uma pasta de saida primeiro.")
            return

        self.run_btn.setEnabled(False)
        self._log("Iniciando pipeline...")

        self._worker = PipelineWorker(
            dict(
                input_equirect=self._input_path,
                output_dir=Path(self.output_line.text()),
                sky_name=self.sky_name_line.text().strip(),
                face_size=self.face_size_spin.value(),
                apply_pole_fix=self.pole_fix_check.isChecked(),
            )
        )
        self._worker.finished_ok.connect(self._on_finished_ok)
        self._worker.finished_error.connect(self._on_finished_error)
        self._worker.start()

    def _on_finished_ok(self, result: PipelineResult) -> None:
        self.run_btn.setEnabled(True)
        sr = result.seam_report
        self._log(
            f"Costura de longitude: diff media={sr.mean_abs_diff:.1f} "
            f"(provavelmente visivel: {sr.likely_visible})"
        )
        self._log(f"6 faces exportadas em: {list(result.goldsrc_faces.values())[0].parent}")

        for suffix, path in result.goldsrc_faces.items():
            if suffix in self.preview_labels:
                # QPixmap(path) nao funciona direto -- Qt nao tem plugin de
                # TGA por padrao. Abrir com Pillow e converter e o caminho
                # confiavel.
                pil_img = Image.open(path).convert("RGBA")
                self.preview_labels[suffix].setPixmap(QPixmap.fromImage(ImageQt(pil_img)))

        self._log("Concluido.")

    def _on_finished_error(self, message: str) -> None:
        self.run_btn.setEnabled(True)
        self._log(f"ERRO: {message}")
        QMessageBox.critical(self, "SkyForge", message)
