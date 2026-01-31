"""
Stats Details Tab Component.
Displays detailed statistics organized by theme.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
)
from PyQt6.QtCore import Qt


class StatsDetailsTab(QWidget):
    """Detailed statistics view with themed sections."""

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

        # KUNDEN-BEREICH
        self._create_items_card(layout, card_style)
        self._create_customers_served_card(layout, card_style)

        # KASSEN-BEREICH
        self._create_payment_card(layout, card_style)
        self._create_issues_card(layout, card_style)

        # ALLGEMEIN
        self._create_time_card(layout, card_style)

        layout.addStretch()

    def _create_items_card(self, layout, card_style):
        """Create items statistics card."""
        card = QGroupBox(
            self.translator.get("sidebar.stats.card_item_stats", "ARTIKEL-STATISTIKEN")
            if self.translator
            else "ARTIKEL-STATISTIKEN"
        )
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        items_grid = QFormLayout()
        items_grid.setSpacing(8)

        # Total items
        total_items_lbl = QLabel(
            self.translator.get("sidebar.stats.total_items")
            if self.translator
            else "Artikel Gesamt:"
        )
        total_items_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_total_items = QLabel("0")
        self.lbl_total_items.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        items_grid.addRow(total_items_lbl, self.lbl_total_items)

        # Avg items per customer
        avg_items_lbl = QLabel(
            self.translator.get("sidebar.stats.avg_items_per_customer")
            if self.translator
            else "Ø Artikel/Kunde:"
        )
        avg_items_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_avg_items_per_customer = QLabel("0.0")
        self.lbl_avg_items_per_customer.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        items_grid.addRow(avg_items_lbl, self.lbl_avg_items_per_customer)

        card_layout.addLayout(items_grid)
        layout.addWidget(card)

    def _create_customers_served_card(self, layout, card_style):
        """Create customers served today card."""
        card = QGroupBox(
            self.translator.get("sidebar.stats.card_served_today", "HEUTE BEDIENT")
            if self.translator
            else "HEUTE BEDIENT"
        )
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        self.lbl_total_customers = QLabel("0")
        self.lbl_total_customers.setStyleSheet("font-size: 36px; color: #111827; font-weight: 700; text-align: center;")
        self.lbl_total_customers.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_total_customers)

        customers_label = QLabel(
            self.translator.get("sidebar.stats.unit_customers", "Kunden")
            if self.translator
            else "Kunden"
        )
        customers_label.setStyleSheet("font-size: 13px; color: #6B7280; text-align: center;")
        customers_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(customers_label)

        layout.addWidget(card)

    def _create_payment_card(self, layout, card_style):
        """Create payment methods card."""
        card = QGroupBox(
            self.translator.get("sidebar.stats.card_payment_methods", "ZAHLUNGSMETHODEN")
            if self.translator
            else "ZAHLUNGSMETHODEN"
        )
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        payment_grid = QFormLayout()
        payment_grid.setSpacing(8)

        # Cash
        cash_lbl = QLabel(
            self.translator.get("sidebar.stats.cash_percent")
            if self.translator
            else "Bar:"
        )
        cash_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_payment_cash = QLabel("0%")
        self.lbl_payment_cash.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        payment_grid.addRow(cash_lbl, self.lbl_payment_cash)

        # Card
        card_lbl = QLabel(
            self.translator.get("sidebar.stats.card_percent")
            if self.translator
            else "Karte:"
        )
        card_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_payment_card = QLabel("0%")
        self.lbl_payment_card.setStyleSheet("font-size: 18px; color: #374151; font-weight: 700;")
        payment_grid.addRow(card_lbl, self.lbl_payment_card)

        card_layout.addLayout(payment_grid)
        layout.addWidget(card)

    def _create_issues_card(self, layout, card_style):
        """Create checkout issues card."""
        card = QGroupBox(
            self.translator.get("sidebar.stats.card_checkout_issues", "KASSEN-PROBLEME")
            if self.translator
            else "KASSEN-PROBLEME"
        )
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        issues_grid = QFormLayout()
        issues_grid.setSpacing(8)

        # Malfunctions
        malfunctions_lbl = QLabel(
            self.translator.get("sidebar.stats.malfunctions_today")
            if self.translator
            else "Störungen:"
        )
        malfunctions_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_malfunctions = QLabel("0")
        self.lbl_malfunctions.setStyleSheet("font-size: 18px; color: #EF4444; font-weight: 700;")
        issues_grid.addRow(malfunctions_lbl, self.lbl_malfunctions)

        # Annoyance
        annoyance_lbl = QLabel(
            self.translator.get("sidebar.stats.label_annoyance", "Verärgerungen:")
            if self.translator
            else "Verärgerungen:"
        )
        annoyance_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_annoyance = QLabel("0")
        self.lbl_annoyance.setStyleSheet("font-size: 18px; color: #F59E0B; font-weight: 700;")
        issues_grid.addRow(annoyance_lbl, self.lbl_annoyance)

        # Conflicts
        conflicts_lbl = QLabel(
            self.translator.get("sidebar.stats.conflicts_today")
            if self.translator
            else "Konflikte:"
        )
        conflicts_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_conflicts = QLabel("0")
        self.lbl_conflicts.setStyleSheet("font-size: 18px; color: #DC2626; font-weight: 700;")
        issues_grid.addRow(conflicts_lbl, self.lbl_conflicts)

        card_layout.addLayout(issues_grid)
        layout.addWidget(card)

    def _create_time_card(self, layout, card_style):
        """Create opening hours card."""
        card = QGroupBox(
            self.translator.get("sidebar.stats.card_opening_hours", "ÖFFNUNGSZEITEN")
            if self.translator
            else "ÖFFNUNGSZEITEN"
        )
        card.setStyleSheet(card_style)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        time_grid = QFormLayout()
        time_grid.setSpacing(8)

        # Elapsed
        elapsed_lbl = QLabel(
            self.translator.get("sidebar.stats.label_elapsed", "Verstrichen:")
            if self.translator
            else "Verstrichen:"
        )
        elapsed_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_elapsed_open = QLabel("0:00")
        self.lbl_elapsed_open.setStyleSheet("font-size: 16px; color: #374151; font-weight: 600;")
        time_grid.addRow(elapsed_lbl, self.lbl_elapsed_open)

        # Scheduled
        scheduled_lbl = QLabel(
            self.translator.get("sidebar.stats.label_scheduled", "Geplant:")
            if self.translator
            else "Geplant:"
        )
        scheduled_lbl.setStyleSheet("font-size: 13px; color: #6B7280; font-weight: 600;")
        self.lbl_scheduled_open = QLabel("0:00")
        self.lbl_scheduled_open.setStyleSheet("font-size: 16px; color: #374151; font-weight: 600;")
        time_grid.addRow(scheduled_lbl, self.lbl_scheduled_open)

        # Overtime
        overtime_lbl = QLabel(
            self.translator.get("sidebar.stats.label_overtime", "Überzeit:")
            if self.translator
            else "Überzeit:"
        )
        overtime_lbl.setStyleSheet("font-size: 13px; color: #F59E0B; font-weight: 600;")
        self.lbl_overtime = QLabel("+0:00")
        self.lbl_overtime.setStyleSheet("font-size: 16px; color: #F59E0B; font-weight: 700;")
        time_grid.addRow(overtime_lbl, self.lbl_overtime)

        card_layout.addLayout(time_grid)
        layout.addWidget(card)
