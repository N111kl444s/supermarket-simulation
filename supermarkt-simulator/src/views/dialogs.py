"""
Dialogs for configuration settings.
Refactored:
- CheckoutConfigDialog: White styled, added Cashier Type selection (Azubi/Pro).
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
from PyQt6.QtCore import pyqtSignal, Qt
from config import COLOR_ACCENT, COLOR_BORDER, COLOR_TEXT_MAIN


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
            cb.stateChanged.connect(self.emit_live_update)
            self.checks[key] = cb
            layout.addWidget(cb)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def emit_live_update(self):
        new_settings = {k: cb.isChecked() for k, cb in self.checks.items()}
        self.settings_changed.emit(new_settings)


class OffsetDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Globale Offsets (Live)")
        self.resize(400, 500)
        self.settings = current_settings.copy()
        self.inputs = {}
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Änderungen werden sofort sichtbar."))

        gb_move = QGroupBox("Kundenbewegung")
        l_move = QFormLayout(gb_move)
        sb_path = QSpinBox()
        sb_path.setRange(0, 200)
        sb_path.setValue(int(self.settings.get("customer_path_offset", 10)))
        sb_path.setSuffix(" px")
        sb_path.valueChanged.connect(self.emit_live_update)
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

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def add_xy_row(self, layout, prefix, title):
        for suffix in ["_left", "_right"]:
            full_key = prefix + suffix
            val = self.settings.get(full_key, [0, 0])
            
            sb_x = QSpinBox()
            sb_x.setRange(-10000, 10000)
            sb_x.setValue(int(val[0]))
            sb_x.valueChanged.connect(self.emit_live_update)
            
            sb_y = QSpinBox()
            sb_y.setRange(-10000, 10000)
            sb_y.setValue(int(val[1]))
            sb_y.valueChanged.connect(self.emit_live_update)
            
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

    def emit_live_update(self):
        current_data = self.settings.copy()
        current_data["customer_path_offset"] = self.inputs["customer_path_offset"].value()
        for key, widgets in self.inputs.items():
            if key == "customer_path_offset":
                continue
            current_data[key] = [widgets[0].value(), widgets[1].value()]
        
        self.settings_changed.emit(current_data)


class CheckoutConfigDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Kasse #{data['id']} konfigurieren")
        
        # Style: Weißer Hintergrund, moderne Schrift
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #FFFFFF;
                font-family: "Segoe UI", sans-serif;
                color: {COLOR_TEXT_MAIN.name()};
            }}
            QLabel {{
                font-weight: 500;
                font-size: 14px;
            }}
            QCheckBox {{
                font-size: 14px;
                padding: 5px;
            }}
            QComboBox, QSpinBox {{
                border: 1px solid {COLOR_BORDER.name()};
                border-radius: 4px;
                padding: 4px;
                background-color: #F9FAFB;
                min-height: 25px;
            }}
            QComboBox:hover, QSpinBox:hover {{
                border: 1px solid {COLOR_ACCENT.name()};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        lbl_header = QLabel(f"Einstellungen für Kasse {data['id']}")
        lbl_header.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_header)

        form = QFormLayout()
        form.setSpacing(10)

        # 1. Warteschlange
        self.sb_queue = QSpinBox()
        self.sb_queue.setRange(1, 50)
        self.sb_queue.setValue(data.get("max_queue", 5))
        form.addRow("Max. Warteschlange:", self.sb_queue)

        # 2. Personal (Skill) - Nur relevant, wenn KEINE SB-Kasse (falls SB Kassen keine Kassierer haben)
        # Wir zeigen es immer an, außer du willst es für SB deaktivieren.
        self.combo_staff = QComboBox()
        self.combo_staff.addItems(["Azubi", "Festangestellter"])
        # Standard ist Festangestellter, falls nichts gesetzt
        current_staff = data.get("cashier_skill", "Festangestellter")
        self.combo_staff.setCurrentText(current_staff)
        form.addRow("Mitarbeiter:", self.combo_staff)

        # 3. Status
        self.cb_open = QCheckBox("Kasse geöffnet")
        self.cb_open.setChecked(data.get("open", True))
        form.addRow("", self.cb_open)

        layout.addLayout(form)
        
        # Buttons
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
            "cashier_skill": self.combo_staff.currentText()
        }


class ObjectPositionDialog(QDialog):
    position_changed = pyqtSignal(float, float)
    orientation_changed = pyqtSignal(str)
    angle_changed = pyqtSignal(int)

    def __init__(self, title, x, y, orientation=None, angle=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        # Auch hier ein leichter Clean-Look
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; font-family: "Segoe UI"; }
            QLabel { font-size: 13px; }
            QDoubleSpinBox, QComboBox { min-height: 25px; }
        """)
        
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

        if orientation is not None:
            self.combo_ori = QComboBox()
            self.combo_ori.addItems(["Left", "Right"])
            self.combo_ori.setCurrentText(orientation)
            self.combo_ori.currentTextChanged.connect(self.orientation_changed.emit)
            form.addRow("Typ:", self.combo_ori)
        
        if orientation is not None:
            self.combo_angle = QComboBox()
            self.combo_angle.addItem("0°", 0)
            self.combo_angle.addItem("90°", 90)
            self.combo_angle.addItem("180°", 180)
            self.combo_angle.addItem("270°", 270)
            idx = self.combo_angle.findData(angle)
            if idx != -1:
                self.combo_angle.setCurrentIndex(idx)
            self.combo_angle.currentIndexChanged.connect(self.emit_angle)
            form.addRow("Rotation:", self.combo_angle)

        layout.addLayout(form)
        
        self.sb_x.valueChanged.connect(self.emit_pos)
        self.sb_y.valueChanged.connect(self.emit_pos)
        
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def emit_pos(self):
        self.position_changed.emit(self.sb_x.value(), self.sb_y.value())

    def emit_angle(self):
        val = self.combo_angle.currentData()
        self.angle_changed.emit(val)
