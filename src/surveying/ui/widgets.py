from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QColor


class Card(QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 16, 20, 18)
        self._layout.setSpacing(11)
        if title:
            header = QVBoxLayout()
            header.setSpacing(3)
            title_label = QLabel(title)
            title_label.setObjectName("CardTitle")
            header.addWidget(title_label)
            if subtitle:
                subtitle_label = QLabel(subtitle)
                subtitle_label.setObjectName("CardSubtitle")
                subtitle_label.setWordWrap(True)
                header.addWidget(subtitle_label)
            self._layout.addLayout(header)
        self.content = QVBoxLayout()
        self.content.setSpacing(12)
        self._layout.addLayout(self.content, 1)


class MetricTile(QFrame):
    def __init__(self, label: str, value: str = "—", hint: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("MetricTile")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)
        self.label = QLabel(label)
        self.label.setObjectName("MetricLabel")
        self.value = QLabel(value)
        self.value.setObjectName("MetricValue")
        self.hint = QLabel(hint)
        self.hint.setObjectName("MetricHint")
        self.hint.setVisible(bool(hint))
        layout.addWidget(self.label)
        layout.addWidget(self.value)
        layout.addWidget(self.hint)
        self.setMinimumHeight(76)

    def set_value(self, value: str, hint: str = "", tone: str = "") -> None:
        self.value.setText(value)
        self.hint.setText(hint)
        self.hint.setVisible(bool(hint))
        self.value.setProperty("tone", tone)
        self.value.style().unpolish(self.value)
        self.value.style().polish(self.value)


class SummaryMetrics(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.tiles = {
            "closure": MetricTile("闭合差", hint="尚未计算"),
            "allowable": MetricTile("容许闭合差"),
            "quality": MetricTile("质量评定"),
            "distance": MetricTile("路线总长"),
            "end_elevation": MetricTile("计算终点高程"),
        }
        for tile in self.tiles.values():
            layout.addWidget(tile, 1)

    def clear(self) -> None:
        for key, tile in self.tiles.items():
            if key == "closure":
                tile.set_value("—", "尚未计算")
            else:
                tile.set_value("—")

    def show_result(self, result) -> None:
        closure_tone = "success" if result.is_within_tolerance else "danger"
        quality_tone = closure_tone
        self.tiles["closure"].set_value(
            f"{result.closure_error_mm:+.2f} mm",
            f"利用率 {result.closure_utilization * 100:.1f}%"
            if result.closure_utilization is not None
            else "",
            closure_tone,
        )
        self.tiles["allowable"].set_value(
            f"±{result.allowable_closure_mm:.2f} mm",
            f"{result.grade} · {result.grade_coefficient_mm_per_sqrt_km:g}√L",
        )
        self.tiles["quality"].set_value(
            result.quality_level.value,
            "符合限差要求" if result.is_within_tolerance else "闭合差超限",
            quality_tone,
        )
        self.tiles["distance"].set_value(
            f"{result.total_distance_km:.3f} km",
            f"{len(result.segments)} 个测段",
        )
        self.tiles["end_elevation"].set_value(
            f"{result.computed_end_elevation_m:.4f} m",
            f"目标 {result.target_end_elevation_m:.4f} m",
        )


class StatusPill(QLabel):
    def __init__(self, text: str = "等待计算", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("StatusPill")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_tone("neutral")

    def set_tone(self, tone: str) -> None:
        self.setProperty("tone", tone)
        self.style().unpolish(self)
        self.style().polish(self)


def create_table(headers: list[str], parent: QWidget | None = None) -> QTableWidget:
    table = QTableWidget(0, len(headers), parent)
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setEditTriggers(
        QAbstractItemView.EditTrigger.DoubleClicked
        | QAbstractItemView.EditTrigger.EditKeyPressed
        | QAbstractItemView.EditTrigger.SelectedClicked
    )
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setShowGrid(False)
    table.setWordWrap(False)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def make_item(text: str = "", alignment: Qt.AlignmentFlag | None = None, editable: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if alignment is not None:
        item.setTextAlignment(alignment)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def add_card_shadow(card: QWidget) -> None:
    effect = QGraphicsDropShadowEffect(card)
    effect.setBlurRadius(20)
    effect.setOffset(0, 4)
    effect.setColor(QColor(23, 50, 77, 22))
    card.setGraphicsEffect(effect)


def primary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("PrimaryButton")
    button.setMinimumHeight(38)
    return button


def secondary_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("SecondaryButton")
    button.setMinimumHeight(34)
    return button


def ghost_button(text: str) -> QPushButton:
    button = QPushButton(text)
    button.setObjectName("GhostButton")
    return button

