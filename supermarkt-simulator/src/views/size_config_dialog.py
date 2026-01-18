"""
Size Configuration Dialog.
Refactored: 
- Added Queue Dot Size, Spacing, Light Size controls.
- Enables Live Updates.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QSpinBox, QDialogButtonBox, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from config import SHELF_SIZE, CUSTOMER_SIZE, CASHIER_SIZE, CHECKOUT_WIDTH, CHECKOUT_HEIGHT

DIALOG_STYLE = """
    QDialog { background-color: #FFFFFF; font-family: "Segoe UI"; }
    QLabel { color: #1F2937; font-weight: bold; }
    QSpinBox { padding: 4px; border: 1px solid #D1D5DB; border-radius: 4px; background: #F9FAFB; }
    QGroupBox { border: 1px solid #D1D5DB; border-radius: 6px; margin-top: 10px; padding-top: 15px; font-weight: bold; color: #3B82F6; }
    QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }
"""

class SizeConfigDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Größen & Skalierung")
        self.resize(400, 600)
        self.setStyleSheet(DIALOG_STYLE)
        self.settings = current_settings.copy()
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Werte werden sofort übernommen."))

        # --- OBJETS ---
        gb_obj = QGroupBox("Objekt Größen")
        l_obj = QFormLayout(gb_obj)
        
        self.sb_shelf = self._add_row(l_obj, "Regal Größe:", "size_shelf", SHELF_SIZE, 10, 200)
        self.sb_cust = self._add_row(l_obj, "Kunde Größe:", "size_customer", CUSTOMER_SIZE, 10, 100)
        self.sb_cashier = self._add_row(l_obj, "Kassierer Größe:", "size_cashier", CASHIER_SIZE, 10, 150)
        
        self.sb_cw = self._add_row(l_obj, "Kasse Breite:", "size_checkout_width", CHECKOUT_WIDTH, 20, 300)
        self.sb_ch = self._add_row(l_obj, "Kasse Höhe:", "size_checkout_height", CHECKOUT_HEIGHT, 20, 300)
        
        layout.addWidget(gb_obj)

        # --- DETAILS ---
        gb_det = QGroupBox("Details & Indikatoren")
        l_det = QFormLayout(gb_det)
        
        self.sb_q_dot = self._add_row(l_det, "Warteschlange Punkt:", "size_queue_dot", 4, 1, 20)
        self.sb_q_space = self._add_row(l_det, "Warteschlange Abstand:", "dist_queue_spacing", 20, 5, 100)
        self.sb_light = self._add_row(l_det, "Kassenampel Größe:", "size_checkout_light", 8, 2, 40)
        
        layout.addWidget(gb_det)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def _add_row(self, layout, label, key, default, min_v, max_v):
        sb = QSpinBox()
        sb.setRange(min_v, max_v)
        sb.setValue(int(self.settings.get(key, default)))
        sb.setSuffix(" px")
        sb.valueChanged.connect(lambda v, k=key: self.emit_change(k, v))
        layout.addRow(label, sb)
        return sb

    def emit_change(self, key, value):
        self.settings[key] = value
        self.settings_changed.emit(self.settings)