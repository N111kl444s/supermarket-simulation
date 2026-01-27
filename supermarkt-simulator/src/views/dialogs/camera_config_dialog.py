"""
Camera Positions Configuration Dialog.
"""

import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QFormLayout,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt
from config import COLOR_ACCENT


CAMERA_POSITIONS_FILE = (
    Path(__file__).parent.parent.parent / "camera_positions.json"
)


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
            with open(self.camera_positions_file, "r") as f:
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
        if not hasattr(self, "position_widgets"):
            self.position_widgets = {}

        self.position_widgets[map_name] = {}

        # Create form for each camera position
        positions = self.positions_data.get(map_name, {})
        for position_name, position_data in positions.items():
            gb = self.create_position_group(
                map_name,
                position_name,
                position_data,
                self.position_widgets[map_name],
            )
            scroll_layout.addWidget(gb)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        tab_layout.addWidget(scroll)

        self.tabs.addTab(tab_widget, map_name)

    def create_position_group(
        self, map_name, position_name, position_data, widget_dict
    ):
        """Create a form group for a single camera position."""
        from PyQt6.QtWidgets import QGroupBox

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
            "zoom": spin_zoom,
        }

        return gb

    def add_new_map(self):
        """Add a new map configuration."""
        from PyQt6.QtWidgets import QInputDialog

        map_name, ok = QInputDialog.getText(
            self, "Neue Map", "Map Name eingeben:"
        )

        if ok and map_name:
            if map_name in self.positions_data:
                QMessageBox.warning(
                    self, "Fehler", f"Map '{map_name}' existiert bereits!"
                )
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
            with open(self.camera_positions_file, "w") as f:
                json.dump(self.positions_data, f, indent=2)

            QMessageBox.information(
                self, "Erfolg", "Kamera-Positionen gespeichert!"
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Fehler", f"Fehler beim Speichern: {str(e)}"
            )

    def apply_styles(self):
        """Apply application styles."""
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
