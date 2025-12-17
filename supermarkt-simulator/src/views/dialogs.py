"""
Dialogs for the application (Visibility, Offsets, Object Positioning, Checkout Config).
Refactored: Split SettingsDialog into VisibilityDialog and OffsetDialog.
Refactored: OffsetDialog made larger (taller).
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QSpinBox,
    QDoubleSpinBox,
    QLabel,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal
from config import COLOR_SUCCESS, COLOR_ERROR


class OffsetWidget(QWidget):
    """
    Helper widget to edit an X/Y offset pair.
    Emits valueChanged signal when either spinbox changes.
    """

    valueChanged = pyqtSignal()

    def __init__(self, x, y, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sb_x = QSpinBox()
        self.sb_x.setRange(-300, 300)  # Increased range
        self.sb_x.setValue(int(x))
        self.sb_x.setSuffix(" px")
        self.sb_x.setToolTip("X-Offset")

        self.sb_y = QSpinBox()
        self.sb_y.setRange(-300, 300)
        self.sb_y.setValue(int(y))
        self.sb_y.setSuffix(" px")
        self.sb_y.setToolTip("Y-Offset")

        layout.addWidget(QLabel("X:"))
        layout.addWidget(self.sb_x)
        layout.addWidget(QLabel("Y:"))
        layout.addWidget(self.sb_y)

        # Connect signals
        self.sb_x.valueChanged.connect(self.valueChanged.emit)
        self.sb_y.valueChanged.connect(self.valueChanged.emit)

    def get_values(self):
        return [self.sb_x.value(), self.sb_y.value()]


class VisibilityDialog(QDialog):
    """
    Dialog specifically for toggling visibility of simulation elements.
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sichtbarkeit")
        self.resize(300, 250)
        self.settings = current_settings.copy()
        self.widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        gb_view = QGroupBox("Elemente anzeigen")
        fl_view = QFormLayout(gb_view)

        view_keys = [
            "show_routes",
            "show_shelves",
            "show_checkouts",
            "show_cashiers",
            "show_waiting_area",
        ]

        for key in view_keys:
            cb = QCheckBox()
            cb.setChecked(self.settings.get(key, True))
            cb.clicked.connect(self.emit_settings)
            fl_view.addRow(key.replace("show_", "Zeige "), cb)
            self.widgets[key] = cb

        layout.addWidget(gb_view)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(
            self.accept
        )  # Close acts as OK here since we have live updates
        layout.addWidget(buttons)

    def emit_settings(self):
        self.settings_changed.emit(self.get_settings())

    def get_settings(self):
        for k, w in self.widgets.items():
            self.settings[k] = w.isChecked()
        return self.settings


class OffsetDialog(QDialog):
    """
    Dialog specifically for tweaking global positioning offsets.
    Made taller as requested.
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Globale Offsets")
        self.resize(450, 700)  # Taller window
        self.settings = current_settings.copy()
        self.widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # -- Group: Warteschlange (Queue) --
        gb_queue = QGroupBox("Warteschlangen-Startpunkt")
        fl_queue = QFormLayout(gb_queue)
        self.add_offset_row(fl_queue, "Normal (Links)", "offset_queue_left")
        self.add_offset_row(fl_queue, "Normal (Rechts)", "offset_queue_right")
        self.add_offset_row(fl_queue, "SB (Links)", "offset_queue_sb_left")
        self.add_offset_row(fl_queue, "SB (Rechts)", "offset_queue_sb_right")
        content_layout.addWidget(gb_queue)

        # -- Group: Kassierer (Cashier) --
        gb_cashier = QGroupBox("Kassierer-Position")
        fl_cashier = QFormLayout(gb_cashier)
        self.add_offset_row(
            fl_cashier, "Normal (Links)", "offset_cashier_left"
        )
        self.add_offset_row(
            fl_cashier, "Normal (Rechts)", "offset_cashier_right"
        )
        content_layout.addWidget(gb_cashier)

        # -- Group: Status-Licht (Light) --
        gb_light = QGroupBox("Status-Licht")
        fl_light = QFormLayout(gb_light)
        self.add_offset_row(
            fl_light, "Normal (Links)", "offset_light_normal_left"
        )
        self.add_offset_row(
            fl_light, "Normal (Rechts)", "offset_light_normal_right"
        )
        self.add_offset_row(fl_light, "SB (Links)", "offset_light_sb_left")
        self.add_offset_row(fl_light, "SB (Rechts)", "offset_light_sb_right")
        content_layout.addWidget(gb_light)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def add_offset_row(self, layout, label, key):
        val = self.settings.get(key, [0, 0])
        widget = OffsetWidget(val[0], val[1])
        widget.valueChanged.connect(self.emit_settings)
        layout.addRow(label + ":", widget)
        self.widgets[key] = widget

    def emit_settings(self):
        self.settings_changed.emit(self.get_settings())

    def get_settings(self):
        for k, w in self.widgets.items():
            self.settings[k] = w.get_values()
        return self.settings


class ObjectPositionDialog(QDialog):
    """
    Dialog to edit the position of an object.
    """

    position_changed = pyqtSignal(float, float)

    def __init__(self, name, x, y, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Bearbeiten: {name}")
        self.x = x
        self.y = y
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sb_x = QDoubleSpinBox()
        self.sb_x.setRange(-1000, 3000)
        self.sb_x.setValue(self.x)

        self.sb_y = QDoubleSpinBox()
        self.sb_y.setRange(-1000, 3000)
        self.sb_y.setValue(self.y)

        form.addRow("X:", self.sb_x)
        form.addRow("Y:", self.sb_y)
        layout.addLayout(form)

        self.sb_x.valueChanged.connect(self.emit_change)
        self.sb_y.valueChanged.connect(self.emit_change)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def emit_change(self):
        self.position_changed.emit(self.sb_x.value(), self.sb_y.value())


class CheckoutConfigDialog(QDialog):
    """
    Dialog to configure a specific checkout (Status, Skill, Queue Limit).
    """

    def __init__(self, checkout_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Konfiguration Kasse #{checkout_data.get('id')}")
        self.data = checkout_data.copy()
        self.is_open = self.data.get("open", True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Status Toggle
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(10)

        self.btn_open = QPushButton("Geöffnet")
        self.btn_open.setCheckable(True)
        self.btn_open.setFixedHeight(30)
        self.btn_open.clicked.connect(lambda: self.set_status(True))

        self.btn_closed = QPushButton("Geschlossen")
        self.btn_closed.setCheckable(True)
        self.btn_closed.setFixedHeight(30)
        self.btn_closed.clicked.connect(lambda: self.set_status(False))

        status_layout.addWidget(self.btn_open)
        status_layout.addWidget(self.btn_closed)
        form.addRow("Status:", status_widget)

        # Skill (Normal only)
        self.combo_skill = None
        if self.data.get("type") == "Normal":
            self.combo_skill = QComboBox()
            self.combo_skill.addItems(["Azubi", "Erfahren", "Profi"])
            current_skill = self.data.get("skill", "Azubi")
            self.combo_skill.setCurrentText(
                current_skill if current_skill else "Azubi"
            )
            form.addRow("Kassierer-Skill:", self.combo_skill)

        # Queue
        self.sb_queue = QSpinBox()
        self.sb_queue.setRange(1, 50)
        self.sb_queue.setValue(self.data.get("max_queue", 5))
        form.addRow("Max. Warteschlange:", self.sb_queue)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.update_toggle_buttons()

    def set_status(self, open_status):
        self.is_open = open_status
        self.update_toggle_buttons()

    def update_toggle_buttons(self):
        base_style = "border-radius: 4px; padding: 6px;"
        if self.is_open:
            self.btn_open.setStyleSheet(
                f"background-color: {COLOR_SUCCESS.name()}; color: white; font-weight: bold; border: 1px solid {COLOR_SUCCESS.name()};"
            )
            self.btn_open.setChecked(True)
            self.btn_closed.setStyleSheet(base_style)
            self.btn_closed.setChecked(False)
        else:
            self.btn_open.setStyleSheet(base_style)
            self.btn_open.setChecked(False)
            self.btn_closed.setStyleSheet(
                f"background-color: {COLOR_ERROR.name()}; color: white; font-weight: bold; border: 1px solid {COLOR_ERROR.name()};"
            )
            self.btn_closed.setChecked(True)

    def get_data(self):
        self.data["open"] = self.is_open
        self.data["max_queue"] = self.sb_queue.value()
        if self.data["type"] == "Normal" and self.combo_skill:
            self.data["skill"] = self.combo_skill.currentText()
        return self.data
