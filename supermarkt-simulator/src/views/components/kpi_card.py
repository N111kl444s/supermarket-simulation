"""
KPI Card Component for Statistics Dashboard.
Provides a modern, card-based display for key performance indicators.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class KPICard(QFrame):
    """
    Modern KPI card with icon, title, value, and status indicator.
    
    Args:
        icon: Emoji or icon character
        title: Card title/label
        value: Current value to display
        unit: Unit of measurement (e.g., "min", "%", "/h")
        status: "good", "warning", "critical", or "neutral"
        show_progress: Whether to show a progress bar
        progress_max: Maximum value for progress bar
        parent: Parent widget
    """
    
    # Color schemes
    COLORS = {
        "good": {
            "border": "#10B981",
            "bg": "#D1FAE5",
            "text": "#065F46",
        },
        "warning": {
            "border": "#F59E0B",
            "bg": "#FEF3C7",
            "text": "#92400E",
        },
        "critical": {
            "border": "#EF4444",
            "bg": "#FEE2E2",
            "text": "#991B1B",
        },
        "neutral": {
            "border": "#3B82F6",
            "bg": "#DBEAFE",
            "text": "#1E40AF",
        },
    }
    
    STATUS_ICONS = {
        "good": "✅",
        "warning": "⚠️",
        "critical": "🔴",
        "neutral": "ℹ️",
    }
    
    def __init__(
        self,
        icon="📊",
        title="Metric",
        value="0",
        unit="",
        status="neutral",
        show_progress=False,
        progress_max=100,
        parent=None,
    ):
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.value = value
        self.unit = unit
        self.status = status
        self.show_progress = show_progress
        self.progress_max = progress_max
        
        self._init_ui()
        self.update_status(status)
    
    def _init_ui(self):
        """Initialize the UI components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header: Title only (no icon)
        self.title_label = QLabel(self.title)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 14px; "
            "font-weight: 700; "
            "color: #1E293B; "
            "text-transform: uppercase; "
            "letter-spacing: 0.5px;"
        )
        layout.addWidget(self.title_label)
        
        # Value (large and prominent)
        self.value_label = QLabel(f"{self.value} {self.unit}")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_font = QFont()
        value_font.setPointSize(32)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)
        self.value_label.setStyleSheet("color: #111827; padding: 8px 0;")
        layout.addWidget(self.value_label)
        
        # Progress bar (optional)
        if self.show_progress:
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, self.progress_max)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setMaximumHeight(8)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    background-color: #E5E7EB;
                }
                QProgressBar::chunk {
                    border-radius: 4px;
                }
            """)
            layout.addWidget(self.progress_bar)
        else:
            self.progress_bar = None
        
        # Status text
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(
            "font-size: 11px; "
            "font-weight: 600; "
            "padding: 4px;"
        )
        layout.addWidget(self.status_label)
    
    def update_value(self, value, unit=None, status=None, progress_value=None):
        """Update the displayed value."""
        self.value = value
        if unit is not None:
            self.unit = unit
        self.value_label.setText(f"{self.value} {self.unit}")
        
        # Update progress bar if present
        if self.progress_bar:
            if progress_value is not None:
                self.progress_bar.setValue(int(progress_value))
            elif isinstance(value, (int, float)):
                self.progress_bar.setValue(int(value))
        
        # Update status if provided
        if status is not None:
            self.update_status(status)
    
    def set_subtitle(self, text):
        """Set the subtitle/status text."""
        self.status_label.setText(text)
    
    def update_status(self, status, status_text=None):
        """Update the status color scheme and text."""
        self.status = status
        colors = self.COLORS.get(status, self.COLORS["neutral"])
        
        # Update card style
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['bg']};
                border: 2px solid {colors['border']};
                border-radius: 10px;
            }}
        """)
        
        # Update status label
        icon = self.STATUS_ICONS.get(status, "")
        if status_text is None:
            status_text = status.upper()
        self.status_label.setText(f"{icon} {status_text}")
        self.status_label.setStyleSheet(f"""
            font-size: 11px;
            font-weight: 600;
            color: {colors['text']};
            padding: 4px;
        """)
        
        # Update progress bar color if present
        if self.progress_bar:
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 4px;
                    background-color: #E5E7EB;
                }}
                QProgressBar::chunk {{
                    background-color: {colors['border']};
                    border-radius: 4px;
                }}
            """)


class LiveIndicator(QWidget):
    """Blinking LIVE indicator for real-time data."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_visible = True
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.dot_label = QLabel("●")
        self.dot_label.setStyleSheet("color: #EF4444; font-size: 14px;")
        layout.addWidget(self.dot_label)
        
        self.text_label = QLabel("LIVE")
        self.text_label.setStyleSheet(
            "color: #EF4444; "
            "font-size: 10px; "
            "font-weight: 700; "
            "letter-spacing: 1px;"
        )
        layout.addWidget(self.text_label)
        
        # Start blinking timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._toggle_visibility)
        self.timer.start(800)  # Blink every 800ms
    
    def _toggle_visibility(self):
        """Toggle visibility for blinking effect."""
        self.is_visible = not self.is_visible
        opacity = "1.0" if self.is_visible else "0.3"
        self.dot_label.setStyleSheet(f"color: #EF4444; font-size: 14px; opacity: {opacity};")
    
    def stop(self):
        """Stop the blinking animation."""
        if self.timer:
            self.timer.stop()


class MetricBox(QFrame):
    """
    Compact box for displaying Min/Avg/Max metrics.
    
    Args:
        label: Metric label
        min_val: Minimum value
        avg_val: Average value
        max_val: Maximum value
        unit: Unit of measurement
        parent: Parent widget
    """
    
    def __init__(self, label, min_val=0, avg_val=0, max_val=0, unit="", parent=None):
        super().__init__(parent)
        self.label = label
        self.min_val = min_val
        self.avg_val = avg_val
        self.max_val = max_val
        self.unit = unit
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI components."""
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Label
        label_widget = QLabel(self.label)
        label_widget.setStyleSheet(
            "font-size: 12px; "
            "font-weight: 600; "
            "color: #374151; "
            "border: none; "
            "background: transparent;"
        )
        layout.addWidget(label_widget)
        
        # Min/Avg/Max row
        values_layout = QHBoxLayout()
        values_layout.setSpacing(4)
        
        for title, value in [("Min", self.min_val), ("Ø", self.avg_val), ("Max", self.max_val)]:
            col_layout = QVBoxLayout()
            col_layout.setSpacing(2)
            
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet(
                "font-size: 9px; "
                "color: #6B7280; "
                "font-weight: 600; "
                "border: none; "
                "background: transparent;"
            )
            col_layout.addWidget(title_label)
            
            value_label = QLabel(f"{value:.1f}{self.unit}")
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value_label.setStyleSheet(
                "font-size: 14px; "
                "color: #111827; "
                "font-weight: 700; "
                "border: none; "
                "background: transparent;"
            )
            col_layout.addWidget(value_label)
            
            values_layout.addLayout(col_layout)
        
        layout.addLayout(values_layout)
    
    def update_values(self, min_val, avg_val, max_val):
        """Update the displayed values."""
        self.min_val = min_val
        self.avg_val = avg_val
        self.max_val = max_val
        # Re-initialize to update display
        # Clear and rebuild
        for i in reversed(range(self.layout().count())): 
            self.layout().itemAt(i).widget().setParent(None)
        self._init_ui()
