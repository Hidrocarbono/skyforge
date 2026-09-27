import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "gui"))

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from main_window import MainWindow

SPLASH_PATH = Path(__file__).parent / "gui" / "assets" / "splash.png"
SPLASH_MIN_DURATION_S = 1.2  # evita "piscar" se o carregamento for rapido demais


def main() -> None:
    app = QApplication(sys.argv)

    splash = None
    if SPLASH_PATH.is_file():
        splash = QSplashScreen(QPixmap(str(SPLASH_PATH)))
        splash.show()
        app.processEvents()  # forca o desenho da splash antes do resto carregar

    start = time.monotonic()
    window = MainWindow()

    if splash is not None:
        elapsed = time.monotonic() - start
        remaining = SPLASH_MIN_DURATION_S - elapsed
        if remaining > 0:
            time.sleep(remaining)
        splash.finish(window)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
