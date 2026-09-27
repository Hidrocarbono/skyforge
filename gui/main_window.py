from __future__ import annotations

from pathlib import Path

from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtGui import QActionGroup, QPixmap
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
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from i18n import DEFAULT_LANGUAGE, LANGUAGES, tr
from skyforge import __version__
from skyforge.pipeline import PipelineResult, run_pipeline

GOLDSRC_FACE_ORDER = ["up", "ft", "rt", "bk", "lf", "dn"]


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
        self.resize(900, 700)

        self._settings = QSettings("Hidrocarbono", "SkyForge")
        self._lang = self._settings.value("language", DEFAULT_LANGUAGE)
        if self._lang not in LANGUAGES:
            self._lang = DEFAULT_LANGUAGE

        self._worker: PipelineWorker | None = None
        self._input_path: Path | None = None

        self._build_ui()
        self._build_menu()
        self.retranslate()

    def tr_(self, key: str, **kwargs) -> str:
        return tr(self._lang, key, **kwargs)

    # --- Menu -------------------------------------------------------------

    def _build_menu(self) -> None:
        self._help_menu = self.menuBar().addMenu("")
        self._about_action = self._help_menu.addAction("")
        self._about_action.triggered.connect(self._on_about)

        self._lang_menu = self.menuBar().addMenu("")
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        self._lang_actions = {}
        for code, label in LANGUAGES.items():
            action = self._lang_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(code == self._lang)
            action.triggered.connect(lambda checked, c=code: self._on_change_language(c))
            lang_group.addAction(action)
            self._lang_actions[code] = action

    def _on_change_language(self, code: str) -> None:
        self._lang = code
        self._settings.setValue("language", code)
        self.retranslate()

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            self.tr_("menu_about"),
            self.tr_("about_html", version=f"v{__version__}"),
        )

    # --- UI -----------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Entrada ---------------------------------------------------
        self.input_group = QGroupBox()
        input_layout = QHBoxLayout(self.input_group)
        self.input_line = QLineEdit()
        self.input_line.setReadOnly(True)
        self.browse_input_btn = QPushButton()
        self.browse_input_btn.clicked.connect(self._on_browse_input)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.browse_input_btn)
        root.addWidget(self.input_group)

        # --- Parametros --------------------------------------------------
        self.params_group = QGroupBox()
        params_layout = QHBoxLayout(self.params_group)

        self.sky_name_label = QLabel()
        params_layout.addWidget(self.sky_name_label)
        self.sky_name_line = QLineEdit("meusky")
        params_layout.addWidget(self.sky_name_line)

        self.face_size_label = QLabel()
        params_layout.addWidget(self.face_size_label)
        self.face_size_spin = QSpinBox()
        self.face_size_spin.setRange(64, 4096)
        self.face_size_spin.setSingleStep(64)
        self.face_size_spin.setValue(1920)  # default pedido: manter alta resolucao
        params_layout.addWidget(self.face_size_spin)

        self.pole_fix_check = QCheckBox()
        self.pole_fix_check.setChecked(True)
        params_layout.addWidget(self.pole_fix_check)

        root.addWidget(self.params_group)

        # --- Saida ------------------------------------------------------
        self.output_group = QGroupBox()
        output_layout = QHBoxLayout(self.output_group)
        self.output_line = QLineEdit()
        self.output_line.setReadOnly(True)
        self.browse_output_btn = QPushButton()
        self.browse_output_btn.clicked.connect(self._on_browse_output)
        output_layout.addWidget(self.output_line)
        output_layout.addWidget(self.browse_output_btn)
        root.addWidget(self.output_group)

        # --- Acao ---------------------------------------------------------
        self.run_btn = QPushButton()
        self.run_btn.clicked.connect(self._on_run)
        root.addWidget(self.run_btn)

        # Indeterminada (range 0,0) -- o cmft roda como processo unico sem
        # progresso granular facil de medir; serve so pra avisar "ainda
        # trabalhando", nao "quanto falta".
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        root.addWidget(self.progress_bar)

        # --- Preview (cross layout simplificado) --------------------------
        self.preview_group = QGroupBox()
        preview_layout = QGridLayout(self.preview_group)
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
        root.addWidget(self.preview_group)

        # --- Log ------------------------------------------------------------
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        root.addWidget(self.log_box)

    def retranslate(self) -> None:
        """Reaplica todos os textos visiveis no idioma atual (self._lang).
        Chamado no __init__ e sempre que o usuario troca de idioma no menu.
        """
        self.setWindowTitle(self.tr_("window_title"))

        self._help_menu.setTitle(self.tr_("menu_help"))
        self._about_action.setText(self.tr_("menu_about"))
        self._lang_menu.setTitle(self.tr_("menu_language"))

        self.input_group.setTitle(self.tr_("group_input"))
        self.browse_input_btn.setText(self.tr_("browse_input"))

        self.params_group.setTitle(self.tr_("group_params"))
        self.sky_name_label.setText(self.tr_("label_sky_name"))
        self.face_size_label.setText(self.tr_("label_face_size"))
        self.pole_fix_check.setText(self.tr_("check_pole_fix"))

        self.output_group.setTitle(self.tr_("group_output"))
        self.browse_output_btn.setText(self.tr_("browse_output"))

        self.run_btn.setText(self.tr_("run_button"))
        self.preview_group.setTitle(self.tr_("group_preview"))

    def _log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

    def _on_browse_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr_("dialog_select_input"),
            "",
            self.tr_("file_filter_input"),
        )
        if path:
            self._input_path = Path(path)
            self.input_line.setText(path)

    def _on_browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, self.tr_("dialog_select_output"))
        if path:
            self.output_line.setText(path)

    def _on_run(self) -> None:
        if not self._input_path:
            QMessageBox.warning(self, "SkyForge", self.tr_("warn_no_input"))
            return
        if not self.output_line.text():
            QMessageBox.warning(self, "SkyForge", self.tr_("warn_no_output"))
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self._log(self.tr_("log_starting"))

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
        self.progress_bar.setVisible(False)
        sr = result.seam_report
        self._log(self.tr_("log_seam", diff=sr.mean_abs_diff, visible=sr.likely_visible))
        self._log(
            self.tr_("log_exported", path=list(result.goldsrc_faces.values())[0].parent)
        )

        for suffix, path in result.goldsrc_faces.items():
            if suffix in self.preview_labels:
                # QPixmap(path) nao funciona direto -- Qt nao tem plugin de
                # TGA por padrao. Abrir com Pillow e converter e o caminho
                # confiavel.
                pil_img = Image.open(path).convert("RGBA")
                self.preview_labels[suffix].setPixmap(QPixmap.fromImage(ImageQt(pil_img)))

        self._log(self.tr_("log_done"))

    def _on_finished_error(self, message: str) -> None:
        self.run_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._log(self.tr_("log_error", message=message))
        QMessageBox.critical(self, "SkyForge", message)
