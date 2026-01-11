"""
Top Toolbar Component.
Contains Mode selection, Map selection, Playback controls, and Speed controls.
Updated: Layout fixes for Reset Zoom button.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QComboBox, QPushButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from config import COLOR_ERROR, COLOR_SUCCESS

class TopToolbar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToolbarFrame")
        self.setFixedHeight(80)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Modus
        layout.addWidget(QLabel("Modus:"))
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(140)
        self.mode_combo.addItems(["Simulation", "Editor"])
        layout.addWidget(self.mode_combo)

        # Map
        layout.addWidget(QLabel("Map:"))
        self.map_combo = QComboBox()
        self.map_combo.setFixedWidth(200)
        layout.addWidget(self.map_combo)

        self._add_separator(layout)
        layout.addStretch()

        # Uhr
        self.lbl_clock = QLabel("08:00")
        self.lbl_clock.setObjectName("ClockLabel")
        self.lbl_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_clock)
        layout.addSpacing(20)

        # Playback
        self.btn_reset = QPushButton("↺")
        self.btn_reset.setObjectName("ToolbarButton")
        self.btn_reset.setFixedWidth(60)
        self.btn_reset.setStyleSheet(f"color: {COLOR_ERROR.name()}; font-size: 24px;")

        self.btn_play_pause = QPushButton("▶")
        self.btn_play_pause.setObjectName("ToolbarButton")
        self.btn_play_pause.setCheckable(True)
        self.btn_play_pause.setFixedWidth(80)
        self.btn_play_pause.setStyleSheet(f"color: {COLOR_SUCCESS.name()}; font-size: 24px;")

        self.btn_skip = QPushButton("⏭")
        self.btn_skip.setObjectName("ToolbarButton")
        self.btn_skip.setFixedWidth(60)
        self.btn_skip.setStyleSheet("font-size: 16px;")

        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_play_pause)
        layout.addWidget(self.btn_skip)

        layout.addSpacing(15)

        # Speed
        self.speed_group = QButtonGroup(self)
        self.speed_group.setExclusive(True)
        
        self.btn_speed_1 = self._create_speed_btn("1x", True)
        self.btn_speed_2 = self._create_speed_btn("2x")
        self.btn_speed_3 = self._create_speed_btn("6x")
        
        layout.addWidget(self.btn_speed_1)
        layout.addWidget(self.btn_speed_2)
        layout.addWidget(self.btn_speed_3)
        layout.addStretch()

        self._add_separator(layout)
        
        # FIX: Button breiter gemacht
        self.btn_reset_zoom = QPushButton("Ansicht Reset")
        self.btn_reset_zoom.setFixedWidth(160) 
        layout.addWidget(self.btn_reset_zoom)

    def _create_speed_btn(self, text, checked=False):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setFixedWidth(60)
        self.speed_group.addButton(btn)
        return btn

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)