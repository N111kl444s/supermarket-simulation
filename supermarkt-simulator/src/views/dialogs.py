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
        self.data = data
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cb_open = QCheckBox("Geöffnet")
        self.cb_open.setChecked(self.data.get("open", True))
        form.addRow(self.cb_open)

        self.combo_skill = QComboBox()
        self.combo_skill.addItems(["Azubi", "Festangestellter"])
        skill = self.data.get("skill", "Azubi")
        self.combo_skill.setCurrentText(skill)
        form.addRow("Personal:", self.combo_skill)

        layout.addLayout(form)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return {
            "open": self.cb_open.isChecked(),
            "skill": self.combo_skill.currentText(),
        }


class VisibilityDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sichtbarkeit & Ebenen")
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


# ==============================================================================
# Camera Positions Configuration Dialog
# ==============================================================================

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QInputDialog,
    QMessageBox,
    QScrollArea,
)

CAMERA_POSITIONS_FILE = Path(__file__).parent.parent / "camera_positions.json"


class CameraPositionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kamera-Positionen konfigurieren")
        self.setGeometry(100, 100, 600, 500)
        
        self.camera_positions_file = CAMERA_POSITIONS_FILE
        self.positions_data = self.load_positions()
        
        self.setup_ui()
        self.apply_styles()

    def load_positions(self):
        """Load camera positions from JSON file."""
        if self.camera_positions_file.exists():
            with open(self.camera_positions_file, 'r') as f:
                return json.load(f)
        return {}

    def setup_ui(self):
        """Setup the dialog UI."""
        main_layout = QVBoxLayout(self)
        
        # Tab widget for different maps
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Create tabs for each map
        for map_name in self.positions_data.keys():
            self.create_map_tab(map_name)
        
        # Add new map button
        btn_layout = QHBoxLayout()
        btn_add_map = QPushButton("Neue Map hinzufügen")
        btn_add_map.clicked.connect(self.add_new_map)
        btn_layout.addWidget(btn_add_map)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        btn_save = QPushButton("Speichern")
        btn_cancel = QPushButton("Abbrechen")
        btn_save.clicked.connect(self.save_positions)
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_cancel)
        main_layout.addLayout(button_layout)

    def create_map_tab(self, map_name):
        """Create a tab for a specific map."""
        tab_widget = QWidget()
        tab_layout = QVBoxLayout(tab_widget)
        
        # Scroll area for better UX with many positions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Store spinboxes for later retrieval
        if not hasattr(self, 'position_widgets'):
            self.position_widgets = {}
        
        self.position_widgets[map_name] = {}
        
        # Create form for each camera position
        positions = self.positions_data.get(map_name, {})
        for position_name, position_data in positions.items():
            gb = self.create_position_group(
                map_name, 
                position_name, 
                position_data,
                self.position_widgets[map_name]
            )
            scroll_layout.addWidget(gb)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        tab_layout.addWidget(scroll)
        
        self.tabs.addTab(tab_widget, map_name)

    def create_position_group(self, map_name, position_name, position_data, widget_dict):
        """Create a form group for a single camera position."""
        gb = QGroupBox(position_name.replace("_", " ").title())
        layout = QFormLayout(gb)
        
        # X coordinate
        spin_x = QDoubleSpinBox()
        spin_x.setRange(-10000, 10000)
        spin_x.setValue(position_data.get("x", 0))
        spin_x.setSingleStep(10)
        layout.addRow("X Position:", spin_x)
        
        # Y coordinate
        spin_y = QDoubleSpinBox()
        spin_y.setRange(-10000, 10000)
        spin_y.setValue(position_data.get("y", 0))
        spin_y.setSingleStep(10)
        layout.addRow("Y Position:", spin_y)
        
        # Zoom level
        spin_zoom = QDoubleSpinBox()
        spin_zoom.setRange(0.1, 1000)
        spin_zoom.setValue(position_data.get("zoom", 1.0))
        spin_zoom.setSingleStep(0.1)
        layout.addRow("Zoom Level:", spin_zoom)
        
        # Store references
        widget_dict[position_name] = {
            "x": spin_x,
            "y": spin_y,
            "zoom": spin_zoom
        }
        
        return gb

    def add_new_map(self):
        """Add a new map configuration."""
        map_name, ok = QInputDialog.getText(
            self, 
            "Neue Map", 
            "Map Name eingeben:"
        )
        
        if ok and map_name:
            if map_name in self.positions_data:
                QMessageBox.warning(self, "Fehler", f"Map '{map_name}' existiert bereits!")
                return
            
            # Create default positions for new map
            self.positions_data[map_name] = {
                "full_store": {"x": 0, "y": 0, "zoom": 1.0},
                "entrance": {"x": 400, "y": 200, "zoom": 2.0},
                "sales_area": {"x": 800, "y": 400, "zoom": 2.5},
                "checkout_normal": {"x": 1200, "y": 600, "zoom": 3.0},
                "checkout_sb": {"x": 1200, "y": 800, "zoom": 3.0},
            }
            
            self.create_map_tab(map_name)

    def save_positions(self):
        """Save all positions to JSON file."""
        try:
            # Update positions_data from spinboxes
            for map_name, position_dict in self.position_widgets.items():
                if map_name not in self.positions_data:
                    continue
                
                for position_name, widgets in position_dict.items():
                    self.positions_data[map_name][position_name] = {
                        "x": widgets["x"].value(),
                        "y": widgets["y"].value(),
                        "zoom": widgets["zoom"].value(),
                    }
            
            # Write to file
            with open(self.camera_positions_file, 'w') as f:
                json.dump(self.positions_data, f, indent=2)
            
            QMessageBox.information(self, "Erfolg", "Kamera-Positionen gespeichert!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern: {str(e)}")

    def apply_styles(self):
        """Apply application styles."""
        from config import COLOR_ACCENT
        accent = COLOR_ACCENT.name()
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: #FFFFFF;
            }}
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
                color: #4B5563;
            }}
            QPushButton:hover {{
                background-color: #EFF6FF;
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:pressed {{
                background-color: {accent};
                color: white;
            }}
            QGroupBox {{
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: 600;
                color: #4B5563;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
            QDoubleSpinBox {{
                border: 1px solid #D1D5DB;
                border-radius: 4px;
                padding: 4px 8px;
                background-color: #FFFFFF;
            }}
            QDoubleSpinBox:focus {{
                border: 1px solid {accent};
                outline: none;
            }}
            """
        )
