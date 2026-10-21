APP_STYLESHEET = """
QWidget {
    color: #1F2937;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
    font-size: 10pt;
}
QMainWindow, QWidget#Root, QWidget#PageHost {
    background: #F2F6F8;
}
QScrollArea#PageScroll {
    background: transparent;
    border: none;
}
QScrollArea#PageScroll > QWidget > QWidget {
    background: transparent;
}
QFrame#Sidebar {
    background: #122B3E;
    border: none;
}
QLabel#BrandMark {
    color: #5EEAD4;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 2px;
}
QLabel#BrandTitle {
    color: #FFFFFF;
    font-size: 18pt;
    font-weight: 700;
}
QLabel#BrandSubtitle {
    color: #9DB4C4;
    font-size: 9pt;
}
QLabel#SidebarSection {
    color: #6F8A9C;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
    padding-left: 8px;
}
QPushButton#NavButton {
    background: transparent;
    color: #BFD0DB;
    border: none;
    border-radius: 8px;
    padding: 12px 14px;
    text-align: left;
    font-size: 10pt;
    font-weight: 600;
}
QPushButton#NavButton:hover {
    background: #1A3A50;
    color: #FFFFFF;
}
QPushButton#NavButton:checked {
    background: #0F766E;
    color: #FFFFFF;
}
QLabel#SidebarFooter {
    color: #6F8A9C;
    font-size: 8pt;
}
QFrame#SidebarDivider {
    background: #224459;
    max-height: 1px;
    min-height: 1px;
}
QLabel#PageTitle {
    color: #122B3E;
    font-size: 20pt;
    font-weight: 700;
}
QLabel#PageSubtitle {
    color: #6B7C8A;
    font-size: 9pt;
}
QLabel#ProjectChip {
    background: #E7EEF2;
    color: #314A5C;
    border-radius: 12px;
    padding: 6px 13px;
    font-size: 9pt;
    font-weight: 600;
}
QLabel#ProjectChip[tone="success"] {
    background: #DDF6ED;
    color: #0F6B5B;
}
QLabel#ProjectChip[tone="danger"] {
    background: #FDE8E8;
    color: #B42318;
}
QLabel#ProjectChip[tone="neutral"] {
    background: #E7EEF2;
    color: #314A5C;
}
QFrame#Card {
    background: #FFFFFF;
    border: 1px solid #E2EAEF;
    border-radius: 11px;
}
QLabel#CardTitle {
    color: #17324D;
    font-size: 12pt;
    font-weight: 700;
}
QLabel#CardSubtitle {
    color: #778895;
    font-size: 9pt;
}
QFrame#MetricTile {
    background: #F7FAFB;
    border: 1px solid #E4ECF1;
    border-radius: 9px;
}
QLabel#MetricLabel {
    color: #718391;
    font-size: 8.5pt;
    font-weight: 600;
}
QLabel#MetricValue {
    color: #17324D;
    font-size: 15pt;
    font-weight: 700;
}
QLabel#MetricValue[tone="success"] {
    color: #0F766E;
}
QLabel#MetricValue[tone="danger"] {
    color: #C0392B;
}
QLabel#MetricHint {
    color: #8495A1;
    font-size: 8pt;
}
QLabel#StatusPill {
    border-radius: 10px;
    padding: 4px 12px;
    font-size: 9pt;
    font-weight: 700;
}
QLabel#StatusPill[tone="success"] {
    background: #DDF6ED;
    color: #0F6B5B;
}
QLabel#StatusPill[tone="danger"] {
    background: #FDE8E8;
    color: #B42318;
}
QLabel#StatusPill[tone="warning"] {
    background: #FEF3C7;
    color: #92400E;
}
QLabel#StatusPill[tone="neutral"] {
    background: #E7EEF2;
    color: #4B6273;
}
QLabel#FieldHint {
    color: #7B8B97;
    font-size: 8.5pt;
}
QLabel#WarningBanner {
    background: #FFF7E6;
    border: 1px solid #F6D58B;
    border-radius: 7px;
    color: #8A5A00;
    padding: 9px 12px;
    font-size: 9pt;
}
QLabel#InfoBanner {
    background: #EEF7F6;
    border: 1px solid #C7E7E3;
    border-radius: 7px;
    color: #0F5F57;
    padding: 9px 12px;
    font-size: 9pt;
}
QLabel#PathLabel {
    color: #667987;
    font-size: 9pt;
}
QFrame#ExportOption {
    background: #FFFFFF;
    border: 1px solid #E2EAEF;
    border-radius: 10px;
}
QFrame#ExportOption:hover {
    border-color: #BBD7D3;
    background: #FCFEFE;
}
QLabel#ExportBadge {
    background: #E3F3F1;
    color: #0F5F57;
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}
QDoubleSpinBox#CellSpinBox {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 0 7px;
    min-height: 28px;
}
QDoubleSpinBox#CellSpinBox:focus {
    background: #EAF6F4;
    border: 1px solid #0F766E;
    border-radius: 4px;
}
QDoubleSpinBox#CellSpinBox::up-button,
QDoubleSpinBox#CellSpinBox::down-button {
    width: 0;
    border: none;
}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QPlainTextEdit {
    background: #FFFFFF;
    color: #1F2937;
    border: 1px solid #D5E0E7;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 18px;
    selection-background-color: #0F766E;
    selection-color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0F766E;
}
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled,
QDoubleSpinBox:disabled, QDateEdit:disabled {
    background: #F1F5F7;
    color: #7C8B96;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #D5E0E7;
    selection-background-color: #E3F3F1;
    selection-color: #17324D;
    outline: 0;
}
QDateEdit::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    background: #FFFFFF;
    border: 1px solid #D4E0E7;
    border-radius: 6px;
    padding: 7px 14px;
    color: #314A5C;
    font-weight: 600;
}
QPushButton:hover {
    background: #F0F6F8;
    border-color: #B9CCD7;
}
QPushButton:pressed {
    background: #E5EEF2;
}
QPushButton:disabled {
    color: #9BA8B2;
    background: #F3F6F8;
    border-color: #E2EAEF;
}
QPushButton#PrimaryButton {
    background: #0F766E;
    border: 1px solid #0F766E;
    color: #FFFFFF;
    font-size: 10pt;
    font-weight: 700;
    padding: 9px 20px;
    border-radius: 7px;
}
QPushButton#PrimaryButton:hover {
    background: #0D655E;
    border-color: #0D655E;
}
QPushButton#PrimaryButton:pressed {
    background: #0A554F;
}
QPushButton#SecondaryButton {
    background: #EAF4F3;
    border: 1px solid #C9E3E0;
    color: #0F5F57;
    padding: 7px 14px;
    border-radius: 6px;
}
QPushButton#SecondaryButton:hover {
    background: #DDEFED;
}
QPushButton#GhostButton {
    background: transparent;
    border: 1px solid transparent;
    color: #405969;
    padding: 6px 10px;
}
QPushButton#GhostButton:hover {
    background: #E8F0F4;
}
QPushButton#DangerButton {
    background: #FFFFFF;
    border: 1px solid #E9C4C4;
    color: #B42318;
    padding: 7px 14px;
    border-radius: 6px;
}
QPushButton#DangerButton:hover {
    background: #FDF1F1;
}
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F9FBFC;
    border: 1px solid #E2EAEF;
    border-radius: 7px;
    gridline-color: #EEF3F6;
    selection-background-color: #DDF1EE;
    selection-color: #17324D;
    outline: 0;
}
QTableWidget::item {
    padding: 5px 7px;
    border: none;
}
QHeaderView::section {
    background: #EDF4F6;
    color: #405969;
    border: none;
    border-bottom: 1px solid #DDE7EC;
    padding: 8px 7px;
    font-size: 8.5pt;
    font-weight: 700;
}
QTableCornerButton::section {
    background: #EDF4F6;
    border: none;
}
QPlainTextEdit {
    font-family: "Cascadia Mono", "Consolas", "Microsoft YaHei UI";
    font-size: 9.5pt;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #C3D2DC;
    border-radius: 4px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #A9BDCA;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #C3D2DC;
    border-radius: 4px;
    min-width: 28px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QMenuBar {
    background: #FFFFFF;
    border-bottom: 1px solid #E2EAEF;
    padding: 3px 8px;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background: #EAF2F5;
}
QMenu {
    background: #FFFFFF;
    border: 1px solid #D5E0E7;
    padding: 6px;
}
QMenu::item {
    padding: 7px 28px 7px 18px;
    border-radius: 4px;
}
QMenu::item:selected {
    background: #E3F3F1;
    color: #0F5F57;
}
QStatusBar {
    background: #FFFFFF;
    border-top: 1px solid #E2EAEF;
    color: #667987;
    font-size: 8.5pt;
}
QStatusBar::item {
    border: none;
}
QCheckBox {
    spacing: 7px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
}
QToolTip {
    background: #17324D;
    color: #FFFFFF;
    border: none;
    padding: 6px;
}
"""

