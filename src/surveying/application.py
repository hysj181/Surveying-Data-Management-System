from __future__ import annotations

import ctypes
import logging
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from . import __app_name__
from .diagnostics import setup_diagnostics
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


def _create_splash_pixmap() -> QPixmap:
    pixmap = QPixmap(720, 400)
    pixmap.fill(QColor("#F2F6F8"))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(QRectF(26, 26, 668, 348), 20, 20)
    painter.setBrush(QColor("#122B3E"))
    painter.drawRoundedRect(QRectF(54, 62, 104, 104), 24, 24)
    painter.setBrush(QColor("#0F766E"))
    painter.drawRoundedRect(QRectF(72, 80, 68, 68), 16, 16)
    painter.setPen(QColor("#FFFFFF"))
    title_font = QFont("Microsoft YaHei UI", 34, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.drawText(QRectF(72, 80, 68, 68), Qt.AlignmentFlag.AlignCenter, "测")
    painter.setPen(QColor("#17324D"))
    painter.setFont(QFont("Microsoft YaHei UI", 24, QFont.Weight.Bold))
    painter.drawText(QRectF(188, 74, 460, 48), Qt.AlignmentFlag.AlignLeft, "测量数据处理系统")
    painter.setPen(QColor("#607D8B"))
    painter.setFont(QFont("Microsoft YaHei UI", 11))
    painter.drawText(
        QRectF(190, 128, 460, 30),
        Qt.AlignmentFlag.AlignLeft,
        "水准计算 · 误差分析 · 成果导出",
    )
    painter.setPen(QColor("#D5E0E7"))
    painter.drawLine(56, 300, 664, 300)
    painter.setPen(QColor("#0F766E"))
    painter.setFont(QFont("Microsoft YaHei UI", 10, QFont.Weight.DemiBold))
    painter.drawText(QRectF(56, 316, 500, 28), Qt.AlignmentFlag.AlignLeft, "正在加载，请稍候…")
    painter.end()
    return pixmap


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
    app.setApplicationVersion("1.1.0")
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei UI", 10))
    app.setWindowIcon(_create_app_icon())
    app.setStyleSheet(APP_STYLESHEET)

    log_path = setup_diagnostics(app)
    logging.info("Showing splash screen")
    splash = QSplashScreen(_create_splash_pixmap())
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    logging.info("Constructing main window")
    window = MainWindow()
    logging.info("Showing main window")
    window.show()
    splash.finish(window)
    logging.info("Entering event loop; log=%s", log_path)
    return app.exec()
