from __future__ import annotations

import faulthandler
import logging
import sys
import tempfile
from pathlib import Path
from types import TracebackType

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox


_log_handle = None
_log_path: Path | None = None


def get_log_path() -> Path | None:
    return _log_path


def get_log_directory() -> Path | None:
    return _log_path.parent if _log_path is not None else None


def _open_log_file() -> tuple[object | None, Path | None]:
    candidates: list[Path] = []
    app_data = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppLocalDataLocation
    )
    if app_data:
        candidates.append(Path(app_data) / "logs")
    candidates.append(Path(tempfile.gettempdir()) / "SurveyingDataManager" / "logs")

    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "app.log"
            handle = path.open("a", encoding="utf-8", buffering=1)
            return handle, path
        except OSError:
            continue
    return None, None


def setup_diagnostics(app: QApplication) -> Path | None:
    global _log_handle, _log_path

    _log_handle, _log_path = _open_log_file()
    handlers: list[logging.Handler]
    if _log_handle is not None:
        faulthandler.enable(_log_handle)
        handlers = [logging.StreamHandler(_log_handle)]
    else:
        handlers = [logging.NullHandler()]

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    logging.info("Application starting; Python=%s", sys.version.replace("\n", " "))

    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_tb))
        location = f"\n\n诊断日志：\n{_log_path}" if _log_path is not None else ""
        try:
            QMessageBox.critical(
                None,
                "程序错误",
                f"程序遇到未处理的错误：\n{exc_value}{location}",
            )
        except Exception:
            pass

    sys.excepthook = handle_exception
    return _log_path
