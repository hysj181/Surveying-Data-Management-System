from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from surveying import __version__
from surveying.domain.error_analysis import ObservationStats, parse_observation_text
from surveying.domain.leveling import LevelingResult, calculate_leveling
from surveying.domain.models import DomainError, LevelingProject
from surveying.services.exporters import ExportError, ResultExporter
from surveying.services.project_io import ProjectSession, ProjectStorage
from surveying.services.samples import (
    create_sample_project,
    sample_observation_target,
    sample_observation_text,
)

from .analysis_page import AnalysisPage
from .export_page import ExportPage
from .leveling_page import LevelingPage


PAGE_META = [
    ("数据输入与计算", "录入工程信息与测段观测值，按距离比例分配闭合差。"),
    ("误差分析", "查看闭合差评定结果，并对重复观测列进行精度与粗差分析。"),
    ("成果导出", "将当前成果导出为 CSV、Excel 或保存为工程文件。"),
]


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self._project: LevelingProject | None = None
        self._result: LevelingResult | None = None
        self._stats: ObservationStats | None = None
        self._session_path: Path | None = None
        self._last_export_dir: Path | None = None
        self._dirty = False
        self._build_actions()
        self._build_ui()
        self._connect_signals()
        self._load_initial_sample()
        self._switch_page(0)

    def _build_actions(self) -> None:
        self.new_action = QAction("新建工程", self)
        self.new_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_action.triggered.connect(self.new_project)

        self.open_action = QAction("打开工程…", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.triggered.connect(self.open_project)

        self.save_action = QAction("保存工程", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.triggered.connect(self.save_project)

        self.save_as_action = QAction("另存为…", self)
        self.save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.save_as_action.triggered.connect(self.save_project_as)

        self.export_csv_action = QAction("导出 CSV…", self)
        self.export_csv_action.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self.export_csv_action.triggered.connect(self.export_csv)

        self.export_excel_action = QAction("导出 Excel…", self)
        self.export_excel_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
        self.export_excel_action.triggered.connect(self.export_excel)

        self.exit_action = QAction("退出", self)
        self.exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        self.exit_action.triggered.connect(self.close)

        self.about_action = QAction("关于", self)
        self.about_action.triggered.connect(self._show_about)

        file_menu = self.menuBar().addMenu("文件")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.export_csv_action)
        file_menu.addAction(self.export_excel_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        help_menu = self.menuBar().addMenu("帮助")
        help_menu.addAction(self.about_action)

    def _build_ui(self) -> None:
        self.setWindowTitle("测量数据管理系统")
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(1380, available.width() - 60)
            height = min(900, available.height() - 80)
            self.resize(max(width, 1220), max(height, 720))
        else:
            self.resize(1360, 860)
        self.setMinimumSize(1220, 720)

        root = QWidget()
        root.setObjectName("Root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_sidebar())

        page_host = QWidget()
        page_host.setObjectName("PageHost")
        host_layout = QVBoxLayout(page_host)
        host_layout.setContentsMargins(26, 20, 26, 16)
        host_layout.setSpacing(14)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        self.page_title = QLabel(PAGE_META[0][0])
        self.page_title.setObjectName("PageTitle")
        self.page_subtitle = QLabel(PAGE_META[0][1])
        self.page_subtitle.setObjectName("PageSubtitle")
        title_block.addWidget(self.page_title)
        title_block.addWidget(self.page_subtitle)
        header.addLayout(title_block)
        header.addStretch(1)
        self.project_chip = QLabel("等待计算")
        self.project_chip.setObjectName("ProjectChip")
        self.project_chip.setProperty("tone", "neutral")
        self.open_header_button = QPushButton("打开")
        self.open_header_button.setObjectName("GhostButton")
        self.save_header_button = QPushButton("保存")
        self.save_header_button.setObjectName("GhostButton")
        self.open_header_button.clicked.connect(self.open_project)
        self.save_header_button.clicked.connect(self.save_project)
        header.addWidget(self.project_chip)
        header.addSpacing(6)
        header.addWidget(self.open_header_button)
        header.addWidget(self.save_header_button)
        host_layout.addLayout(header)

        self.stack = QStackedWidget()
        self.leveling_page = LevelingPage()
        self.analysis_page = AnalysisPage()
        self.export_page = ExportPage()
        self.stack.addWidget(self._scroll_wrap(self.leveling_page))
        self.stack.addWidget(self._scroll_wrap(self.analysis_page))
        self.stack.addWidget(self._scroll_wrap(self.export_page))
        host_layout.addWidget(self.stack, 1)
        root_layout.addWidget(page_host, 1)
        self.setCentralWidget(root)

        self.statusBar().showMessage("就绪")
        self.path_status = QLabel("未保存工程")
        self.statusBar().addPermanentWidget(self.path_status)
        self._update_window_title()

    @staticmethod
    def _scroll_wrap(page: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setObjectName("PageScroll")
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        area.setWidget(page)
        area.viewport().setAutoFillBackground(False)
        return area

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(232)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 24, 18, 20)
        layout.setSpacing(8)

        brand_mark = QLabel("SURVEYING DATA")
        brand_mark.setObjectName("BrandMark")
        brand_title = QLabel("测量数据处理")
        brand_title.setObjectName("BrandTitle")
        brand_subtitle = QLabel("水准计算 · 误差分析 · 成果导出")
        brand_subtitle.setObjectName("BrandSubtitle")
        layout.addWidget(brand_mark)
        layout.addWidget(brand_title)
        layout.addWidget(brand_subtitle)
        layout.addSpacing(22)

        divider = QFrame()
        divider.setObjectName("SidebarDivider")
        layout.addWidget(divider)
        layout.addSpacing(12)

        section = QLabel("工作台")
        section.setObjectName("SidebarSection")
        layout.addWidget(section)
        layout.addSpacing(2)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons: list[QPushButton] = []
        for index, (title, _subtitle) in enumerate(PAGE_META):
            button = QPushButton(f"{index + 1:02d}   {title}")
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(button, index)
            layout.addWidget(button)
            self.nav_buttons.append(button)

        layout.addStretch(1)
        divider_bottom = QFrame()
        divider_bottom.setObjectName("SidebarDivider")
        layout.addWidget(divider_bottom)
        layout.addSpacing(10)
        footer = QLabel("PySide6 桌面版")
        footer.setObjectName("SidebarFooter")
        version = QLabel(f"Version {__version__}")
        version.setObjectName("SidebarFooter")
        layout.addWidget(footer)
        layout.addWidget(version)
        return sidebar

    def _connect_signals(self) -> None:
        self.nav_group.idClicked.connect(self._switch_page)
        self.leveling_page.calculate_requested.connect(self._calculate)
        self.leveling_page.result_invalidated.connect(self._invalidate_result)
        self.leveling_page.content_changed.connect(self._mark_dirty)
        self.analysis_page.content_changed.connect(self._on_analysis_content_changed)
        self.analysis_page.analysis_completed.connect(self._on_analysis_completed)
        self.export_page.export_csv_requested.connect(self.export_csv)
        self.export_page.export_excel_requested.connect(self.export_excel)
        self.export_page.save_project_requested.connect(self.save_project)
        self.export_page.open_project_requested.connect(self.open_project)

    def _load_initial_sample(self) -> None:
        project = create_sample_project()
        self.leveling_page.set_project(project)
        self._calculate(show_warning=False)
        values = parse_observation_text(sample_observation_text())
        self.analysis_page.set_observation_data(values, sample_observation_target())
        self._session_path = None
        self._dirty = False
        self._update_window_title()
        self.path_status.setText("示例工程 · 尚未保存")

    def _switch_page(self, index: int) -> None:
        if 0 <= index < len(PAGE_META):
            self.stack.setCurrentIndex(index)
            self.nav_buttons[index].setChecked(True)
            self.page_title.setText(PAGE_META[index][0])
            self.page_subtitle.setText(PAGE_META[index][1])

    def _calculate(self, show_warning: bool = True):
        try:
            project = self.leveling_page.collect_project()
            result = calculate_leveling(project)
        except DomainError as exc:
            self._invalidate_result()
            if show_warning:
                QMessageBox.warning(self, "无法计算", str(exc))
            return None
        except Exception as exc:
            self._invalidate_result()
            if show_warning:
                QMessageBox.critical(self, "计算错误", f"计算过程中发生错误：{exc}")
            return None

        self.leveling_page.show_result(result)
        self._project = project
        self._result = result
        self.analysis_page.set_result(project, result)
        self.export_page.set_result(project, result)
        self._update_project_chip()
        self._update_export_observation_count()
        self.statusBar().showMessage(
            f"计算完成：闭合差 {result.closure_error_mm:+.2f} mm，"
            f"容许 ±{result.allowable_closure_mm:.2f} mm"
        )
        if show_warning and not result.is_within_tolerance:
            QMessageBox.warning(
                self,
                "闭合差超限",
                "闭合差超过容许值，计算仍已完成，但成果不应直接用于生产。\n\n"
                + "\n".join(result.warnings),
            )
        return project, result

    def _invalidate_result(self) -> None:
        self._result = None
        self._project = None
        self.analysis_page.clear_closure()
        self.export_page.clear_result()
        self.project_chip.setText("数据已修改 · 待重新计算")
        self.project_chip.setProperty("tone", "neutral")
        self.project_chip.style().unpolish(self.project_chip)
        self.project_chip.style().polish(self.project_chip)
        self.statusBar().showMessage("数据已修改，请重新执行计算。")

    def _update_project_chip(self) -> None:
        if self._result is None:
            self.project_chip.setText("等待计算")
            tone = "neutral"
        else:
            self.project_chip.setText(
                f"{self._result.project_name} · {self._result.grade} · "
                f"{self._result.quality_level.value}"
            )
            tone = "success" if self._result.is_within_tolerance else "danger"
        self.project_chip.setProperty("tone", tone)
        self.project_chip.style().unpolish(self.project_chip)
        self.project_chip.style().polish(self.project_chip)

    def _on_analysis_completed(
        self,
        stats: ObservationStats,
        _values: list[float],
        _target: float | None,
    ) -> None:
        self._stats = stats
        self.export_page.set_observation_count(stats.count)
        self._mark_dirty()

    def _on_analysis_content_changed(self) -> None:
        stats = self.analysis_page.current_stats()
        self.export_page.set_observation_count(stats.count if stats else None)
        self._mark_dirty()

    def _update_export_observation_count(self) -> None:
        stats = self.analysis_page.current_stats()
        self.export_page.set_observation_count(stats.count if stats else None)

    def _mark_dirty(self, *_args) -> None:
        if not self._dirty:
            self._dirty = True
            self._update_window_title()

    def _update_window_title(self) -> None:
        name = "测量数据管理系统"
        if self._session_path is not None:
            name = f"{self._session_path.stem} - {name}"
        if self._dirty:
            name = f"* {name}"
        self.setWindowTitle(name)
        if self._session_path is not None:
            self.path_status.setText(str(self._session_path))
        elif not self._dirty:
            self.path_status.setText("未保存工程")

    def _confirm_discard(self) -> bool:
        if not self._dirty:
            return True
        answer = QMessageBox.question(
            self,
            "未保存的更改",
            "当前工程有未保存的更改，是否先保存？",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save_project()
        return answer == QMessageBox.StandardButton.Discard

    def new_project(self, *_args) -> None:
        if not self._confirm_discard():
            return
        self.leveling_page.reset()
        self.analysis_page.reset()
        self.export_page.clear_result()
        self._project = None
        self._result = None
        self._stats = None
        self._session_path = None
        self._dirty = False
        self._update_project_chip()
        self._update_window_title()
        self.path_status.setText("未保存工程")
        self.statusBar().showMessage("已新建工程，请录入测段数据。")
        self._switch_page(0)

    def open_project(self, *_args) -> bool:
        if not self._confirm_discard():
            return False
        start_dir = str(self._session_path.parent) if self._session_path else str(Path.home())
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "打开测量工程",
            start_dir,
            "测量工程文件 (*.json);;所有文件 (*.*)",
        )
        if not filename:
            return False
        try:
            session = ProjectStorage.load(filename)
        except DomainError as exc:
            QMessageBox.warning(self, "打开工程失败", str(exc))
            return False
        self.leveling_page.set_project(session.project)
        self.analysis_page.set_observation_data(
            session.observation_values,
            session.observation_target,
        )
        self._session_path = Path(filename)
        self._dirty = False
        self.path_status.setText(str(self._session_path))
        self._calculate(show_warning=True)
        self._dirty = False
        self._update_window_title()
        self.statusBar().showMessage(f"已打开工程：{self._session_path}")
        return True

    def _collect_session(self) -> ProjectSession | None:
        try:
            project = self.leveling_page.collect_project()
            values = self.analysis_page.observation_values()
        except DomainError as exc:
            QMessageBox.warning(self, "无法保存", f"当前数据不完整：{exc}")
            return None
        return ProjectSession(
            project=project,
            observation_values=values,
            observation_target=self.analysis_page.observation_target(),
        )

    def save_project(self, *_args) -> bool:
        session = self._collect_session()
        if session is None:
            return False
        if self._session_path is None:
            return self.save_project_as()
        try:
            ProjectStorage.save(self._session_path, session)
        except DomainError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return False
        self._dirty = False
        self._update_window_title()
        self.path_status.setText(str(self._session_path))
        self.statusBar().showMessage(f"工程已保存：{self._session_path}")
        return True

    def save_project_as(self, *_args) -> bool:
        session = self._collect_session()
        if session is None:
            return False
        start_dir = (
            self._session_path.parent
            if self._session_path
            else Path.home() / "Documents"
        )
        default_name = f"{self._safe_name(session.project.name)}.json"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存测量工程",
            str(start_dir / default_name),
            "测量工程文件 (*.json)",
        )
        if not filename:
            return False
        destination = Path(filename)
        if destination.suffix.lower() != ".json":
            destination = destination.with_suffix(".json")
        try:
            ProjectStorage.save(destination, session)
        except DomainError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return False
        self._session_path = destination
        self._dirty = False
        self._update_window_title()
        self.path_status.setText(str(self._session_path))
        self.statusBar().showMessage(f"工程已保存：{self._session_path}")
        return True

    def _prepare_export(self):
        prepared = self._calculate(show_warning=False)
        if prepared is None:
            QMessageBox.warning(
                self,
                "无法导出",
                "当前数据不完整或无法计算，请先在“数据输入与计算”页面检查输入。",
            )
            return None
        project, result = prepared
        if not result.is_within_tolerance:
            answer = QMessageBox.warning(
                self,
                "闭合差超限",
                "当前闭合差超过容许值。\n\n是否仍然导出成果？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return None
        return project, result, self.analysis_page.current_stats()

    def export_csv(self, *_args) -> None:
        prepared = self._prepare_export()
        if prepared is None:
            return
        project, result, stats = prepared
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出 CSV",
            str(self._default_export_path(project.name, "csv")),
            "CSV 文件 (*.csv)",
        )
        if not filename:
            return
        destination = self._ensure_suffix(filename, ".csv")
        try:
            ResultExporter.export_csv(destination, project, result, stats)
        except ExportError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        self._last_export_dir = destination.parent
        self.export_page.set_last_export(destination)
        self.statusBar().showMessage(f"CSV 已导出：{destination}")
        QMessageBox.information(self, "导出完成", f"CSV 成果已导出至：\n{destination}")

    def export_excel(self, *_args) -> None:
        prepared = self._prepare_export()
        if prepared is None:
            return
        project, result, stats = prepared
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出 Excel",
            str(self._default_export_path(project.name, "xlsx")),
            "Excel 工作簿 (*.xlsx)",
        )
        if not filename:
            return
        destination = self._ensure_suffix(filename, ".xlsx")
        try:
            ResultExporter.export_excel(destination, project, result, stats)
        except ExportError as exc:
            QMessageBox.warning(self, "导出失败", str(exc))
            return
        self._last_export_dir = destination.parent
        self.export_page.set_last_export(destination)
        self.statusBar().showMessage(f"Excel 已导出：{destination}")
        QMessageBox.information(self, "导出完成", f"Excel 成果已导出至：\n{destination}")

    def _default_export_path(self, project_name: str, suffix: str) -> Path:
        folder = self._last_export_dir
        if folder is None:
            folder = self._session_path.parent if self._session_path else Path.home() / "Documents"
        filename = f"{self._safe_name(project_name)}_水准成果_{date.today():%Y%m%d}.{suffix}"
        return folder / filename

    @staticmethod
    def _safe_name(name: str) -> str:
        cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name).strip().strip(".")
        return cleaned or "水准成果"

    @staticmethod
    def _ensure_suffix(filename: str, suffix: str) -> Path:
        path = Path(filename)
        return path if path.suffix.lower() == suffix else path.with_suffix(suffix)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "关于测量数据管理系统",
            "<h3>测量数据管理系统</h3>"
            f"<p>Version {__version__}</p>"
            "<p>面向水准测量的桌面数据处理工具，提供闭合/附合水准路线计算、"
            "误差分析、重复观测精度评定与成果导出。</p>"
            "<p>技术栈：Python + PySide6 + openpyxl</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()
