from __future__ import annotations

from PySide6.QtCore import QDate, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from surveying.domain.leveling import LevelingResult
from surveying.domain.models import LevelingGrade, LevelingProject, LevelingSegment, RouteType
from surveying.services.samples import create_sample_project

from .widgets import Card, SummaryMetrics, create_table, make_item, primary_button, secondary_button


class LevelingPage(QWidget):
    calculate_requested = Signal()
    content_changed = Signal()
    result_invalidated = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._loading = False
        self._has_result = False
        self._build_ui()
        self._connect_signals()
        self._sync_closed_endpoint()
        self._update_grade_hint()
        self._add_segment_row()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(13)

        info_card = Card("工程信息", "录入路线类型、等级与控制点信息，闭合路线将自动回到起点。")

        def field_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label.setMinimumWidth(76)
            return label

        self.name_edit = QLineEdit("新建水准工程")
        self.observer_edit = QLineEdit()
        self.observer_edit.setPlaceholderText("选填")
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.route_combo = QComboBox()
        for route in RouteType:
            self.route_combo.addItem(route.label, route.value)
        self.grade_combo = QComboBox()
        for grade in LevelingGrade:
            self.grade_combo.addItem(grade.value, grade.value)
        self.grade_combo.setCurrentIndex(1)
        self.start_point_edit = QLineEdit("BM-A")
        self.start_elevation_spin = QDoubleSpinBox()
        self.start_elevation_spin.setRange(-10000.0, 10000.0)
        self.start_elevation_spin.setDecimals(4)
        self.start_elevation_spin.setSingleStep(0.1)
        self.start_elevation_spin.setValue(100.0)
        self.end_point_edit = QLineEdit("BM-A")
        self.end_elevation_spin = QDoubleSpinBox()
        self.end_elevation_spin.setRange(-10000.0, 10000.0)
        self.end_elevation_spin.setDecimals(4)
        self.end_elevation_spin.setSingleStep(0.1)
        self.end_elevation_spin.setValue(100.0)
        self.end_point_label = field_label("终点名称")
        self.end_elevation_label = field_label("终点高程(m)")
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("可填写仪器、天气、路线说明等")
        self.grade_hint = QLabel()
        self.grade_hint.setObjectName("FieldHint")

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(7)
        grid.addWidget(field_label("工程名称"), 0, 0)
        grid.addWidget(self.name_edit, 0, 1, 1, 3)
        grid.addWidget(field_label("观测者"), 0, 4)
        grid.addWidget(self.observer_edit, 0, 5, 1, 3)
        grid.addWidget(field_label("观测日期"), 1, 0)
        grid.addWidget(self.date_edit, 1, 1)
        grid.addWidget(field_label("路线类型"), 1, 2)
        grid.addWidget(self.route_combo, 1, 3)
        grid.addWidget(field_label("测量等级"), 1, 4)
        grid.addWidget(self.grade_combo, 1, 5)
        grid.addWidget(field_label("起点名称"), 1, 6)
        grid.addWidget(self.start_point_edit, 1, 7)
        grid.addWidget(field_label("起点高程(m)"), 2, 0)
        grid.addWidget(self.start_elevation_spin, 2, 1)
        grid.addWidget(self.end_point_label, 2, 2)
        grid.addWidget(self.end_point_edit, 2, 3)
        grid.addWidget(self.end_elevation_label, 2, 4)
        grid.addWidget(self.end_elevation_spin, 2, 5)
        grid.addWidget(field_label("限差"), 2, 6)
        grid.addWidget(self.grade_hint, 2, 7)
        grid.addWidget(field_label("工程备注"), 3, 0)
        grid.addWidget(self.notes_edit, 3, 1, 1, 7)
        for column in (1, 3, 5, 7):
            grid.setColumnStretch(column, 1)
        info_card.content.addLayout(grid)
        layout.addWidget(info_card)

        data_card = Card("测段数据")
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        add_button = secondary_button("添加测段")
        delete_button = QPushButton("删除选中")
        delete_button.setObjectName("DangerButton")
        clear_button = QPushButton("清空测段")
        clear_button.setObjectName("GhostButton")
        sample_button = QPushButton("载入示例")
        sample_button.setObjectName("GhostButton")
        self.row_count_label = QLabel()
        self.row_count_label.setObjectName("FieldHint")
        add_button.clicked.connect(lambda: self._add_segment_row())
        delete_button.clicked.connect(self._delete_selected_rows)
        clear_button.clicked.connect(self._clear_rows)
        sample_button.clicked.connect(self._load_sample)
        toolbar.addWidget(add_button)
        toolbar.addWidget(delete_button)
        toolbar.addWidget(clear_button)
        toolbar.addWidget(sample_button)
        toolbar.addStretch(1)
        toolbar.addWidget(self.row_count_label)
        data_card.content.addLayout(toolbar)

        headers = [
            "序号",
            "起点",
            "终点",
            "距离(m)",
            "观测高差(m)",
            "改正数(mm)",
            "改正后高差(m)",
            "起点高程(m)",
            "终点高程(m)",
        ]
        self.table = create_table(headers)
        self.table.setMinimumHeight(200)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        for column in range(5, 9):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        data_card.content.addWidget(self.table, 1)

        self.summary = SummaryMetrics()
        data_card.content.addWidget(self.summary)

        self.warning_label = QLabel()
        self.warning_label.setObjectName("WarningBanner")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        data_card.content.addWidget(self.warning_label)
        layout.addWidget(data_card, 1)

        footer = QHBoxLayout()
        footer.setSpacing(12)
        footer_hint = QLabel("距离按比例分配闭合差；计算后可在“误差分析”和“成果导出”页面查看与导出成果。")
        footer_hint.setObjectName("FieldHint")
        self.calculate_button = primary_button("执行水准计算")
        self.calculate_button.setMinimumWidth(170)
        footer.addWidget(footer_hint)
        footer.addStretch(1)
        footer.addWidget(self.calculate_button)
        layout.addLayout(footer)

        self._update_row_count()

    def _connect_signals(self) -> None:
        self.calculate_button.clicked.connect(self.calculate_requested.emit)
        self.route_combo.currentIndexChanged.connect(self._on_route_changed)
        self.grade_combo.currentIndexChanged.connect(self._on_grade_changed)
        self.start_point_edit.textChanged.connect(self._on_start_point_changed)
        self.start_elevation_spin.valueChanged.connect(self._on_start_elevation_changed)
        self.name_edit.textChanged.connect(self._mark_changed)
        self.observer_edit.textChanged.connect(self._mark_changed)
        self.date_edit.dateChanged.connect(self._mark_changed)
        self.start_point_edit.textChanged.connect(self._mark_changed)
        self.start_elevation_spin.valueChanged.connect(self._mark_changed)
        self.end_point_edit.textChanged.connect(self._mark_changed)
        self.end_elevation_spin.valueChanged.connect(self._mark_changed)
        self.notes_edit.textChanged.connect(self._mark_changed)
        self.table.itemChanged.connect(self._on_item_changed)

    def _on_route_changed(self, _index: int = -1) -> None:
        if self._loading:
            return
        self._sync_closed_endpoint()
        self._mark_changed()

    def _on_grade_changed(self, _index: int = -1) -> None:
        self._update_grade_hint()
        self._mark_changed()

    def _on_start_point_changed(self, text: str) -> None:
        if self._loading:
            return
        self._sync_closed_endpoint()

    def _on_start_elevation_changed(self, value: float) -> None:
        if self._loading:
            return
        self._sync_closed_endpoint()

    def _is_closed(self) -> bool:
        return self.route_combo.currentData() == RouteType.CLOSED.value

    def _sync_closed_endpoint(self) -> None:
        closed = self._is_closed()
        self.end_point_edit.setEnabled(not closed)
        self.end_elevation_spin.setEnabled(not closed)
        self.end_point_label.setText("终点名称*" if closed else "终点名称")
        self.end_elevation_label.setText("终点高程(m)*" if closed else "终点高程(m)")
        self.end_point_label.setToolTip("闭合路线自动回到起点" if closed else "")
        self.end_elevation_label.setToolTip("闭合路线自动采用起点高程" if closed else "")
        if closed:
            with QSignalBlocker(self.end_point_edit), QSignalBlocker(self.end_elevation_spin):
                self.end_point_edit.setText(self.start_point_edit.text())
                self.end_elevation_spin.setValue(self.start_elevation_spin.value())

    def _update_grade_hint(self) -> None:
        grade_value = self.grade_combo.currentData()
        if grade_value:
            grade = LevelingGrade.from_value(grade_value)
            self.grade_hint.setText(f"±{grade.coefficient_mm_per_sqrt_km:g}√L mm")
            self.grade_hint.setToolTip(
                f"容许闭合差 ±{grade.coefficient_mm_per_sqrt_km:g}√L mm，L 为路线长度（km）"
            )

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._loading:
            return
        if item.column() in (1, 2):
            self._mark_changed()

    def _mark_changed(self, *_args) -> None:
        if self._loading:
            return
        if self._has_result:
            self.clear_result()
            self.result_invalidated.emit()
        self.content_changed.emit()

    def _add_segment_row(self, from_point: str | None = None) -> None:
        if self._loading:
            self._loading = True
            try:
                self._append_row(from_point)
            finally:
                self._loading = False
            self._update_row_count()
            return

        self._append_row(from_point)
        self._mark_changed()
        self._update_row_count()

    def _append_row(self, from_point: str | None = None) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setRowHeight(row, 32)

        if from_point is None and row > 0:
            previous = self.table.item(row - 1, 2)
            from_point = previous.text().strip() if previous else ""
        if from_point is None:
            from_point = self.start_point_edit.text().strip()

        index_item = make_item(str(row + 1), Qt.AlignmentFlag.AlignCenter)
        from_item = make_item(from_point, Qt.AlignmentFlag.AlignCenter, editable=True)
        to_item = make_item("", Qt.AlignmentFlag.AlignCenter, editable=True)
        self.table.setItem(row, 0, index_item)
        self.table.setItem(row, 1, from_item)
        self.table.setItem(row, 2, to_item)

        distance_spin = self._make_cell_spin(3, 100.0, 0.001)
        difference_spin = self._make_cell_spin(4, 0.0, -100000.0)
        self.table.setCellWidget(row, 3, distance_spin)
        self.table.setCellWidget(row, 4, difference_spin)

        for column in range(5, 9):
            self.table.setItem(row, column, make_item("", Qt.AlignmentFlag.AlignRight))

    def _make_cell_spin(self, decimals: int, value: float, minimum: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setObjectName("CellSpinBox")
        spin.setDecimals(decimals)
        spin.setRange(minimum, 1000000.0 if minimum >= 0 else 100000.0)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        spin.setKeyboardTracking(False)
        spin.valueChanged.connect(self._on_cell_value_changed)
        if minimum >= 0:
            spin.valueChanged.connect(lambda _value: self._update_row_count())
        return spin

    def _on_cell_value_changed(self, _value: float) -> None:
        self._mark_changed()

    def _delete_selected_rows(self) -> None:
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "删除测段", "请先选中需要删除的测段行。")
            return
        self._loading = True
        try:
            for row in rows:
                self.table.removeRow(row)
            self._renumber_rows()
        finally:
            self._loading = False
        self._update_row_count()
        self._mark_changed()

    def _clear_rows(self) -> None:
        if self.table.rowCount() == 0:
            return
        answer = QMessageBox.question(
            self,
            "清空测段",
            "确定清空全部测段数据吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer is not QMessageBox.StandardButton.Yes:
            return
        self._loading = True
        try:
            self.table.setRowCount(0)
        finally:
            self._loading = False
        self._add_segment_row()
        self._update_row_count()
        self._mark_changed()

    def _renumber_rows(self) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                item = make_item("", Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, item)
            item.setText(str(row + 1))

    def _update_row_count(self) -> None:
        count = self.table.rowCount()
        total_distance = 0.0
        for row in range(count):
            widget = self.table.cellWidget(row, 3)
            if isinstance(widget, QDoubleSpinBox):
                total_distance += widget.value()
        self.row_count_label.setText(f"{count} 个测段 · 合计 {total_distance / 1000:.3f} km")

    def collect_project(self) -> LevelingProject:
        route_type = RouteType.from_value(self.route_combo.currentData())
        grade = LevelingGrade.from_value(self.grade_combo.currentData())
        segments: list[LevelingSegment] = []
        for row in range(self.table.rowCount()):
            from_item = self.table.item(row, 1)
            to_item = self.table.item(row, 2)
            distance_spin = self.table.cellWidget(row, 3)
            difference_spin = self.table.cellWidget(row, 4)
            if not isinstance(distance_spin, QDoubleSpinBox) or not isinstance(
                difference_spin, QDoubleSpinBox
            ):
                continue
            segments.append(
                LevelingSegment(
                    from_point=from_item.text().strip() if from_item else "",
                    to_point=to_item.text().strip() if to_item else "",
                    distance_m=distance_spin.value(),
                    observed_difference_m=difference_spin.value(),
                )
            )
        closed = route_type is RouteType.CLOSED
        return LevelingProject(
            name=self.name_edit.text().strip() or "未命名水准工程",
            route_type=route_type,
            grade=grade,
            observer=self.observer_edit.text().strip(),
            survey_date=self.date_edit.date().toString("yyyy-MM-dd"),
            start_point=self.start_point_edit.text().strip(),
            start_elevation_m=self.start_elevation_spin.value(),
            end_point=self.start_point_edit.text().strip() if closed else self.end_point_edit.text().strip(),
            end_elevation_m=self.start_elevation_spin.value() if closed else self.end_elevation_spin.value(),
            notes=self.notes_edit.text().strip(),
            segments=segments,
        )

    def show_result(self, result: LevelingResult) -> None:
        self._loading = True
        try:
            for row, segment_result in enumerate(result.segments):
                values = [
                    f"{segment_result.correction_mm:+.2f}",
                    f"{segment_result.corrected_difference_m:.4f}",
                    f"{segment_result.from_elevation_m:.4f}",
                    f"{segment_result.to_elevation_m:.4f}",
                ]
                for offset, value in enumerate(values, start=5):
                    item = self.table.item(row, offset)
                    if item is None:
                        item = make_item(value, Qt.AlignmentFlag.AlignRight)
                        self.table.setItem(row, offset, item)
                    item.setText(value)
                    item.setForeground(QColor("#405969") if offset > 5 else QColor("#0F766E"))
            self.summary.show_result(result)
            self.warning_label.setText("\n".join(result.warnings))
            self.warning_label.setVisible(bool(result.warnings))
            self._has_result = True
        finally:
            self._loading = False

    def clear_result(self) -> None:
        previous_loading = self._loading
        self._loading = True
        try:
            for row in range(self.table.rowCount()):
                for column in range(5, 9):
                    item = self.table.item(row, column)
                    if item is not None:
                        item.setText("")
            self.summary.clear()
            self.warning_label.clear()
            self.warning_label.hide()
            self._has_result = False
        finally:
            self._loading = previous_loading

    def reset(self) -> None:
        self.set_project(LevelingProject(segments=[]))
        if self.table.rowCount() == 0:
            self._add_segment_row()

    def set_project(self, project: LevelingProject) -> None:
        self._loading = True
        try:
            self.name_edit.setText(project.name)
            self.observer_edit.setText(project.observer)
            date = QDate.fromString(project.survey_date, "yyyy-MM-dd")
            self.date_edit.setDate(date if date.isValid() else QDate.currentDate())
            route_index = self.route_combo.findData(project.route_type.value)
            self.route_combo.setCurrentIndex(route_index if route_index >= 0 else 0)
            grade_index = self.grade_combo.findData(project.grade.value)
            self.grade_combo.setCurrentIndex(grade_index if grade_index >= 0 else 1)
            self.start_point_edit.setText(project.start_point)
            self.start_elevation_spin.setValue(project.start_elevation_m)
            self.end_point_edit.setText(project.end_point)
            self.end_elevation_spin.setValue(project.end_elevation_m)
            self.notes_edit.setText(project.notes)
            self.table.setRowCount(0)
            for segment in project.segments:
                self._append_row(segment.from_point)
                row = self.table.rowCount() - 1
                self.table.item(row, 1).setText(segment.from_point)
                self.table.item(row, 2).setText(segment.to_point)
                distance_spin = self.table.cellWidget(row, 3)
                difference_spin = self.table.cellWidget(row, 4)
                distance_spin.setValue(segment.distance_m)
                difference_spin.setValue(segment.observed_difference_m)
            if not project.segments:
                self._append_row(project.start_point)
            self._sync_closed_endpoint()
            self._update_grade_hint()
            self.clear_result()
            self._update_row_count()
        finally:
            self._loading = False

    def _load_sample(self) -> None:
        project = create_sample_project()
        self.set_project(project)
        self._mark_changed()
        self.calculate_requested.emit()

    def set_busy(self, busy: bool) -> None:
        self.calculate_button.setEnabled(not busy)
        self.calculate_button.setText("正在计算…" if busy else "执行水准计算")



