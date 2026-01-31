"""Statistics dialogs module - Professional statistics reporting."""

from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QDialogButtonBox,
    QLabel,
    QGroupBox,
    QWidget,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QProgressBar,
    QHeaderView,
    QAbstractScrollArea,
    QSizePolicy,
    QLayout,
)
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont
from datetime import datetime
from config import COLOR_BG_MAIN
from views.statistics_tabs import (
    KPIDashboardTab,
    CustomerAnalysisTab,
    CheckoutPerformanceTab,
    OperationsTab,
)

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class StatisticsReportDialog(QDialog):
    def __init__(self, stats, parent=None, translator=None, sim_manager=None, settings=None):
        super().__init__(parent)
        self.translator = translator
        self.stats = stats or {}
        self.sim_manager = sim_manager
        self.settings = settings
        self._live_timer = None
        title = (
            self.translator.get("dialogs.stats_report_title")
            if self.translator
            else "Statistikbericht"
        )
        self.setWindowTitle(title)
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.setMinimumSize(1200, 920)
        self.setSizeGripEnabled(False)
        self._init_ui()
        if self.sim_manager is not None:
            self._start_live_updates()

    def _init_ui(self):
        """Initialize the modern 4-tab UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #F8FAFC;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #475569;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            QTabBar::tab:selected {
                background-color: #F8FAFC;
                color: #1E293B;
            }
            QTabBar::tab:hover {
                background-color: #CBD5E1;
            }
        """)
        
        # Initialize new professional tabs
        self.kpi_tab = KPIDashboardTab(translator=self.translator)
        self.customer_tab = CustomerAnalysisTab(translator=self.translator)
        self.checkout_tab = CheckoutPerformanceTab(translator=self.translator)
        self.operations_tab = OperationsTab(translator=self.translator)
        
        # Add tabs
        self.tabs.addTab(
            self.kpi_tab,
            self._t("dialogs.stats_tab_kpi", "KPI Dashboard")
        )
        self.tabs.addTab(
            self.customer_tab,
            self._t("dialogs.stats_tab_customers", "Kunden")
        )
        self.tabs.addTab(
            self.checkout_tab,
            self._t("dialogs.stats_tab_checkouts", "Kassen")
        )
        self.tabs.addTab(
            self.operations_tab,
            self._t("dialogs.stats_tab_operations", "Betrieb")
        )
        
        layout.addWidget(self.tabs)

        # Close button
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_label = self._t("dialogs.close", "Schließen")
        btns.button(QDialogButtonBox.StandardButton.Close).setText(close_label)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)
        
        # Populate tabs with initial statistics
        self._refresh_all_tabs()

    def closeEvent(self, event):
        if self._live_timer is not None:
            self._live_timer.stop()
        super().closeEvent(event)

    def _start_live_updates(self):
        if self._live_timer is None:
            self._live_timer = QTimer(self)
            self._live_timer.setInterval(1000)
            self._live_timer.timeout.connect(self._refresh_from_sim)
        self._live_timer.start()

    def _refresh_from_sim(self):
        """Refresh statistics from simulation manager."""
        if not self.sim_manager:
            return
        self.stats = self.sim_manager.get_statistics_snapshot()
        self._refresh_all_tabs()

    def _refresh_all_tabs(self):
        """Refresh all tab components with current statistics."""
        # KPI Dashboard Tab
        self.kpi_tab.update_kpis(self.stats, self.settings)
        self.kpi_tab.update_trend_chart(self.stats)
        self.kpi_tab.update_recommendations(self.stats, self.settings)
        
        # Customer Analysis Tab
        self.customer_tab.update_distributions(self.stats)
        self.customer_tab.update_time_metrics(self.stats)
        self.customer_tab.update_customer_list(self.stats)
        
        # Checkout Performance Tab
        self.checkout_tab.update_status(self.stats)
        self.checkout_tab.update_topflop(self.stats)
        self.checkout_tab.update_performance_table(self.stats)
        self.checkout_tab.update_skill_comparison(self.stats)
        
        # Operations Tab
        self.operations_tab.update_hours(self.stats)
        self.operations_tab.update_peak_chart(self.stats)

    # Legacy helper methods
    
    def _t(self, key, fallback):
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)

    def _info_label(self, text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lbl.setStyleSheet(
            "color: #8a8a8a; font-size: 10px; font-weight: 500; padding: 0px 0px;"
        )
        lbl.setMaximumHeight(lbl.sizeHint().height())
        return lbl


class CheckoutStatsDialog(QDialog):
    def __init__(self, checkout_id, sim_manager, parent=None, translator=None):
        super().__init__(parent)
        self.translator = translator
        self.checkout_id = checkout_id
        self.sim_manager = sim_manager
        title_tpl = (
            self.translator.get("dialogs.checkout_stats_title", "Kasse #{id} - Live Statistik")
            if self.translator
            else "Kasse #{id} - Live Statistik"
        )
        self.setWindowTitle(title_tpl.format(id=checkout_id))
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.setMinimumWidth(420)
        self._init_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self.refresh)
        self._timer.start()
        self.refresh()

    def closeEvent(self, event):
        if hasattr(self, "_timer"):
            self._timer.stop()
        super().closeEvent(event)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.lbl_status = QLabel("-")
        self.lbl_queue = QLabel("0")
        self.lbl_customers = QLabel("0")
        self.lbl_scan_avg = QLabel("0.0 min")
        self.lbl_pay_avg = QLabel("0.0 min")
        self.lbl_total_items = QLabel("0")
        self.lbl_payment_split = QLabel("0% / 0%")
        self.lbl_skill = QLabel("-")

        # Card-based styling like in sidebar
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
            QLabel {
                font-size: 10px;
                color: #6B7280;
            }
        """

        gb_status = QGroupBox(self._t("dialogs.checkout_stats_status_section", "Status"))
        gb_status.setStyleSheet(card_style)
        f_status = QFormLayout(gb_status)
        f_status.setSpacing(8)
        f_status.setContentsMargins(12, 8, 12, 12)
        f_status.addRow(self._t("dialogs.checkout_stats_status", "Status:"), self.lbl_status)
        f_status.addRow(self._t("dialogs.checkout_stats_queue", "Queue-Länge:"), self.lbl_queue)
        f_status.addRow(self._t("dialogs.checkout_stats_skill", "Kassierer:"), self.lbl_skill)

        gb_customers = QGroupBox(self._t("dialogs.checkout_stats_customers_section", "Kunden"))
        gb_customers.setStyleSheet(card_style)
        f_customers = QFormLayout(gb_customers)
        f_customers.setSpacing(8)
        f_customers.setContentsMargins(12, 8, 12, 12)
        f_customers.addRow(self._t("dialogs.checkout_stats_customers", "Bedient:"), self.lbl_customers)
        f_customers.addRow(self._t("dialogs.checkout_stats_scan_avg", "Ø Scan-Zeit:"), self.lbl_scan_avg)
        f_customers.addRow(self._t("dialogs.checkout_stats_pay_avg", "Ø Bezahl-Zeit:"), self.lbl_pay_avg)
        f_customers.addRow(self._t("dialogs.checkout_stats_total_items", "Artikel gesamt:"), self.lbl_total_items)

        gb_payment = QGroupBox(self._t("dialogs.checkout_stats_payment_section", "Bezahlung"))
        gb_payment.setStyleSheet(card_style)
        f_payment = QFormLayout(gb_payment)
        f_payment.setSpacing(8)
        f_payment.setContentsMargins(12, 8, 12, 12)
        f_payment.addRow(self._t("dialogs.checkout_stats_payment_split", "Zahlungsart:"), self.lbl_payment_split)

        layout.addWidget(gb_status)
        layout.addWidget(gb_customers)
        layout.addWidget(gb_payment)

    def refresh(self):
        stats = self.sim_manager.get_live_checkout_stats(self.checkout_id)
        if not stats:
            return

        status_text = self._translate_status(stats.get("status", "unknown"))
        self.lbl_status.setText(status_text)
        self.lbl_queue.setText(str(stats.get("queue_length", 0)))
        self.lbl_customers.setText(str(stats.get("customers_served", 0)))
        self.lbl_scan_avg.setText(f"{stats.get('scan_avg_sec', 0.0) / 60.0:.2f} min")
        self.lbl_pay_avg.setText(f"{stats.get('pay_avg_sec', 0.0) / 60.0:.2f} min")
        self.lbl_total_items.setText(str(stats.get("total_items", 0)))
        
        # Translate payment split
        cash_label = self._t("dialogs.payment_cash", "Bar")
        card_label = self._t("dialogs.payment_card", "Karte")
        self.lbl_payment_split.setText(
            f"{cash_label} {stats.get('cash_percent', 0.0):.0f}% / {card_label} {stats.get('card_percent', 0.0):.0f}%"
        )
        
        # Translate skill name
        skill_raw = stats.get("skill", "-")
        skill_text = self._translate_skill(skill_raw)
        self.lbl_skill.setText(skill_text)

    def _translate_status(self, status):
        if not self.translator:
            return status
        key_map = {
            "open": "dialogs.checkout_status_open",
            "closed": "dialogs.checkout_status_closed",
            "malfunction": "dialogs.checkout_status_malfunction",
            "conflict": "dialogs.checkout_status_conflict",
        }
        return self.translator.get(key_map.get(status, ""), status)

    def _translate_skill(self, skill):
        """Translate skill name from German to current language."""
        if not self.translator:
            return skill
        skill_map = {
            "Azubi": "dialogs.checkout_skill_azubi",
            "Festangestellter": "dialogs.checkout_skill_festangestellter",
        }
        return self.translator.get(skill_map.get(skill, ""), skill)

    def _t(self, key, fallback):
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
