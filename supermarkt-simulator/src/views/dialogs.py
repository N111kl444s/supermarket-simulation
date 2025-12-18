"""
Dialogs for configuration settings.
Refactored: Removed Exit Direction from CheckoutConfigDialog (now global).
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDialogButtonBox,
    QCheckBox,
    QLabel,
    QDoubleSpinBox,
    QGroupBox,
    QWidget,
    QHBoxLayout,
    QComboBox,
)
from PyQt6.QtCore import pyqtSignal


class VisibilityDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sichtbarkeit")
        self.settings = current_settings.copy()
        self.checks = {}

        layout = QVBoxLayout(self)
        opts = [
            ("show_routes", "Routen anzeigen"),
            ("show_shelves", "Regale anzeigen"),
            ("show_checkouts", "Kassen anzeigen"),
            ("show_cashiers", "Kassierer anzeigen"),
            ("show_waiting_area", "Wartebereich anzeigen"),
            ("show_start_area", "Startbereich anzeigen"),
        ]

        for key, label in opts:
            cb = QCheckBox(label)
            cb.setChecked(self.settings.get(key, True))
            self.checks[key] = cb
            layout.addWidget(cb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        new_settings = {k: cb.isChecked() for k, cb in self.checks.items()}
        self.settings_changed.emit(new_settings)
        super().accept()


class OffsetDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Globale Offsets")
        self.resize(400, 500)
        self.settings = current_settings.copy()
        self.inputs = {}
        layout = QVBoxLayout(self)
        form = QFormLayout()

        gb_move = QGroupBox("Kundenbewegung")
        l_move = QFormLayout(gb_move)
        sb_path = QSpinBox()
        sb_path.setRange(0, 50)
        sb_path.setValue(int(self.settings.get("customer_path_offset", 10)))
        sb_path.setSuffix(" px")
        self.inputs["customer_path_offset"] = sb_path
        l_move.addRow("Maximaler Versatz (Jitter):", sb_path)
        layout.addWidget(gb_move)

        gb_q = QGroupBox("Warteschlangen Position")
        l_q = QFormLayout(gb_q)
        self.add_xy_row(l_q, "offset_queue", "Warteschlange (Normal)")
        self.add_xy_row(l_q, "offset_queue_sb", "Warteschlange (SB)")
        layout.addWidget(gb_q)

        gb_c = QGroupBox("Kassierer & Ampel")
        l_c = QFormLayout(gb_c)
        self.add_xy_row(l_c, "offset_cashier", "Kassierer")
        self.add_xy_row(l_c, "offset_light_normal", "Ampel (Normal)")
        self.add_xy_row(l_c, "offset_light_sb", "Ampel (SB)")
        layout.addWidget(gb_c)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_xy_row(self, layout, prefix, title):
        for suffix in ["_left", "_right"]:
            full_key = prefix + suffix
            val = self.settings.get(full_key, [0, 0])
            sb_x = QSpinBox()
            sb_x.setRange(-100, 100)
            sb_x.setValue(int(val[0]))
            sb_y = QSpinBox()
            sb_y.setRange(-100, 100)
            sb_y.setValue(int(val[1]))
            layout.addRow(
                f"{title} ({'Links' if 'left' in suffix else 'Rechts'}) X/Y:",
                self.create_hbox(sb_x, sb_y),
            )
            self.inputs[full_key] = (sb_x, sb_y)

    def create_hbox(self, w1, w2):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.addWidget(w1)
        l.addWidget(w2)
        return w

    def accept(self):
        self.settings["customer_path_offset"] = self.inputs[
            "customer_path_offset"
        ].value()
        for key, widgets in self.inputs.items():
            if key == "customer_path_offset":
                continue
            self.settings[key] = [widgets[0].value(), widgets[1].value()]
        self.settings_changed.emit(self.settings)
        super().accept()


class CheckoutConfigDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Konfiguration Kasse #{data['id']}")
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.sb_queue = QSpinBox()
        self.sb_queue.setRange(1, 20)
        self.sb_queue.setValue(data.get("max_queue", 5))
        form.addRow("Max. Warteschlange:", self.sb_queue)

        # Exit Direction removed here (it's global now)

        self.cb_open = QCheckBox("Geöffnet")
        self.cb_open.setChecked(data.get("open", True))
        form.addRow(self.cb_open)

        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "max_queue": self.sb_queue.value(),
            "open": self.cb_open.isChecked(),
        }


class ObjectPositionDialog(QDialog):
    position_changed = pyqtSignal(float, float)

    def __init__(self, title, x, y, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.sb_x = QDoubleSpinBox()
        self.sb_x.setRange(-10000, 10000)
        self.sb_x.setValue(x)
        self.sb_y = QDoubleSpinBox()
        self.sb_y.setRange(-10000, 10000)
        self.sb_y.setValue(y)
        form.addRow("X:", self.sb_x)
        form.addRow("Y:", self.sb_y)
        layout.addLayout(form)
        self.sb_x.valueChanged.connect(self.emit_change)
        self.sb_y.valueChanged.connect(self.emit_change)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def emit_change(self):
        self.position_changed.emit(self.sb_x.value(), self.sb_y.value())
