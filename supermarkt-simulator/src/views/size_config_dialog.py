"""
Size Configuration Dialog.
Refactored:
- UPDATED: Uses QDoubleSpinBox for Screen dimensions to allow precision.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
)
from PyQt6.QtCore import pyqtSignal
from config import (
    SHELF_SIZE,
    CUSTOMER_SIZE,
    CASHIER_SIZE,
    CHECKOUT_WIDTH,
    CHECKOUT_HEIGHT,
    COLOR_BG_MAIN,
)


class SizeConfigDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Größen & Skalierung")
        self.resize(400, 700)
        # Use global app background color for consistency
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.settings = current_settings.copy()

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Werte werden sofort übernommen."))

        # --- OBJETS ---
        gb_obj = QGroupBox("Objekt Größen")
        l_obj = QFormLayout(gb_obj)

        self.sb_shelf = self._add_row(
            l_obj, "Regal Größe:", "size_shelf", SHELF_SIZE, 10, 200
        )
        self.sb_cust = self._add_row(
            l_obj, "Kunde Größe:", "size_customer", CUSTOMER_SIZE, 10, 100
        )
        self.sb_cashier = self._add_row(
            l_obj, "Kassierer Größe:", "size_cashier", CASHIER_SIZE, 10, 150
        )

        self.sb_cw = self._add_row(
            l_obj,
            "Kasse Breite:",
            "size_checkout_width",
            CHECKOUT_WIDTH,
            20,
            300,
        )
        self.sb_ch = self._add_row(
            l_obj,
            "Kasse Höhe:",
            "size_checkout_height",
            CHECKOUT_HEIGHT,
            20,
            300,
        )

        layout.addWidget(gb_obj)

        # --- DETAILS ---
        gb_det = QGroupBox("Details & Indikatoren")
        l_det = QFormLayout(gb_det)

        self.sb_q_dot = self._add_double_row(
            l_det, "Warteschlange Punkt:", "size_queue_dot", 4.0, 0.5, 20.0
        )
        self.sb_q_space = self._add_double_row(
            l_det,
            "Warteschlange Abstand:",
            "dist_queue_spacing",
            20.0,
            1.0,
            100.0,
        )

        layout.addWidget(gb_det)

        # --- SCREENS (Präzise Einstellung) ---
        gb_screen = QGroupBox("Kassenbildschirm")
        l_screen = QFormLayout(gb_screen)

        self.sb_scr_n_w = self._add_double_row(
            l_screen,
            "Normal Breite:",
            "size_screen_normal_width",
            15.0,
            0.1,
            100.0,
        )
        self.sb_scr_n_h = self._add_double_row(
            l_screen,
            "Normal Höhe:",
            "size_screen_normal_height",
            10.0,
            0.1,
            100.0,
        )

        self.sb_scr_sb_w = self._add_double_row(
            l_screen, "SB Breite:", "size_screen_sb_width", 10.0, 0.1, 100.0
        )
        self.sb_scr_sb_h = self._add_double_row(
            l_screen, "SB Höhe:", "size_screen_sb_height", 10.0, 0.1, 100.0
        )

        layout.addWidget(gb_screen)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _add_row(self, layout, label, key, default, min_v, max_v):
        """Standard Integer SpinBox"""
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(int(self.settings.get(key, default)))
        sb.setSuffix(" px")
        sb.valueChanged.connect(lambda v, k=key: self.emit_change(k, v))
        layout.addRow(label, sb)
        return sb

    def _add_double_row(self, layout, label, key, default, min_v, max_v):
        """Float DoubleSpinBox für präzise Werte"""
        sb = QDoubleSpinBox()
        sb.setRange(min_v, max_v)
        sb.setSingleStep(0.5)
        sb.setDecimals(2)
        sb.setValue(float(self.settings.get(key, default)))
        sb.setSuffix(" px")
        sb.valueChanged.connect(lambda v, k=key: self.emit_change(k, v))
        layout.addRow(label, sb)
        return sb

    def emit_change(self, key, value):
        self.settings[key] = value
        self.settings_changed.emit(self.settings)
