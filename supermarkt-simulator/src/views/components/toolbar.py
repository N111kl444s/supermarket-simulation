"""
Toolbar Component.
Refactored:
- FIX: Widened buttons to ensure content fits fully.
- HEIGHT: Buttons increased to 44px to match Sidebar header style.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QButtonGroup,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from config import COLOR_ACCENT, COLOR_BORDER


class ProgressClock(QLabel):
    def __init__(self, parent=None):
        super().__init__("08:00", parent)
        self.progress = 0.0
        self.is_overtime = False
        self.blink_state = False
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(140, 44)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.blink_timer = None

    def set_progress(self, val):
        self.progress = max(0.0, min(1.0, val))
        self.repaint()

    def set_overtime(self, active):
        if self.is_overtime == active:
            return
        self.is_overtime = active
        if active:
            if not self.blink_timer:
                from PyQt6.QtCore import QTimer

                self.blink_timer = QTimer(self)
                self.blink_timer.setInterval(500)
                self.blink_timer.timeout.connect(self._toggle_blink)
            self.blink_timer.start()
        else:
            if self.blink_timer:
                self.blink_timer.stop()
            self.blink_state = False
        self.repaint()

    def _toggle_blink(self):
        self.blink_state = not self.blink_state
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#F3F4F6")))
        painter.drawRoundedRect(rect, 10, 10)

        if not self.is_overtime:
            fill_width = int(rect.width() * self.progress)
            if fill_width > 0:
                painter.save()
                painter.setClipRect(0, 0, fill_width, rect.height())
                painter.setBrush(QBrush(QColor("#DBEAFE")))
                painter.drawRoundedRect(rect, 10, 10)
                painter.restore()
        else:
            if self.blink_state:
                painter.setBrush(QBrush(QColor("#FECACA")))
                painter.drawRoundedRect(rect, 10, 10)

        painter.setBrush(Qt.BrushStyle.NoBrush)
        border_col = (
            QColor(COLOR_ACCENT) if not self.is_overtime else QColor("#EF4444")
        )
        painter.setPen(QPen(border_col, 2))
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 10, 10)
        super().paintEvent(event)


class TopToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setup_ui()
        self.apply_styles()

    def apply_styles(self):
        accent = COLOR_ACCENT.name()
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: #FFFFFF;
                border-bottom: 1px solid #E5E7EB;
            }}
            QPushButton {{
                background-color: #FFFFFF;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                font-weight: 700;
                font-size: 16px; 
                color: #4B5563;
            }}
            QPushButton:hover {{
                background-color: #EFF6FF;
                border-color: {accent};
                color: {accent};
            }}
            QPushButton:checked {{
                background-color: {accent};
                color: white;
                border: 1px solid {accent};
            }}
            ProgressClock {{
                font-size: 24px; 
                font-family: 'Segoe UI', sans-serif; 
                font-weight: 800;
                color: {accent};
            }}
        """
        )

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(0)

        # LEFT SPACER
        layout.addStretch(1)

        # === CENTER BLOCK ===
        center_layout = QHBoxLayout()
        center_layout.setSpacing(20)

        # 1. Sim Controls
        self.btn_reset = QPushButton("↺")
        self.btn_reset.setToolTip("Reset")
        self.btn_reset.setFixedSize(60, 44)

        self.btn_play_pause = QPushButton("▶")
        self.btn_play_pause.setCheckable(True)
        self.btn_play_pause.setToolTip("Start / Pause")
        self.btn_play_pause.setFixedSize(70, 44)

        self.btn_skip = QPushButton("⏭")
        self.btn_skip.setToolTip("Tag überspringen")
        self.btn_skip.setFixedSize(60, 44)

        center_layout.addWidget(self.btn_reset)
        center_layout.addWidget(self.btn_play_pause)
        center_layout.addWidget(self.btn_skip)

        # 2. Clock
        self.clock_widget = ProgressClock()
        center_layout.addWidget(self.clock_widget)

        # 3. Speed Controls
        self.speed_group = QButtonGroup(self)

        self.btn_speed_1 = QPushButton("1x")
        self.btn_speed_1.setCheckable(True)
        self.btn_speed_1.setChecked(True)
        self.btn_speed_1.setFixedSize(60, 44)

        self.btn_speed_2 = QPushButton("4x")
        self.btn_speed_2.setCheckable(True)
        self.btn_speed_2.setFixedSize(60, 44)

        self.btn_speed_3 = QPushButton("16x")
        self.btn_speed_3.setCheckable(True)
        self.btn_speed_3.setFixedSize(60, 44)

        self.speed_group.addButton(self.btn_speed_1)
        self.speed_group.addButton(self.btn_speed_2)
        self.speed_group.addButton(self.btn_speed_3)

        center_layout.addWidget(self.btn_speed_1)
        center_layout.addWidget(self.btn_speed_2)
        center_layout.addWidget(self.btn_speed_3)

        layout.addLayout(center_layout)

        # RIGHT SPACER
        layout.addStretch(1)

        # === FAR RIGHT: ZOOM ===
        self.btn_reset_zoom = QPushButton("Ansicht ausrichten")
        layout.addWidget(self.btn_reset_zoom)
