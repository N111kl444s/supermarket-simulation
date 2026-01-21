"""
Dialogs for configuration settings.
Refactored:
- UPDATED: OffsetDialog uses QDoubleSpinBox for precise positioning.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDialogButtonBox,
    QCheckBox,
    QLabel,
    QGroupBox,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal

DIALOG_STYLE = """
    QDialog { background-color: #FFFFFF; color: #000000; font-family: "Segoe UI", sans-serif; }
    QLabel { color: #1F2937; font-weight: 500; font-size: 13px; background-color: transparent; }
    QGroupBox { border: 1px solid #D1D5DB; border-radius: 6px; margin-top: 10px; padding-top: 15px; font-weight: bold; color: #3B82F6; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }
    QSpinBox, QDoubleSpinBox, QComboBox { min-height: 25px; padding: 2px; border: 1px solid #D1D5DB; border-radius: 4px; background-color: #F9FAFB; color: #000000; selection-background-color: #3B82F6; }
    QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { width: 20px; background: #E5E7EB; border: 1px solid #D1D5DB; }
    QPushButton { background-color: #F3F4F6; border: 1px solid #D1D5DB; border-radius: 4px; padding: 6px 12px; color: #1F2937; }
    QPushButton:hover { background-color: #E5E7EB; border-color: #3B82F6; }
"""


class VisibilityDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sichtbarkeit")
        self.setStyleSheet(DIALOG_STYLE)
        self.settings = current_settings.copy()
        self.checks = {}
        layout = QVBoxLayout(self)
        opts = [
            ("show_routes", "Routen anzeigen"),
            ("show_shelves", "Regale anzeigen"),
            ("show_shelf_numbers", "Regal-Nummern anzeigen"),
            ("show_checkouts", "Kassen anzeigen"),
            ("show_checkout_numbers", "Kassen-Nummern anzeigen"),
            ("show_cashiers", "Kassierer anzeigen"),
            ("show_queues", "Warteschlangen anzeigen"),
            ("show_waiting_area", "Wartebereich anzeigen"),
            ("show_start_area", "Startbereich anzeigen"),
            ("show_exit_area", "Ausgangsfläche anzeigen"),
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
        self.settings_changed.emit(
            {k: cb.isChecked() for k, cb in self.checks.items()}
        )


class OffsetDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Globale Offsets (Live)")
        self.resize(450, 600)
        self.setStyleSheet(DIALOG_STYLE)
        self.settings = current_settings.copy()
        self.inputs = {}
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Änderungen werden sofort sichtbar."))

        # --- KUNDEN BEWEGUNG (Float) ---
        gb_move = QGroupBox("Kundenbewegung")
        l_move = QFormLayout(gb_move)
        sb_path = QDoubleSpinBox()
        sb_path.setRange(0, 200)
        sb_path.setValue(float(self.settings.get("customer_path_offset", 10)))
        sb_path.setSuffix(" px")
        sb_path.valueChanged.connect(self.emit_live_update)
        self.inputs["customer_path_offset"] = sb_path
        l_move.addRow("Maximaler Versatz (Jitter):", sb_path)
        layout.addWidget(gb_move)

        # --- WARTESCHLANGEN (Float) ---
        gb_q = QGroupBox("Warteschlangen Offset (Start)")
        l_q = QFormLayout(gb_q)
        self.add_xy_row(l_q, "offset_queue", "Warteschlange (Normal)")
        self.add_xy_row(l_q, "offset_queue_sb", "Warteschlange (SB)")
        layout.addWidget(gb_q)

        # --- KASSIERER & BILDSCHIRM (Float) ---
        gb_c = QGroupBox("Kassierer & Bildschirm Offset")
        l_c = QFormLayout(gb_c)
        self.add_xy_row(l_c, "offset_cashier", "Kassierer")

        self.add_xy_row(l_c, "offset_screen_normal", "Bildschirm (Normal)")
        self.add_xy_row(l_c, "offset_screen_sb", "Bildschirm (SB)")
        layout.addWidget(gb_c)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def add_xy_row(self, layout, prefix, title):
        for suffix in ["_left", "_right"]:
            full_key = prefix + suffix
            val = self.settings.get(full_key, [0, 0])

            # Jetzt QDoubleSpinBox nutzen
            sb_x = QDoubleSpinBox()
            sb_x.setRange(-10000, 10000)
            sb_x.setSingleStep(0.5)
            sb_x.setDecimals(2)
            sb_x.setValue(float(val[0]))
            sb_x.valueChanged.connect(self.emit_live_update)

            sb_y = QDoubleSpinBox()
            sb_y.setRange(-10000, 10000)
            sb_y.setSingleStep(0.5)
            sb_y.setDecimals(2)
            sb_y.setValue(float(val[1]))
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
        if "customer_path_offset" in self.inputs:
            current_data["customer_path_offset"] = self.inputs[
                "customer_path_offset"
            ].value()

        for key, widgets in self.inputs.items():
            if isinstance(widgets, tuple):
                # Float Werte speichern
                current_data[key] = [widgets[0].value(), widgets[1].value()]
        self.settings_changed.emit(current_data)


class CheckoutConfigDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Kasse #{data['id']} konfigurieren")
        self.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        lbl_header = QLabel(f"Einstellungen für Kasse {data['id']}")
        lbl_header.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #1F2937;"
        )
        layout.addWidget(lbl_header)
        form = QFormLayout()
        form.setSpacing(10)
        self.sb_queue = QSpinBox()
        self.sb_queue.setRange(1, 50)
        self.sb_queue.setValue(data.get("max_queue", 5))
        form.addRow("Max. Warteschlange:", self.sb_queue)
        self.combo_staff = QComboBox()
        self.combo_staff.addItems(["Azubi", "Festangestellter"])
        current_staff = (
            data.get("cashier_skill") or data.get("skill") or "Azubi"
        )
        self.combo_staff.setCurrentText(current_staff)
        if data.get("type") == "SB":
            self.combo_staff.setDisabled(True)
            self.combo_staff.setToolTip("SB-Kassen haben kein Personal.")
        form.addRow("Mitarbeiter:", self.combo_staff)
        self.cb_open = QCheckBox("Kasse geöffnet")
        self.cb_open.setChecked(data.get("open", True))
        form.addRow("", self.cb_open)
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
            "cashier_skill": self.combo_staff.currentText(),
        }


class ObjectPositionDialog(QDialog):
    position_changed = pyqtSignal(float, float)
    orientation_changed = pyqtSignal(str)
    angle_changed = pyqtSignal(int)
    variant_changed = pyqtSignal(int)

    def __init__(
        self, title, x, y, orientation=None, angle=0, variant=None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.sb_x = QDoubleSpinBox()
        self.sb_x.setRange(-10000, 10000)
        self.sb_x.setSingleStep(0.1)
        self.sb_x.setValue(x)
        self.sb_y = QDoubleSpinBox()
        self.sb_y.setRange(-10000, 10000)
        self.sb_y.setSingleStep(0.1)
        self.sb_y.setValue(y)
        form.addRow("X:", self.sb_x)
        form.addRow("Y:", self.sb_y)
        if orientation is not None:
            self.combo_ori = QComboBox()
            self.combo_ori.addItems(["Left", "Right"])
            self.combo_ori.setCurrentText(orientation)
            self.combo_ori.currentTextChanged.connect(
                self.orientation_changed.emit
            )
            form.addRow("Typ:", self.combo_ori)
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
        if variant is not None:
            self.sb_var = QSpinBox()
            self.sb_var.setRange(1, 5)
            self.sb_var.setValue(variant)
            self.sb_var.valueChanged.connect(self.emit_variant)
            form.addRow("Variante:", self.sb_var)
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

    def emit_variant(self):
        self.variant_changed.emit(self.sb_var.value())
