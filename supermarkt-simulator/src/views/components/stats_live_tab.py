"""
Stats Live Tab Component.
Displays real-time statistics in a card-based layout.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QGridLayout,
    QProgressBar,
)
from PyQt6.QtCore import Qt
from .kpi_card import LiveIndicator


class StatsLiveTab(QWidget):
    """Live statistics overview with KPI cards."""

    def __init__(self, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        card_style = """
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
        """

        # Card 1: KUNDEN
        self._create_customers_card(layout, card_style)

        # Card 2: Zufriedenheit
        self._create_satisfaction_card(layout, card_style)

        # Card 3: Kassen-Status
        self._create_checkouts_card(layout, card_style)

        # Card 4: Zufriedenheitsscore
        self._create_score_card(layout, card_style)

        # Report Button
        self._create_report_button(layout)

        layout.addStretch()

    def _create_customers_card(self, layout, card_style):
        """Create customers KPI card."""
        self.gb_stats = QGroupBox("KUNDEN")  # Keep as instance variable for compatibility
        self.gb_stats.setStyleSheet(card_style)
        card_layout = QVBoxLayout(self.gb_stats)
        card_layout.setSpacing(10)

        # Im Laden
        store_row = self._create_metric_row(
            "Im Laden:",
            "lbl_customers_in_store",
            "0",
            "20px",
            "Kunden"
        )
        card_layout.addLayout(store_row)

        # Gesamt bedient
        total_row = self._create_metric_row(
            "Gesamt bedient:",
            "lbl_total_customers_served_live",
            "0",
            "20px",
            "Kunden"
        )
        card_layout.addLayout(total_row)

        # Durchsatz
        throughput_row = QHBoxLayout()
        throughput_row.setSpacing(6)

        throughput_lbl = QLabel("Durchsatz:")
        throughput_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        throughput_row.addWidget(throughput_lbl)

        self.lbl_throughput = QLabel("0 K/h")
        self.lbl_throughput.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 700;")
        throughput_row.addWidget(self.lbl_throughput)
        throughput_row.addStretch()
        card_layout.addLayout(throughput_row)

        layout.addWidget(self.gb_stats)

    def _create_satisfaction_card(self, layout, card_style):
        """Create customer satisfaction card."""
        card = QGroupBox("KUNDENZUFRIEDENHEIT")
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        # Wartezeit
        wait_row = QHBoxLayout()
        wait_row.setSpacing(6)

        wait_lbl = QLabel("Ø Wartezeit:")
        wait_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        wait_row.addWidget(wait_lbl)

        self.lbl_avg_wait = QLabel("0.0 min")
        self.lbl_avg_wait.setStyleSheet("font-size: 22px; color: #111827; font-weight: 700;")
        wait_row.addWidget(self.lbl_avg_wait)

        self.lbl_wait_status = QLabel("")
        self.lbl_wait_status.setStyleSheet("font-size: 22px;")
        wait_row.addWidget(self.lbl_wait_status)
        wait_row.addStretch()
        card_layout.addLayout(wait_row)

        # Progress bar
        self.wait_progress = QProgressBar()
        self.wait_progress.setRange(0, 10)
        self.wait_progress.setValue(0)
        self.wait_progress.setTextVisible(False)
        self.wait_progress.setMaximumHeight(10)
        self.wait_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background-color: #E5E7EB;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 3px;
            }
        """)
        card_layout.addWidget(self.wait_progress)

        # Warteschlange
        queue_row = self._create_metric_row(
            "In Warteschlange:",
            "lbl_queue_count",
            "0",
            "18px",
            "Kunden"
        )
        card_layout.addLayout(queue_row)

        # Längste Queue
        longest_row = QHBoxLayout()
        longest_row.setSpacing(6)

        longest_lbl = QLabel("Längste Queue:")
        longest_lbl.setStyleSheet("font-size: 12px; color: #9CA3AF; font-weight: 600;")
        longest_row.addWidget(longest_lbl)

        self.lbl_longest_queue = QLabel("Kasse #0 (0)")
        self.lbl_longest_queue.setStyleSheet("font-size: 12px; color: #6B7280; font-weight: 600;")
        longest_row.addWidget(self.lbl_longest_queue)
        longest_row.addStretch()
        card_layout.addLayout(longest_row)

        layout.addWidget(card)

    def _create_checkouts_card(self, layout, card_style):
        """Create checkouts status card."""
        card = QGroupBox("KASSEN-STATUS")
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        checkouts_grid = QGridLayout()
        checkouts_grid.setSpacing(8)

        # Offen
        open_lbl = QLabel("Offen:")
        open_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(open_lbl, 0, 0)

        self.lbl_checkouts_open = QLabel("0")
        self.lbl_checkouts_open.setStyleSheet("font-size: 18px; color: #10B981; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_open, 0, 1)

        open_unit = QLabel("Kassen")
        open_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(open_unit, 0, 2)

        # Störung
        malfunction_lbl = QLabel("Störung:")
        malfunction_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(malfunction_lbl, 1, 0)

        self.lbl_checkouts_malfunction = QLabel("0")
        self.lbl_checkouts_malfunction.setStyleSheet("font-size: 18px; color: #EF4444; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_malfunction, 1, 1)

        malfunction_unit = QLabel("Kassen")
        malfunction_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(malfunction_unit, 1, 2)

        # Geschlossen
        closed_lbl = QLabel("Geschlossen:")
        closed_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        checkouts_grid.addWidget(closed_lbl, 2, 0)

        self.lbl_checkouts_closed = QLabel("0")
        self.lbl_checkouts_closed.setStyleSheet("font-size: 18px; color: #9CA3AF; font-weight: 700;")
        checkouts_grid.addWidget(self.lbl_checkouts_closed, 2, 1)

        closed_unit = QLabel("Kassen")
        closed_unit.setStyleSheet("font-size: 13px; color: #6B7280;")
        checkouts_grid.addWidget(closed_unit, 2, 2)

        card_layout.addLayout(checkouts_grid)

        # Compatibility label
        self.lbl_available_checkouts = QLabel("0/0")

        layout.addWidget(card)

    def _create_score_card(self, layout, card_style):
        """Create satisfaction score card."""
        card = QGroupBox("ZUFRIEDENHEITSSCORE")
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        # Score value
        satisfaction_value_layout = QHBoxLayout()

        self.lbl_satisfaction_score = QLabel("0%")
        self.lbl_satisfaction_score.setStyleSheet("font-size: 32px; color: #111827; font-weight: 700;")
        satisfaction_value_layout.addWidget(self.lbl_satisfaction_score)
        satisfaction_value_layout.addStretch()

        card_layout.addLayout(satisfaction_value_layout)

        # Progress bar
        self.satisfaction_progress = QProgressBar()
        self.satisfaction_progress.setRange(0, 100)
        self.satisfaction_progress.setValue(0)
        self.satisfaction_progress.setTextVisible(False)
        self.satisfaction_progress.setMaximumHeight(12)
        self.satisfaction_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #E5E7EB;
            }
            QProgressBar::chunk {
                background-color: #10B981;
                border-radius: 5px;
            }
        """)
        card_layout.addWidget(self.satisfaction_progress)

        # Status
        self.lbl_satisfaction_status = QLabel("Status: GUT")
        self.lbl_satisfaction_status.setStyleSheet("font-size: 13px; color: #10B981; font-weight: 700; text-align: center;")
        self.lbl_satisfaction_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_satisfaction_status)

        layout.addWidget(card)

    def _create_report_button(self, layout):
        """Create report button."""
        report_button_label = (
            self.translator.get("sidebar.stats.open_report")
            if self.translator
            else "📊 Bericht öffnen"
        )
        report_button_tooltip = (
            self.translator.get("sidebar.stats.open_report_tooltip")
            if self.translator
            else "Öffnet die ausführliche Statistikübersicht"
        )

        self.btn_open_report = QPushButton(report_button_label)
        self.btn_open_report.setToolTip(report_button_tooltip)
        self.btn_open_report.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:pressed {
                background-color: #1D4ED8;
            }
        """)
        layout.addWidget(self.btn_open_report)

    def _create_metric_row(self, label_text, attr_name, default_value, font_size, unit_text=None):
        """Helper to create a metric row with label, value, and optional unit."""
        row = QHBoxLayout()
        row.setSpacing(6)

        label = QLabel(label_text)
        label.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        row.addWidget(label)

        value_label = QLabel(default_value)
        value_label.setStyleSheet(f"font-size: {font_size}; color: #111827; font-weight: 700;")
        setattr(self, attr_name, value_label)
        row.addWidget(value_label)

        if unit_text:
            unit = QLabel(unit_text)
            unit.setStyleSheet("font-size: 13px; color: #6B7280;")
            row.addWidget(unit)

        row.addStretch()
        return row
