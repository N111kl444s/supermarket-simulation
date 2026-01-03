"""
Dialog for configuring global object sizes.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDialogButtonBox,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal


class SizeConfigDialog(QDialog):
    """
    Dialog to edit the global sizes of simulation objects.
    """

    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Größen Konfiguration")
        self.settings = current_settings.copy()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Ändern Sie die globalen Anzeigegrößen der Objekte.\n"
            "Hinweis: Änderungen werden sofort wirksam und gespeichert."
        )
        layout.addWidget(info)

        form = QFormLayout()

        self.spin_customer = self._create_spin("size_customer")
        form.addRow("Kunden Größe (px):", self.spin_customer)

        self.spin_shelf = self._create_spin("size_shelf")
        form.addRow("Regal Größe (px):", self.spin_shelf)

        self.spin_cashier = self._create_spin("size_cashier")
        form.addRow("Kassierer Größe (px):", self.spin_cashier)

        self.spin_co_w = self._create_spin("size_checkout_width")
        form.addRow("Kasse Breite (px):", self.spin_co_w)

        self.spin_co_h = self._create_spin("size_checkout_height")
        form.addRow("Kasse Höhe (px):", self.spin_co_h)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _create_spin(self, key):
        spin = QSpinBox()
        spin.setRange(5, 500)
        spin.setValue(self.settings.get(key, 32))
        spin.valueChanged.connect(lambda v: self.update_setting(key, v))
        return spin

    def update_setting(self, key, value):
        self.settings[key] = value
        self.settings_changed.emit({key: value})

    def get_settings(self):
        return self.settings