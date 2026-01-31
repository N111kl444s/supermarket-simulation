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
    QFileDialog,
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
        
        # Add export tab (keep legacy for now)
        export_tab = self._build_export_tab()
        self.tabs.addTab(
            export_tab,
            "⚙️ " + self._t("dialogs.stats_tab_export", "Export")
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

    # Legacy tab builders removed - using new component-based tabs
    # Export tab kept for backward compatibility
    
    def _build_export_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_export_desc",
                    "Exportiere die Statistiken in verschiedenen Formaten für weitere Analysen.",
                )
            )
        )

        # JSON Export
        btn_json = QPushButton("📊 " + self._t("dialogs.export_json", "Als JSON speichern"))
        btn_json.setToolTip("Vollständiger Datensatz für Entwickler und API-Integration")
        btn_json.clicked.connect(self._export_json_comprehensive)
        
        # CSV Export
        btn_csv = QPushButton("📄 " + self._t("dialogs.export_csv", "Als CSV speichern"))
        btn_csv.setToolTip("Tabellarische Daten für Excel, Pivot-Tabellen, etc.")
        btn_csv.clicked.connect(self._export_csv_comprehensive)
        
        # PDF Export (placeholder for future implementation)
        btn_pdf = QPushButton("📋 " + self._t("dialogs.export_pdf", "Als PDF-Report exportieren"))
        btn_pdf.setToolTip("Druckfertiger professioneller Report (in Entwicklung)")
        btn_pdf.setEnabled(False)  # TODO: Implement PDF export
        btn_pdf.clicked.connect(self._export_pdf)

        l.addWidget(btn_json)
        l.addWidget(btn_csv)
        l.addWidget(btn_pdf)
        l.addStretch()
        return tab

    def _export_json_comprehensive(self):
        """Export comprehensive statistics as JSON covering all tabs."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("dialogs.export_json", "Als JSON speichern"),
            "statistikbericht.json",
            "JSON (*.json)",
        )
        if not path:
            return
        
        import json
        from datetime import datetime
        
        # Build comprehensive export structure
        export_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "simulation_date": self.stats.get("global", {}).get("current_time", ""),
                "version": "2.0"
            },
            "kpis": self._build_kpi_export(),
            "customers": self._build_customer_export(),
            "checkouts": self._build_checkout_export(),
            "operations": self._build_operations_export(),
            "raw_statistics": self.stats  # Include full raw data for reference
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def _export_csv_comprehensive(self):
        """Export comprehensive statistics as CSV with multiple sections."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("dialogs.export_csv", "Als CSV speichern"),
            "statistikbericht.csv",
            "CSV (*.csv)",
        )
        if not path:
            return
        
        import csv
        
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")  # Use semicolon for better Excel compatibility
            
            # Write metadata
            writer.writerow(["STATISTIKBERICHT"])
            writer.writerow(["Exportiert am", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            
            # Section 1: KPIs
            writer.writerow(["=== KPI DASHBOARD ==="])
            writer.writerow(["Kennzahl", "Wert", "Einheit", "Status"])
            kpi_data = self._build_kpi_export()
            for kpi, data in kpi_data.items():
                writer.writerow([
                    kpi,
                    data.get("value", ""),
                    data.get("unit", ""),
                    data.get("status", "")
                ])
            writer.writerow([])
            
            # Section 2: Customer Analysis
            writer.writerow(["=== KUNDENANALYSE ==="])
            writer.writerow(["Metrik", "Wert"])
            customer_data = self._build_customer_export()
            for key, value in customer_data.items():
                if isinstance(value, dict):
                    writer.writerow([key, ""])
                    for sub_key, sub_val in value.items():
                        writer.writerow(["  " + sub_key, sub_val])
                else:
                    writer.writerow([key, value])
            writer.writerow([])
            
            # Section 3: Checkout Performance
            writer.writerow(["=== KASSEN-PERFORMANCE ==="])
            checkout_data = self._build_checkout_export()
            if "checkouts" in checkout_data:
                headers = ["Kassen-ID", "Skill", "Kunden", "Artikel", "Ø Queue", "Ø Scan", "Uptime %", "Störungen"]
                writer.writerow(headers)
                for checkout in checkout_data["checkouts"]:
                    writer.writerow([
                        checkout.get("id", ""),
                        checkout.get("skill", ""),
                        checkout.get("customers_served", ""),
                        checkout.get("items_scanned", ""),
                        checkout.get("avg_queue_time", ""),
                        checkout.get("avg_scan_time", ""),
                        checkout.get("uptime_percent", ""),
                        checkout.get("failures", "")
                    ])
            writer.writerow([])
            
            # Section 4: Operations
            writer.writerow(["=== BETRIEBSSTATISTIK ==="])
            writer.writerow(["Metrik", "Wert"])
            operations_data = self._build_operations_export()
            for key, value in operations_data.items():
                writer.writerow([key, value])

    def _export_pdf(self):
        """Placeholder for PDF export functionality."""
        # TODO: Implement PDF report generation with charts and professional layout
        pass
    
    def _build_kpi_export(self):
        """Build KPI data structure for export."""
        global_stats = self.stats.get("global", {})
        
        return {
            "kunden_gesamt": {
                "value": global_stats.get("customers_total", 0),
                "unit": "Kunden",
                "status": "info"
            },
            "wartezeit_durchschnitt": {
                "value": round(global_stats.get("avg_queue_time", 0), 2),
                "unit": "Minuten",
                "status": "good" if global_stats.get("avg_queue_time", 0) <= 5 else "warning"
            },
            "zufriedenheit": {
                "value": round(global_stats.get("satisfaction", 0), 1),
                "unit": "%",
                "status": "good" if global_stats.get("satisfaction", 0) >= 70 else "critical"
            },
            "durchsatz": {
                "value": round(global_stats.get("throughput", 0), 1),
                "unit": "Kunden/h",
                "status": "info"
            },
            "ueberzeit": {
                "value": global_stats.get("overtime_minutes", 0),
                "unit": "Minuten",
                "status": "warning" if global_stats.get("overtime_minutes", 0) > 0 else "good"
            },
            "kassen_offen": {
                "value": global_stats.get("checkouts_open", 0),
                "unit": "Kassen",
                "status": "info"
            }
        }
    
    def _build_customer_export(self):
        """Build customer analysis data for export."""
        global_stats = self.stats.get("global", {})
        customers = self.stats.get("customers", [])
        
        # Calculate distributions
        total_customers = len(customers)
        disabled_count = sum(1 for c in customers if c.get("is_disabled", False))
        scanner_count = sum(1 for c in customers if c.get("has_handscanner", False))
        
        # Payment methods
        payment_methods = {}
        for c in customers:
            payment = c.get("payment_method", "unknown")
            payment_methods[payment] = payment_methods.get(payment, 0) + 1
        
        return {
            "gesamt": total_customers,
            "beeintraechtigt": disabled_count,
            "beeintraechtigt_prozent": round(100 * disabled_count / total_customers, 1) if total_customers > 0 else 0,
            "handscanner": scanner_count,
            "handscanner_prozent": round(100 * scanner_count / total_customers, 1) if total_customers > 0 else 0,
            "zahlungsmethoden": payment_methods,
            "zeitmetriken": {
                "wartezeit_min": round(global_stats.get("min_queue_time", 0), 2),
                "wartezeit_durchschnitt": round(global_stats.get("avg_queue_time", 0), 2),
                "wartezeit_max": round(global_stats.get("max_queue_time", 0), 2),
                "verweildauer_min": round(global_stats.get("min_total_time", 0), 2),
                "verweildauer_durchschnitt": round(global_stats.get("avg_total_time", 0), 2),
                "verweildauer_max": round(global_stats.get("max_total_time", 0), 2)
            }
        }
    
    def _build_checkout_export(self):
        """Build checkout performance data for export."""
        checkout_stats = self.stats.get("checkouts", {})
        
        checkouts_list = []
        for checkout_id, data in checkout_stats.items():
            checkouts_list.append({
                "id": checkout_id,
                "skill": data.get("skill_level", "unknown"),
                "customers_served": data.get("customers_served", 0),
                "items_scanned": data.get("items_scanned", 0),
                "avg_queue_time": round(data.get("avg_queue_time", 0), 2),
                "avg_scan_time": round(data.get("avg_scan_time", 0), 2),
                "uptime_percent": round(data.get("uptime_percent", 0), 1),
                "failures": data.get("failure_count", 0),
                "status": data.get("status", "unknown")
            })
        
        return {
            "checkouts": checkouts_list,
            "summary": {
                "total_checkouts": len(checkout_stats),
                "open_checkouts": sum(1 for d in checkout_stats.values() if d.get("status") == "open"),
                "failed_checkouts": sum(1 for d in checkout_stats.values() if d.get("status") == "failed")
            }
        }
    
    def _build_operations_export(self):
        """Build operations data for export."""
        global_stats = self.stats.get("global", {})
        
        return {
            "geplante_oeffnungszeit": global_stats.get("planned_open_hours", ""),
            "tatsaechliche_zeit": global_stats.get("elapsed_time", ""),
            "ueberzeit_minuten": global_stats.get("overtime_minutes", 0),
            "kunden_im_laden": global_stats.get("customers_in_store", 0),
            "kunden_in_warteschlange": global_stats.get("customers_in_queue", 0),
            "laengste_warteschlange": global_stats.get("longest_queue", 0),
            "peak_hour": global_stats.get("peak_hour", ""),
            "peak_customers": global_stats.get("peak_customers", 0)
        }

    # Legacy helper methods (kept for backward compatibility with export tab)
    
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
            self.translator.get("dialogs.checkout_stats_title")
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

        self.lbl_status = QLabel("-")
        self.lbl_queue = QLabel("0")
        self.lbl_customers = QLabel("0")
        self.lbl_scan_avg = QLabel("0.0 min")
        self.lbl_pay_avg = QLabel("0.0 min")
        self.lbl_total_items = QLabel("0")
        self.lbl_payment_split = QLabel("0% / 0%")
        self.lbl_skill = QLabel("-")

        gb_status = QGroupBox(self._t("dialogs.checkout_stats_status_section", "Status"))
        f_status = QFormLayout(gb_status)
        f_status.addRow(self._t("dialogs.checkout_stats_status", "Status:"), self.lbl_status)
        f_status.addRow(self._t("dialogs.checkout_stats_queue", "Queue-Länge:"), self.lbl_queue)
        f_status.addRow(self._t("dialogs.checkout_stats_skill", "Kassierer:"), self.lbl_skill)

        gb_customers = QGroupBox(self._t("dialogs.checkout_stats_customers_section", "Kunden"))
        f_customers = QFormLayout(gb_customers)
        f_customers.addRow(self._t("dialogs.checkout_stats_customers", "Bedient:"), self.lbl_customers)
        f_customers.addRow(self._t("dialogs.checkout_stats_scan_avg", "Ø Scan-Zeit:"), self.lbl_scan_avg)
        f_customers.addRow(self._t("dialogs.checkout_stats_pay_avg", "Ø Bezahl-Zeit:"), self.lbl_pay_avg)
        f_customers.addRow(self._t("dialogs.checkout_stats_total_items", "Artikel gesamt:"), self.lbl_total_items)

        gb_payment = QGroupBox(self._t("dialogs.checkout_stats_payment_section", "Bezahlung"))
        f_payment = QFormLayout(gb_payment)
        f_payment.addRow(self._t("dialogs.checkout_stats_payment_split", "Bar / Karte:"), self.lbl_payment_split)

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
        self.lbl_payment_split.setText(
            f"{stats.get('cash_percent', 0.0):.0f}% / {stats.get('card_percent', 0.0):.0f}%"
        )
        self.lbl_skill.setText(stats.get("skill", "-"))

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

    def _t(self, key, fallback):
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
