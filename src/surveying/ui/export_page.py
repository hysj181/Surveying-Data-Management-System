from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from surveying.domain.leveling import LevelingResult
from surveying.domain.models import LevelingProject

from .widgets import Card, StatusPill, primary_button, secondary_button


class ExportOption(QFrame):
    def __init__(
        self,
        badge: str,
        title: str,
        description: str,
        button_text: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setObjectName("ExportOption")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        badge_label = QLabel(badge)
        badge_label.setObjectName("ExportBadge")
        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")
        description_label = QLabel(description)
        description_label.setObjectName("CardSubtitle")
        description_label.setWordWrap(True)
        description_label.setMinimumHeight(58)
        self.button = secondary_button(button_text)
        layout.addWidget(badge_label, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(self.button)


class ExportPage(QWidget):
    export_csv_requested = Signal()
    export_excel_requested = Signal()
    save_project_requested = Signal()
    open_project_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._project: LevelingProject | None = None
        self._result: LevelingResult | None = None
        self._build_ui()
        self.clear_result()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        summary_card = Card("当前成果", "导出操作将使用当前录入数据重新计算，确保成果与界面数据一致。")
        header_row = QHBoxLayout()
        self.project_label = QLabel("尚未载入工程")
        self.project_label.setObjectName("CardTitle")
        self.status = StatusPill("等待计算")
        header_row.addWidget(self.project_label)
        header_row.addStretch(1)
        header_row.addWidget(self.status)
        summary_card.content.addLayout(header_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(8)
        self.meta_values: dict[str, QLabel] = {}
        for index, (key, caption) in enumerate(
            [
                ("route", "路线类型"),
                ("grade", "测量等级"),
                ("closure", "闭合差"),
                ("quality", "质量评定"),
                ("distance", "路线总长"),
                ("observations", "观测列分析"),
            ]
        ):
            row, column = divmod(index, 3)
            caption_label = QLabel(caption)
            caption_label.setObjectName("FieldHint")
            value_label = QLabel("—")
            grid.addWidget(caption_label, row, column * 2)
            grid.addWidget(value_label, row, column * 2 + 1)
            self.meta_values[key] = value_label
        summary_card.content.addLayout(grid)
        layout.addWidget(summary_card)

        options_row = QHBoxLayout()
        options_row.setSpacing(16)
        csv_option = ExportOption(
            "CSV",
            "CSV 表格",
            "UTF-8 带 BOM 编码，可直接用 Excel 打开。包含工程概况、计算摘要、测段成果和误差分析。",
            "导出 CSV",
        )
        excel_option = ExportOption(
            "XLSX",
            "Excel 工作簿",
            "生成工程概况、水准计算、误差分析三个工作表，带表头样式、列宽和数字格式。",
            "导出 Excel",
        )
        project_option = ExportOption(
            "JSON",
            "工程文件",
            "保存当前工程与观测列，便于下次继续编辑；也可打开已保存的工程文件。",
            "保存工程",
        )
        csv_option.button.clicked.connect(self.export_csv_requested.emit)
        excel_option.button.clicked.connect(self.export_excel_requested.emit)
        project_option.button.clicked.connect(self.save_project_requested.emit)
        self.export_buttons = [csv_option.button, excel_option.button, project_option.button]
        options_row.addWidget(csv_option, 1)
        options_row.addWidget(excel_option, 1)
        options_row.addWidget(project_option, 1)
        layout.addLayout(options_row, 1)

        project_card = Card("工程文件管理", "工程文件使用 JSON 格式保存，包含测段、控制点、工程信息和观测列。")
        project_row = QHBoxLayout()
        project_row.setSpacing(10)
        open_hint = QLabel("也可以使用菜单“文件 → 打开工程”载入历史工程。")
        open_hint.setObjectName("FieldHint")
        self.open_button = secondary_button("打开工程")
        self.open_button.clicked.connect(self.open_project_requested.emit)
        project_row.addWidget(open_hint)
        project_row.addStretch(1)
        project_row.addWidget(self.open_button)
        project_card.content.addLayout(project_row)
        layout.addWidget(project_card)

        self.export_path_label = QLabel("尚未导出成果。")
        self.export_path_label.setObjectName("PathLabel")
        self.export_path_label.setWordWrap(True)
        layout.addWidget(self.export_path_label)

    def set_result(self, project: LevelingProject, result: LevelingResult) -> None:
        self._project = project
        self._result = result
        self.project_label.setText(project.name or "未命名水准工程")
        self.status.setText("成果可导出")
        self.status.set_tone("success" if result.is_within_tolerance else "danger")
        self.meta_values["route"].setText(project.route_type.label)
        self.meta_values["grade"].setText(project.grade.value)
        self.meta_values["closure"].setText(f"{result.closure_error_mm:+.2f} mm")
        self.meta_values["quality"].setText(result.quality_level.value)
        self.meta_values["distance"].setText(f"{result.total_distance_km:.3f} km")
        for button in self.export_buttons:
            button.setEnabled(True)
        self.open_button.setEnabled(True)

    def set_observation_count(self, count: int | None) -> None:
        self.meta_values["observations"].setText(
            "未分析" if not count else f"{count} 个观测值"
        )

    def set_last_export(self, path: str | Path) -> None:
        self.export_path_label.setText(f"最近导出：{Path(path)}")

    def clear_result(self) -> None:
        self._project = None
        self._result = None
        self.project_label.setText("尚未载入工程")
        self.status.setText("等待计算")
        self.status.set_tone("neutral")
        for value in self.meta_values.values():
            value.setText("—")
        for button in self.export_buttons:
            button.setEnabled(False)
        self.open_button.setEnabled(True)
