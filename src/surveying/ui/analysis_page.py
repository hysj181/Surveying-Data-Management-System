from __future__ import annotations

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from surveying.domain.error_analysis import (
    ObservationStats,
    analyze_observations,
    assess_closure,
    parse_observation_text,
)
from surveying.domain.leveling import LevelingResult
from surveying.domain.models import DomainError, LevelingProject
from surveying.services.samples import sample_observation_target, sample_observation_text

from .widgets import Card, StatusPill, SummaryMetrics, create_table, make_item, primary_button


class AnalysisPage(QWidget):
    content_changed = Signal()
    analysis_completed = Signal(object, object, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._stats: ObservationStats | None = None
        self._project: LevelingProject | None = None
        self._result: LevelingResult | None = None
        self._build_ui()
        self._connect_signals()
        self._clear_closure()
        self._clear_observation_results()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.summary = SummaryMetrics()
        layout.addWidget(self.summary)

        content = QHBoxLayout()
        content.setSpacing(16)

        closure_card = Card("路线闭合差评定", "根据当前计算成果检查限差、改正数分配与各点高程。")
        status_row = QHBoxLayout()
        status_caption = QLabel("评定结论")
        status_caption.setObjectName("FieldHint")
        self.closure_status = StatusPill("等待计算")
        status_row.addWidget(status_caption)
        status_row.addWidget(self.closure_status)
        status_row.addStretch(1)
        closure_card.content.addLayout(status_row)

        detail_grid = QGridLayout()
        detail_grid.setHorizontalSpacing(16)
        detail_grid.setVerticalSpacing(6)
        self.closure_ratio_label = QLabel("—")
        self.closure_ratio_label.setObjectName("FieldHint")
        self.correction_label = QLabel("—")
        self.correction_label.setObjectName("FieldHint")
        self.endpoint_label = QLabel("—")
        self.endpoint_label.setObjectName("FieldHint")
        detail_grid.addWidget(QLabel("闭合差 / 路线长"), 0, 0)
        detail_grid.addWidget(self.closure_ratio_label, 0, 1)
        detail_grid.addWidget(QLabel("改正数中误差"), 1, 0)
        detail_grid.addWidget(self.correction_label, 1, 1)
        detail_grid.addWidget(QLabel("终点高程"), 2, 0)
        detail_grid.addWidget(self.endpoint_label, 2, 1)
        closure_card.content.addLayout(detail_grid)

        headers = ["序号", "测段", "距离(m)", "改正(mm)", "改正后高差(m)", "高程(m)"]
        self.segment_table = create_table(headers)
        self.segment_table.setMinimumHeight(200)
        self.segment_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.segment_table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for column in range(2, 6):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        closure_card.content.addWidget(self.segment_table, 1)

        self.warning_label = QLabel()
        self.warning_label.setObjectName("WarningBanner")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        closure_card.content.addWidget(self.warning_label)

        observation_card = Card(
            "重复观测精度分析",
            "输入同一量的多次观测值，计算均值、标准差、标准误差并按设定倍数 σ 原则提示粗差。",
        )
        self.observation_edit = QPlainTextEdit()
        self.observation_edit.setPlaceholderText(
            "每行输入一个观测值，也可使用逗号分隔，例如：\n1.5234\n1.5241\n1.5238"
        )
        self.observation_edit.setMinimumHeight(90)
        self.observation_edit.setMaximumHeight(104)
        observation_card.content.addWidget(self.observation_edit)

        option_row = QHBoxLayout()
        option_row.setSpacing(8)
        self.target_check = QCheckBox("设置参考值")
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(-1000000.0, 1000000.0)
        self.target_spin.setDecimals(5)
        self.target_spin.setEnabled(False)
        self.target_spin.setValue(sample_observation_target())
        self.outlier_combo = QComboBox()
        self.outlier_combo.addItem("3σ 粗差判定", 3.0)
        self.outlier_combo.addItem("2σ 粗差判定", 2.0)
        self.outlier_combo.setToolTip("观测值偏离均值超过指定倍数标准差时标记为可疑值")
        option_row.addWidget(self.target_check)
        option_row.addWidget(self.target_spin)
        option_row.addStretch(1)
        option_row.addWidget(self.outlier_combo)
        observation_card.content.addLayout(option_row)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        analyze_button = primary_button("分析观测列")
        analyze_button.setMinimumHeight(34)
        sample_button = QPushButton("示例数据")
        sample_button.setObjectName("GhostButton")
        clear_button = QPushButton("清空")
        clear_button.setObjectName("GhostButton")
        analyze_button.clicked.connect(self.analyze_observations)
        sample_button.clicked.connect(self._load_sample)
        clear_button.clicked.connect(self._clear_observation_input)
        button_row.addWidget(analyze_button)
        button_row.addWidget(sample_button)
        button_row.addWidget(clear_button)
        button_row.addStretch(1)
        self.observation_status = StatusPill("尚未分析")
        button_row.addWidget(self.observation_status)
        observation_card.content.addLayout(button_row)

        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(18)
        stats_grid.setVerticalSpacing(5)
        self.stat_values: dict[str, QLabel] = {}
        stat_specs = [
            ("count", "观测个数"),
            ("mean", "均值"),
            ("median", "中位数"),
            ("std", "样本标准差"),
            ("se", "标准误差"),
            ("rmse", "RMSE"),
            ("min", "最小值"),
            ("max", "最大值"),
            ("range", "极差"),
            ("relative", "相对标准差"),
        ]
        for index, (key, caption) in enumerate(stat_specs):
            row, column = divmod(index, 2)
            label = QLabel(caption)
            label.setObjectName("FieldHint")
            value = QLabel("—")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            stats_grid.addWidget(label, row, column * 2)
            stats_grid.addWidget(value, row, column * 2 + 1)
            self.stat_values[key] = value
        observation_card.content.addLayout(stats_grid)

        outlier_headers = ["序号", "观测值", "残差", "判定"]
        self.outlier_table = create_table(outlier_headers)
        self.outlier_table.setMinimumHeight(120)
        outlier_header = self.outlier_table.horizontalHeader()
        outlier_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        outlier_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        outlier_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        outlier_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.outlier_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        observation_card.content.addWidget(self.outlier_table, 1)

        content.addWidget(closure_card, 1)
        content.addWidget(observation_card, 1)
        layout.addLayout(content, 1)

    def _connect_signals(self) -> None:
        self.target_check.toggled.connect(self.target_spin.setEnabled)
        self.target_check.toggled.connect(lambda _checked: self.content_changed.emit())
        self.target_spin.valueChanged.connect(lambda _value: self.content_changed.emit())
        self.outlier_combo.currentIndexChanged.connect(lambda _index: self.content_changed.emit())
        self.observation_edit.textChanged.connect(lambda: self.content_changed.emit())

    def set_result(self, project: LevelingProject, result: LevelingResult) -> None:
        self._project = project
        self._result = result
        self.summary.show_result(result)
        closure = assess_closure(result)
        self.closure_status.setText(result.quality_level.value)
        self.closure_status.set_tone("success" if result.is_within_tolerance else "danger")
        self.closure_ratio_label.setText(
            f"{closure.ratio_text} · 利用率 "
            f"{'—' if closure.utilization is None else f'{closure.utilization * 100:.1f}%'}"
        )
        self.correction_label.setText(
            f"{closure.correction_rms_mm:.3f} mm（最大 {closure.max_abs_correction_mm:.3f} mm）"
        )
        self.endpoint_label.setText(
            f"{result.computed_end_elevation_m:.4f} m / 目标 {result.target_end_elevation_m:.4f} m"
        )
        self.warning_label.setText("\n".join(result.warnings))
        self.warning_label.setVisible(bool(result.warnings))

        self.segment_table.setRowCount(len(result.segments))
        for row, item in enumerate(result.segments):
            values = [
                str(item.index),
                f"{item.segment.from_point} → {item.segment.to_point}",
                f"{item.segment.distance_m:.3f}",
                f"{item.correction_mm:+.2f}",
                f"{item.corrected_difference_m:.4f}",
                f"{item.to_elevation_m:.4f}",
            ]
            for column, value in enumerate(values):
                alignment = Qt.AlignmentFlag.AlignLeft if column == 1 else Qt.AlignmentFlag.AlignCenter
                self.segment_table.setItem(row, column, make_item(value, alignment))
            self.segment_table.setRowHeight(row, 32)

    def clear_closure(self) -> None:
        self._clear_closure()

    def _clear_closure(self) -> None:
        self._project = None
        self._result = None
        self.summary.clear()
        self.closure_status.setText("等待计算")
        self.closure_status.set_tone("neutral")
        self.closure_ratio_label.setText("—")
        self.correction_label.setText("—")
        self.endpoint_label.setText("—")
        self.segment_table.setRowCount(0)
        self.warning_label.clear()
        self.warning_label.hide()

    def analyze_observations(self) -> None:
        try:
            values = parse_observation_text(self.observation_edit.toPlainText())
            target = self.target_spin.value() if self.target_check.isChecked() else None
            stats = analyze_observations(
                values,
                target=target,
                outlier_sigma=float(self.outlier_combo.currentData()),
            )
        except DomainError as exc:
            QMessageBox.warning(self, "误差分析", str(exc))
            return
        self._stats = stats
        self._show_stats(stats)
        if stats.has_outliers:
            self.observation_status.setText(f"发现 {len(stats.outliers)} 个可疑值")
            self.observation_status.set_tone("warning")
        else:
            self.observation_status.setText("分析完成")
            self.observation_status.set_tone("success")
        self.analysis_completed.emit(stats, list(stats.values), stats.target)

    def _show_stats(self, stats: ObservationStats) -> None:
        self.stat_values["count"].setText(str(stats.count))
        self.stat_values["mean"].setText(f"{stats.mean:.5f}")
        self.stat_values["median"].setText(f"{stats.median:.5f}")
        self.stat_values["std"].setText(f"{stats.std_dev:.5f}")
        self.stat_values["se"].setText(f"{stats.standard_error:.5f}")
        self.stat_values["rmse"].setText(f"{stats.rmse:.5f}")
        self.stat_values["min"].setText(f"{stats.minimum:.5f}")
        self.stat_values["max"].setText(f"{stats.maximum:.5f}")
        self.stat_values["range"].setText(f"{stats.range_value:.5f}")
        self.stat_values["relative"].setText(
            "—" if stats.relative_std is None else f"{stats.relative_std * 100:.3f}%"
        )

        self.outlier_table.setRowCount(len(stats.values))
        outlier_indexes = {item.index for item in stats.outliers}
        reference = stats.target if stats.target is not None else stats.mean
        for row, value in enumerate(stats.values):
            flagged = row + 1 in outlier_indexes
            values = [
                str(row + 1),
                f"{value:.5f}",
                f"{value - reference:+.5f}",
                "粗差可疑" if flagged else "正常",
            ]
            for column, text in enumerate(values):
                item = make_item(text, Qt.AlignmentFlag.AlignCenter)
                if flagged and column == 3:
                    item.setForeground(Qt.GlobalColor.darkRed)
                self.outlier_table.setItem(row, column, item)
            self.outlier_table.setRowHeight(row, 28)
        if not stats.outliers:
            self.observation_status.setToolTip("未发现超出判定阈值的数据")
        else:
            self.observation_status.setToolTip(
                f"发现 {len(stats.outliers)} 个可疑值，建议复核原始记录"
            )

    def _clear_observation_results(self) -> None:
        self._stats = None
        self.observation_status.setText("尚未分析")
        self.observation_status.set_tone("neutral")
        for value in self.stat_values.values():
            value.setText("—")
        self.outlier_table.setRowCount(0)

    def _clear_observation_input(self) -> None:
        self.observation_edit.clear()
        self.target_check.setChecked(False)
        self._clear_observation_results()
        self.content_changed.emit()

    def _load_sample(self) -> None:
        with QSignalBlocker(self.observation_edit):
            self.observation_edit.setPlainText(sample_observation_text())
        self.target_check.setChecked(True)
        self.target_spin.setValue(sample_observation_target())
        self.analyze_observations()
        self.content_changed.emit()

    def reset(self) -> None:
        with QSignalBlocker(self.observation_edit):
            self.observation_edit.clear()
        self.target_check.setChecked(False)
        self._clear_observation_results()
        self._clear_closure()

    def set_observation_data(self, values: list[float], target: float | None) -> None:
        with QSignalBlocker(self.observation_edit):
            self.observation_edit.setPlainText("\n".join(f"{value:.5f}" for value in values))
        with QSignalBlocker(self.target_check):
            self.target_check.setChecked(target is not None)
        self.target_spin.setEnabled(target is not None)
        if target is not None:
            with QSignalBlocker(self.target_spin):
                self.target_spin.setValue(target)
        self._clear_observation_results()
        if values:
            self.analyze_observations()

    def current_stats(self) -> ObservationStats | None:
        if self._stats is None:
            return None
        try:
            values = parse_observation_text(self.observation_edit.toPlainText())
        except DomainError:
            return None
        target = self.target_spin.value() if self.target_check.isChecked() else None
        if tuple(values) != self._stats.values or target != self._stats.target:
            return None
        return self._stats

    def observation_values(self) -> list[float]:
        if not self.observation_edit.toPlainText().strip():
            return []
        return parse_observation_text(self.observation_edit.toPlainText())

    def observation_target(self) -> float | None:
        return self.target_spin.value() if self.target_check.isChecked() else None

