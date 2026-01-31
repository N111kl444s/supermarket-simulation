"""
Stats Log Tab Component.
Displays event protocol in a list widget.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QGroupBox,
)


class StatsLogTab(QWidget):
    """Event log tab for statistics."""

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.plot_widget = None  # For future chart integration
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        event_log_title = (
            self.translator.get("sidebar.stats.event_log")
            if self.translator
            else "Ereignis-Protokoll"
        )

        # Event log group box
        gb_log = QGroupBox(event_log_title)
        gb_log.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: 700;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
        """)

        log_layout = QVBoxLayout(gb_log)

        # List widget for events
        self.list_log = QListWidget()
        self.list_log.setStyleSheet("""
            QListWidget {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                font-size: 10px;
                padding: 4px;
            }
        """)
        # Enable infinite scroll by not limiting the number of items
        # QListWidget doesn't have a default item limit, so it's already infinite
        log_layout.addWidget(self.list_log)

        layout.addWidget(gb_log)

    def clear_log(self):
        """Clear all entries from the event log."""
        self.list_log.clear()
