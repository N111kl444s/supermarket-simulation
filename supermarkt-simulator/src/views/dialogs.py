"""
Dialogs Module.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QSpinBox,
    QDoubleSpinBox,
    QComboBox,
    QCheckBox,
    QLabel,
    QGroupBox,
    QWidget,
    QTabWidget,
)
from PyQt6.QtCore import pyqtSignal, Qt
from config import COLOR_BG_MAIN

# ... (ObjectPositionDialog und CheckoutConfigDialog bleiben unverändert, hier weggelassen zur Kürze) ...
# Bitte den Code für ObjectPositionDialog und CheckoutConfigDialog aus deiner bestehenden Datei beibehalten.
# Ich zeige hier nur VisibilityDialog und OffsetDialog updates.


class ObjectPositionDialog(QDialog):
    # ... (Code beibehalten) ...
    position_changed = pyqtSignal(float, float)
    angle_changed = pyqtSignal(float)
    orientation_changed = pyqtSignal(str)
    variant_changed = pyqtSignal(int)

    def __init__(
        self, title, x, y, orientation=None, angle=0, variant=None, parent=None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.x = x
        self.y = y
        self.orientation = orientation
        self.angle = angle
        self.variant = variant
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setValue(self.x)
        self.spin_x.valueChanged.connect(self._on_pos_changed)

        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setValue(self.y)
        self.spin_y.valueChanged.connect(self._on_pos_changed)

        form.addRow("X:", self.spin_x)
        form.addRow("Y:", self.spin_y)

        self.spin_angle = QDoubleSpinBox()
        self.spin_angle.setRange(0, 360)
        self.spin_angle.setValue(self.angle)
        self.spin_angle.valueChanged.connect(
            lambda v: self.angle_changed.emit(v)
        )
        form.addRow("Winkel:", self.spin_angle)

        if self.orientation is not None:
            self.combo_ori = QComboBox()
            self.combo_ori.addItems(["Left", "Right"])
            self.combo_ori.setCurrentText(self.orientation)
            self.combo_ori.currentTextChanged.connect(
                lambda t: self.orientation_changed.emit(t)
            )
            form.addRow("Ausrichtung:", self.combo_ori)

        if self.variant is not None:
            self.spin_var = QSpinBox()
            self.spin_var.setRange(1, 5)  # Annahme
            self.spin_var.setValue(self.variant)
            self.spin_var.valueChanged.connect(
                lambda v: self.variant_changed.emit(v)
            )
            form.addRow("Variante:", self.spin_var)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)

    def _on_pos_changed(self):
        self.position_changed.emit(self.spin_x.value(), self.spin_y.value())


class CheckoutConfigDialog(QDialog):
    # ... (Code beibehalten) ...
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Kasse #{data['id']} Konfigurieren")
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.data = data
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cb_open = QCheckBox("Geöffnet")
        self.cb_open.setChecked(self.data.get("open", True))
        form.addRow(self.cb_open)

        # Max queue length
        self.spin_max_queue = QSpinBox()
        self.spin_max_queue.setRange(1, 20)
        self.spin_max_queue.setValue(self.data.get("max_queue", 5))
        self.spin_max_queue.setSuffix(" Kunden")
        form.addRow("Max. Warteschlange:", self.spin_max_queue)

        # Only show cashier skill for normal checkouts, not for SB (self-checkout)
        checkout_type = self.data.get("type", "Normal")
        if checkout_type != "SB":
            self.combo_skill = QComboBox()
            self.combo_skill.addItems(["Azubi", "Festangestellter"])
            skill = self.data.get("skill", "Azubi")
            self.combo_skill.setCurrentText(skill)
            form.addRow("Personal:", self.combo_skill)
        else:
            self.combo_skill = None  # No skill selection for SB checkouts

        layout.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        result = {
            "open": self.cb_open.isChecked(),
            "max_queue": self.spin_max_queue.value(),
        }
        # Only include skill if it exists (i.e., not SB checkout)
        if self.combo_skill is not None:
            result["skill"] = self.combo_skill.currentText()
        return result

    def set_blocked(self, blocked):
        """Enable/disable all checkout controls."""
        self.cb_open.setEnabled(not blocked)
        self.spin_max_queue.setEnabled(not blocked)
        if self.combo_skill is not None:
            self.combo_skill.setEnabled(not blocked)


class VisibilityDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sichtbarkeit & Ebenen")
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.settings = current_settings.copy()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        gb = QGroupBox("Elemente anzeigen")
        form = QFormLayout(gb)

        self.cb_routes = self._add_cb("Routen", "show_routes", form)
        self.cb_shelves = self._add_cb("Regale", "show_shelves", form)
        self.cb_s_nums = self._add_cb(
            "Regal Nummern", "show_shelf_numbers", form
        )
        self.cb_checkouts = self._add_cb("Kassen", "show_checkouts", form)
        self.cb_c_nums = self._add_cb(
            "Kassen Nummern", "show_checkout_numbers", form
        )
        self.cb_cashiers = self._add_cb("Kassierer", "show_cashiers", form)
        self.cb_queues = self._add_cb(
            "Warteschlangen (Punkte)", "show_queues", form
        )

        # Areas
        self.cb_start = self._add_cb("Start-Bereich", "show_start_area", form)
        self.cb_wait = self._add_cb("Warte-Bereich", "show_waiting_area", form)
        self.cb_exit = self._add_cb("Ausgangs-Bereich", "show_exit_area", form)

        layout.addWidget(gb)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)

    def _add_cb(self, label, key, layout):
        cb = QCheckBox()
        cb.setChecked(self.settings.get(key, True))
        cb.toggled.connect(lambda v: self._on_change(key, v))
        layout.addRow(label, cb)
        return cb

    def _on_change(self, key, val):
        self.settings[key] = val
        self.settings_changed.emit(self.settings)


class OffsetDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Offsets Konfigurieren")
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.settings = current_settings.copy()
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Tabs für verschiedene Offsets
        tabs = QTabWidget()

        # 1. Queues
        tab_q = QWidget()
        l_q = QFormLayout(tab_q)
        self._add_offset_control("Queue Normal (L)", "offset_queue_left", l_q)
        self._add_offset_control("Queue Normal (R)", "offset_queue_right", l_q)
        self._add_offset_control("Queue SB (L)", "offset_queue_sb_left", l_q)
        self._add_offset_control("Queue SB (R)", "offset_queue_sb_right", l_q)
        tabs.addTab(tab_q, "Warteschlangen")

        # 2. Cashiers
        tab_c = QWidget()
        l_c = QFormLayout(tab_c)
        self._add_offset_control("Kassierer (L)", "offset_cashier_left", l_c)
        self._add_offset_control("Kassierer (R)", "offset_cashier_right", l_c)
        tabs.addTab(tab_c, "Kassierer")

        # 3. Screens
        tab_s = QWidget()
        l_s = QFormLayout(tab_s)
        self._add_offset_control(
            "Screen Normal (L)", "offset_screen_normal_left", l_s
        )
        self._add_offset_control(
            "Screen Normal (R)", "offset_screen_normal_right", l_s
        )
        self._add_offset_control("Screen SB (L)", "offset_screen_sb_left", l_s)
        self._add_offset_control(
            "Screen SB (R)", "offset_screen_sb_right", l_s
        )
        tabs.addTab(tab_s, "Bildschirme")

        layout.addWidget(tabs)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)

    def _add_offset_control(self, label, key, layout):
        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)

        val = self.settings.get(key, [0, 0])

        sb_x = QDoubleSpinBox()
        sb_x.setRange(-200, 200)
        sb_x.setValue(val[0])
        sb_x.setPrefix("X: ")

        sb_y = QDoubleSpinBox()
        sb_y.setRange(-200, 200)
        sb_y.setValue(val[1])
        sb_y.setPrefix("Y: ")

        def update():
            self.settings[key] = [sb_x.value(), sb_y.value()]
            self.settings_changed.emit(self.settings)

        sb_x.valueChanged.connect(update)
        sb_y.valueChanged.connect(update)

        h.addWidget(sb_x)
        h.addWidget(sb_y)
        layout.addRow(label, container)
