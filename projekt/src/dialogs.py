from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QSpinBox,
    QPushButton,
    QVBoxLayout,
    QTabWidget,
    QWidget,
    QCheckBox,
    QGridLayout,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal


class ObjectPositionDialog(QDialog):
    position_changed = pyqtSignal(float, float)

    def __init__(self, item_name, current_x, current_y, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Pos. bearbeiten: {item_name}")
        self.resize(300, 150)
        self.layout = QFormLayout(self)
        self.spin_x = QSpinBox()
        self.spin_x.setRange(0, 2000)
        self.spin_x.setValue(int(current_x))
        self.spin_x.valueChanged.connect(self.on_change)
        self.spin_y = QSpinBox()
        self.spin_y.setRange(0, 2000)
        self.spin_y.setValue(int(current_y))
        self.spin_y.valueChanged.connect(self.on_change)
        self.layout.addRow("Position X:", self.spin_x)
        self.layout.addRow("Position Y:", self.spin_y)
        btn_close = QPushButton("Fertig")
        btn_close.clicked.connect(self.accept)
        self.layout.addRow(btn_close)

    def on_change(self):
        self.position_changed.emit(self.spin_x.value(), self.spin_y.value())


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.resize(500, 700)
        self.settings = current_settings.copy()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # TAB 1: Ansicht
        tab_view = QWidget()
        form_view = QFormLayout(tab_view)
        self.chk_routes = QCheckBox()
        self.chk_routes.setChecked(self.settings["show_routes"])
        self.chk_shelves = QCheckBox()
        self.chk_shelves.setChecked(self.settings["show_shelves"])
        self.chk_checkouts = QCheckBox()
        self.chk_checkouts.setChecked(self.settings["show_checkouts"])
        self.chk_cashiers = QCheckBox()
        self.chk_cashiers.setChecked(self.settings["show_cashiers"])
        self.chk_waiting = QCheckBox()
        self.chk_waiting.setChecked(
            self.settings.get("show_waiting_area", True)
        )

        self.chk_routes.toggled.connect(
            lambda v: self.update_setting("show_routes", v)
        )
        self.chk_shelves.toggled.connect(
            lambda v: self.update_setting("show_shelves", v)
        )
        self.chk_checkouts.toggled.connect(
            lambda v: self.update_setting("show_checkouts", v)
        )
        self.chk_cashiers.toggled.connect(
            lambda v: self.update_setting("show_cashiers", v)
        )
        self.chk_waiting.toggled.connect(
            lambda v: self.update_setting("show_waiting_area", v)
        )

        form_view.addRow("Routen anzeigen:", self.chk_routes)
        form_view.addRow("Regale anzeigen:", self.chk_shelves)
        form_view.addRow("Kassen anzeigen:", self.chk_checkouts)
        form_view.addRow("Kassierer & Licht:", self.chk_cashiers)
        form_view.addRow("Wartebereich:", self.chk_waiting)
        tabs.addTab(tab_view, "Ansicht")

        # TAB 2: Layout
        tab_layout = QWidget()
        grid = QGridLayout(tab_layout)

        def add_pos_row(title, key_l, key_r, start_row):
            grid.addWidget(QLabel(f"<b>{title}</b>"), start_row, 0, 1, 4)
            grid.addWidget(QLabel("Links X:"), start_row + 1, 0)
            slx = self.create_spin(key_l, 0)
            grid.addWidget(slx, start_row + 1, 1)
            grid.addWidget(QLabel("Links Y:"), start_row + 1, 2)
            sly = self.create_spin(key_l, 1)
            grid.addWidget(sly, start_row + 1, 3)
            grid.addWidget(QLabel("Rechts X:"), start_row + 2, 0)
            srx = self.create_spin(key_r, 0)
            grid.addWidget(srx, start_row + 2, 1)
            grid.addWidget(QLabel("Rechts Y:"), start_row + 2, 2)
            sry = self.create_spin(key_r, 1)
            grid.addWidget(sry, start_row + 2, 3)
            return start_row + 4

        row = 0
        row = add_pos_row(
            "Kassierer Position",
            "offset_cashier_left",
            "offset_cashier_right",
            row,
        )
        row = add_pos_row(
            "Licht Position (Normal)",
            "offset_light_normal_left",
            "offset_light_normal_right",
            row,
        )
        row = add_pos_row(
            "Licht Position (SB)",
            "offset_light_sb_left",
            "offset_light_sb_right",
            row,
        )
        row = add_pos_row(
            "Warteschlange (Normal)",
            "offset_queue_left",
            "offset_queue_right",
            row,
        )
        row = add_pos_row(
            "Warteschlange (SB)",
            "offset_queue_sb_left",
            "offset_queue_sb_right",
            row,
        )

        tabs.addTab(tab_layout, "Layout")
        layout.addWidget(tabs)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def create_spin(self, key, index):
        sb = QSpinBox()
        sb.setRange(-200, 200)
        sb.setValue(self.settings[key][index])
        sb.valueChanged.connect(lambda v: self.update_offset(key, index, v))
        return sb

    def update_setting(self, key, value):
        self.settings[key] = value
        self.settings_changed.emit(self.settings)

    def update_offset(self, key, index, value):
        self.settings[key][index] = value
        self.settings_changed.emit(self.settings)
