from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from surveying.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_main_window_initial_sample(app) -> None:
    window = MainWindow()
    try:
        assert window.leveling_page.table.rowCount() == 5
        assert window._result is not None
        assert window._result.closure_error_mm == pytest.approx(-8.0)
        assert window.analysis_page.segment_table.rowCount() == 5
        assert window.export_page.status.text() == "成果可导出"
    finally:
        window.close()


def test_new_project_and_calculation_validation(app) -> None:
    window = MainWindow()
    try:
        window._dirty = False
        window.new_project()
        assert window.leveling_page.table.rowCount() == 1
        assert window._result is None
        assert window.leveling_page.collect_project().route_type.value == "闭合"
    finally:
        window.close()


def test_closed_endpoint_is_synced(app) -> None:
    window = MainWindow()
    try:
        window.leveling_page.start_point_edit.setText("BM-X")
        window.leveling_page.start_elevation_spin.setValue(88.5)
        assert window.leveling_page.end_point_edit.text() == "BM-X"
        assert window.leveling_page.end_elevation_spin.value() == pytest.approx(88.5)
        assert not window.leveling_page.end_point_edit.isEnabled()
    finally:
        window._dirty = False
        window.close()
