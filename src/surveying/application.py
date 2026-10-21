from __future__ import annotations

import ctypes
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from . import __app_name__
from .ui.main_window import MainWindow
from .ui.style import APP_STYLESHEET


def _create_app_icon() -> QIcon:
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#122B3E"))
    painter.drawRoundedRect(QRectF(8, 8, 240, 240), 52, 52)
    painter.setBrush(QColor("#0F766E"))
    painter.drawRoundedRect(QRectF(36, 36, 184, 184), 36, 36)
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Microsoft YaHei UI", 96, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(36, 36, 184, 184), Qt.AlignmentFlag.AlignCenter, "测")
    painter.end()
    return QIcon(pixmap)


def run() -> int:
    if sys.platform == "win32":
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "Surveying.LevelingDataManager.1"
            )
        except (AttributeError, OSError):
            pass

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setOrganizationName("SurveyingTools")
    app.setApplicationVersion("1.0.0")
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setWindowIcon(_create_app_icon())
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    return app.exec()
