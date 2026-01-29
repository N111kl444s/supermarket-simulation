"""Statistics dialogs module."""

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
)
from PyQt6.QtCore import Qt, QTimer, QTime
from config import COLOR_BG_MAIN

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class StatisticsReportDialog(QDialog):
    def __init__(self, stats, parent=None, translator=None, sim_manager=None):
        super().__init__(parent)
        self.translator = translator
        self.stats = stats or {}
        self.sim_manager = sim_manager
        self._live_timer = None
        title = (
            self.translator.get("dialogs.stats_report_title")
            if self.translator
            else "Statistikbericht"
        )
        self.setWindowTitle(title)
        self.setStyleSheet(f"QDialog {{ background-color: {COLOR_BG_MAIN.name()}; }}")
        self.setMinimumSize(1200, 820)
        self.setSizeGripEnabled(False)
        self._init_ui()
        if self.sim_manager is not None:
            self._start_live_updates()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        tabs.addTab(self._build_overview_tab(), self._t("dialogs.stats_tab_overview", "Übersicht"))
        tabs.addTab(self._build_customers_tab(), self._t("dialogs.stats_tab_customers", "Kunden"))
        tabs.addTab(self._build_payments_tab(), self._t("dialogs.stats_tab_payments", "Bezahlung"))
        tabs.addTab(self._build_operations_tab(), self._t("dialogs.stats_tab_operations", "Betrieb"))
        tabs.addTab(self._build_checkouts_tab(), self._t("dialogs.stats_tab_checkouts", "Kassen"))
        tabs.addTab(self._build_advanced_tab(), self._t("dialogs.stats_tab_advanced", "Erweitert"))
        tabs.addTab(self._build_export_tab(), self._t("dialogs.stats_tab_export", "Export"))

        layout.addWidget(tabs)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_label = self._t("dialogs.close", "Schließen")
        btns.button(QDialogButtonBox.StandardButton.Close).setText(close_label)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)

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
        if not self.sim_manager:
            return
        self.stats = self.sim_manager.get_statistics_snapshot()
        self._refresh_tables_and_charts()

    def _build_overview_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_overview_desc",
                    "Globale Kennzahlen und Durchschnittswerte der gesamten Simulation.",
                )
            )
        )

        gb = QGroupBox(self._t("dialogs.stats_overview_global", "Globale Kennzahlen"))
        form = QFormLayout(gb)

        global_stats = self.stats.get("global", {})
        times = global_stats.get("times", {})
        payment = global_stats.get("payment", {})

        self.lbl_overview_total_customers = QLabel()
        self.lbl_overview_total_served = QLabel()
        self.lbl_overview_total_items = QLabel()
        self.lbl_overview_avg_items = QLabel()
        self.lbl_overview_cash = QLabel()
        self.lbl_overview_card = QLabel()

        form.addRow(self._t("dialogs.stats_total_customers", "Kunden Gesamt:"), self.lbl_overview_total_customers)
        form.addRow(self._t("dialogs.stats_total_served", "Kunden bedient:"), self.lbl_overview_total_served)
        form.addRow(self._t("dialogs.stats_total_items", "Artikel gesamt:"), self.lbl_overview_total_items)
        form.addRow(self._t("dialogs.stats_avg_items", "Ø Artikel/Kunde:"), self.lbl_overview_avg_items)
        form.addRow(self._t("dialogs.stats_payment_cash", "Barzahlungen:"), self.lbl_overview_cash)
        form.addRow(self._t("dialogs.stats_payment_card", "Kartenzahlungen:"), self.lbl_overview_card)

        l.addWidget(gb)
        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_scheduled_open_info",
                    "Geplant geöffnet = Schließzeit − Öffnungszeit (laut Einstellungen).",
                )
            )
        )

        gb_time = QGroupBox(self._t("dialogs.stats_overview_times", "Durchschnittswerte"))
        form_time = QFormLayout(gb_time)
        self.lbl_overview_store_avg = QLabel()
        self.lbl_overview_queue_avg = QLabel()
        self.lbl_overview_service_avg = QLabel()
        form_time.addRow(self._t("dialogs.stats_store_stay_avg", "Ø Verweildauer (min):"), self.lbl_overview_store_avg)
        form_time.addRow(self._t("dialogs.stats_queue_wait_avg", "Ø Wartezeit (min):"), self.lbl_overview_queue_avg)
        form_time.addRow(self._t("dialogs.stats_service_time_avg", "Ø Servicezeit (min):"), self.lbl_overview_service_avg)
        l.addWidget(gb_time)

        gb_sat = QGroupBox(self._t("dialogs.stats_satisfaction", "Zufriedenheit"))
        sat_layout = QVBoxLayout(gb_sat)
        self.sat_bar = QProgressBar()
        self.sat_bar.setRange(0, 100)
        sat_layout.addWidget(self.sat_bar)
        if HAS_MATPLOTLIB:
            self.sat_pie_fig = Figure(figsize=(4, 2.2))
            self.sat_pie_canvas = FigureCanvas(self.sat_pie_fig)
            self.sat_pie_ax = self.sat_pie_fig.add_subplot(1, 1, 1)
            self.sat_pie_fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
            sat_layout.addWidget(self.sat_pie_canvas)
        l.addWidget(gb_sat)
        self.lbl_satisfaction_info = self._info_label(
            self._t(
                "dialogs.stats_satisfaction_desc",
                "Berechnung: Abzüge bei Ø‑Verweildauer > {store} min oder Ø‑Wartezeit > {queue} min (linear).",
            )
        )
        l.addWidget(self.lbl_satisfaction_info)

        l.addStretch()
        self._refresh_overview_labels()
        return tab

    def _build_customer_flow_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_flow_desc",
                    "Zeitmetriken (min) für Aufenthalt, Wartezeit und Service.",
                )
            )
        )

        times = self.stats.get("global", {}).get("times", {})
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(4)
        self.flow_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_metric", "Metrik"),
            self._t("dialogs.stats_min", "Min"),
            self._t("dialogs.stats_avg", "Ø"),
            self._t("dialogs.stats_max", "Max"),
        ])
        rows = [
            (
                self._t("dialogs.stats_store_stay", "Verweildauer"),
                times.get("store_stay_min", 0.0) / 60.0,
                times.get("store_stay_avg", 0.0) / 60.0,
                times.get("store_stay_max", 0.0) / 60.0,
            ),
            (
                self._t("dialogs.stats_queue_wait", "Wartezeit"),
                times.get("queue_wait_min", 0.0) / 60.0,
                times.get("queue_wait_avg", 0.0) / 60.0,
                times.get("queue_wait_max", 0.0) / 60.0,
            ),
            (
                self._t("dialogs.stats_service_time", "Servicezeit"),
                times.get("service_time_min", 0.0) / 60.0,
                times.get("service_time_avg", 0.0) / 60.0,
                times.get("service_time_max", 0.0) / 60.0,
            ),
        ]
        self.flow_table.setRowCount(len(rows))
        for r, (label, v_min, v_avg, v_max) in enumerate(rows):
            self.flow_table.setItem(r, 0, self._make_item(label))
            self.flow_table.setItem(r, 1, self._make_item(f"{v_min:.1f}", numeric=True))
            self.flow_table.setItem(r, 2, self._make_item(f"{v_avg:.1f}", numeric=True))
            self.flow_table.setItem(r, 3, self._make_item(f"{v_max:.1f}", numeric=True))
        self.flow_table.resizeColumnsToContents()
        self._style_table(self.flow_table)
        l.addWidget(self.flow_table)
        l.addStretch()
        return tab

    def _build_customers_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        sub_tabs = QTabWidget()

        # Subtab: Overview
        tab_overview = QWidget()
        l_overview = QVBoxLayout(tab_overview)
        l_overview.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_customers_desc",
                    "Kundenmix, Gesamtzahlen und zentrale Kennzahlen.",
                )
            )
        )

        gb = QGroupBox(self._t("dialogs.stats_customers_overview", "Kundenübersicht"))
        form = QFormLayout(gb)
        self.lbl_cust_total = QLabel()
        self.lbl_cust_normal = QLabel()
        self.lbl_cust_disabled = QLabel()
        self.lbl_cust_handheld = QLabel()
        form.addRow(self._t("dialogs.stats_total_customers", "Kunden Gesamt:"), self.lbl_cust_total)
        form.addRow(self._t("dialogs.stats_customers_normal", "Normal:"), self.lbl_cust_normal)
        form.addRow(self._t("dialogs.stats_customers_disabled", "Eingeschränkt:"), self.lbl_cust_disabled)
        form.addRow(self._t("dialogs.stats_customers_handheld", "Handscanner:"), self.lbl_cust_handheld)
        l_overview.addWidget(gb)

        if HAS_MATPLOTLIB:
            self.customers_fig = Figure(figsize=(5, 3))
            self.customers_canvas = FigureCanvas(self.customers_fig)
            self.customers_fig.subplots_adjust(
                left=0.06, right=0.96, top=0.88, bottom=0.12
            )
            self._refresh_customers_chart()
            l_overview.addWidget(self.customers_canvas)

        sub_tabs.addTab(tab_overview, self._t("dialogs.stats_subtab_overview", "Übersicht"))

        # Subtab: Times table
        tab_times = QWidget()
        l_times = QVBoxLayout(tab_times)
        l_times.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_flow_desc",
                    "Zeitmetriken für Aufenthalt, Wartezeit und Service (Min/Ø/Max).",
                )
            )
        )
        self.flow_table = QTableWidget()
        self.flow_table.setColumnCount(4)
        self.flow_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_metric", "Metrik"),
            self._t("dialogs.stats_min", "Min"),
            self._t("dialogs.stats_avg", "Ø"),
            self._t("dialogs.stats_max", "Max"),
        ])
        self._style_table(self.flow_table)
        l_times.addWidget(self.flow_table)
        sub_tabs.addTab(tab_times, self._t("dialogs.stats_subtab_times", "Zeiten"))

        # Subtab: Charts
        tab_charts = QWidget()
        l_charts = QVBoxLayout(tab_charts)
        l_charts.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_charts_desc_details",
                    "• Boxplot: Verteilung der Zeiten (Laden, Queue, Service)\n"
                    "• Histogramm: Verteilung der Queue‑Zeiten",
                )
            )
        )
        if HAS_MATPLOTLIB:
            self.charts_fig = Figure(figsize=(7, 6))
            self.charts_canvas = FigureCanvas(self.charts_fig)
            gs = self.charts_fig.add_gridspec(2, 2)
            self.ax_box = self.charts_fig.add_subplot(gs[0, 0])
            self.ax_pay = self.charts_fig.add_subplot(gs[0, 1])
            self.ax_cust = self.charts_fig.add_subplot(gs[1, 0])
            self.ax_hist = self.charts_fig.add_subplot(gs[1, 1])
            self.charts_fig.subplots_adjust(
                left=0.06,
                right=0.98,
                top=0.92,
                bottom=0.08,
                hspace=0.35,
                wspace=0.25,
            )
            self._refresh_charts()
            l_charts.addWidget(self.charts_canvas)
        sub_tabs.addTab(tab_charts, self._t("dialogs.stats_subtab_charts", "Diagramme"))

        # Subtab: Customer list
        tab_list = QWidget()
        l_list = QVBoxLayout(tab_list)
        l_list.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_customers_list_desc",
                    "Liste der Kunden mit Zeiten, Zahlung und Kasse.",
                )
            )
        )
        self.customers_list_table = QTableWidget()
        self.customers_list_table.setColumnCount(12)
        self.customers_list_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_customer_id", "ID"),
            self._t("dialogs.stats_customer_type", "Typ"),
            self._t("dialogs.stats_customer_handheld", "Handscanner"),
            self._t("dialogs.stats_customer_payment", "Zahlung"),
            self._t("dialogs.stats_customer_items", "Artikel"),
            self._t("dialogs.stats_customer_checkout", "Kasse"),
            self._t("dialogs.stats_customer_entry", "Eintritt"),
            self._t("dialogs.stats_customer_exit", "Verlassen"),
            self._t("dialogs.stats_customer_store", "Verweildauer (min)"),
            self._t("dialogs.stats_customer_queue", "Wartezeit (min)"),
            self._t("dialogs.stats_customer_service", "Service (min)"),
            self._t("dialogs.stats_customer_payment_time", "Bezahlen (min)"),
        ])
        self._style_table(self.customers_list_table)
        l_list.addWidget(self.customers_list_table)
        sub_tabs.addTab(tab_list, self._t("dialogs.stats_subtab_list", "Liste"))

        l.addWidget(sub_tabs)
        l.addStretch()
        self._refresh_customers_overview()
        self._refresh_customers_list_table()
        self._refresh_charts()
        return tab

    def _build_operations_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_operations_desc",
                    "Öffnungszeiten, Überzeit und Peak-Analyse.",
                )
            )
        )

        gb = QGroupBox(self._t("dialogs.stats_operations_title", "Betrieb"))
        form = QFormLayout(gb)
        self.lbl_ops_open = QLabel()
        self.lbl_ops_close = QLabel()
        self.lbl_ops_scheduled = QLabel()
        self.lbl_ops_actual = QLabel()
        self.lbl_ops_overtime = QLabel()
        self.lbl_ops_max_queue = QLabel()
        self.lbl_ops_busiest_hour = QLabel()

        form.addRow(self._t("dialogs.stats_open_time", "Öffnet:"), self.lbl_ops_open)
        form.addRow(self._t("dialogs.stats_close_time", "Schließt:"), self.lbl_ops_close)
        form.addRow(self._t("dialogs.stats_scheduled_open", "Geplant geöffnet:"), self.lbl_ops_scheduled)
        form.addRow(self._t("dialogs.stats_actual_open", "Tatsächlich geöffnet:"), self.lbl_ops_actual)
        form.addRow(self._t("dialogs.stats_overtime", "Überzeit:"), self.lbl_ops_overtime)
        form.addRow(self._t("dialogs.stats_max_queue", "Max. Queue:"), self.lbl_ops_max_queue)
        self.lbl_ops_max_queue_time = QLabel()
        form.addRow(self._t("dialogs.stats_max_queue_time", "Zeit Max. Queue:"), self.lbl_ops_max_queue_time)
        form.addRow(self._t("dialogs.stats_busiest_hour", "Spitzenstunde:"), self.lbl_ops_busiest_hour)

        l.addWidget(gb)

        self.hourly_table = QTableWidget()
        self.hourly_table.setColumnCount(2)
        self.hourly_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_hour", "Stunde"),
            self._t("dialogs.stats_avg_customers", "Ø Kunden im Laden"),
        ])
        self._style_table(self.hourly_table)
        l.addWidget(self.hourly_table)

        l.addStretch()
        self._refresh_operations_tab()
        return tab

    def _build_payments_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_payments_desc",
                    "Verteilung und Dauer der Zahlungsmethoden (Bar/Karte).",
                )
            )
        )

        pay = self.stats.get("global", {}).get("payment", {})
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(4)
        self.payments_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_payment_method", "Methode"),
            self._t("dialogs.stats_payment_count", "Anzahl"),
            self._t("dialogs.stats_payment_avg", "Ø Zeit (min)"),
            self._t("dialogs.stats_payment_range", "Min/Max (min)"),
        ])

        cash = pay.get("cash_time", {})
        card = pay.get("card_time", {})
        rows = [
            (
                self._t("dialogs.stats_chart_cash", "Bar"),
                pay.get("cash_count", 0),
                cash.get("avg", 0.0) / 60.0,
                f"{cash.get('min', 0.0) / 60.0:.1f}/{cash.get('max', 0.0) / 60.0:.1f}",
            ),
            (
                self._t("dialogs.stats_chart_card", "Karte"),
                pay.get("card_count", 0),
                card.get("avg", 0.0) / 60.0,
                f"{card.get('min', 0.0) / 60.0:.1f}/{card.get('max', 0.0) / 60.0:.1f}",
            ),
        ]
        self.payments_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.payments_table.setItem(r, 0, self._make_item(row[0]))
            self.payments_table.setItem(r, 1, self._make_item(row[1], numeric=True))
            self.payments_table.setItem(r, 2, self._make_item(row[2], numeric=True))
            self.payments_table.setItem(r, 3, self._make_item(row[3], numeric=False))
        self.payments_table.resizeColumnsToContents()
        self._style_table(self.payments_table)
        l.addWidget(self.payments_table)
        l.addStretch()
        return tab

    def _build_checkouts_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        sub_tabs = QTabWidget()

        tab_overview = QWidget()
        l_overview = QVBoxLayout(tab_overview)
        l_overview.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_checkouts_desc",
                    "Übersicht aller Kassen mit Queue-, Service- und Zahlungsmetriken.",
                )
            )
        )

        self.checkouts_table = QTableWidget()
        self.checkouts_table.setColumnCount(10)
        self.checkouts_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_checkout_id", "ID"),
            self._t("dialogs.stats_checkout_skill", "Skill"),
            self._t("dialogs.stats_checkout_customers", "Kunden"),
            self._t("dialogs.stats_checkout_items", "Artikel"),
            self._t("dialogs.stats_checkout_queue_avg", "Ø Queue (min)"),
            self._t("dialogs.stats_checkout_service_avg", "Ø Service (min)"),
            self._t("dialogs.stats_checkout_scan_avg", "Ø Scan (min)"),
            self._t("dialogs.stats_checkout_pay_avg", "Ø Bezahlen (min)"),
            self._t("dialogs.stats_checkout_cash", "Bar"),
            self._t("dialogs.stats_checkout_card", "Karte"),
        ])
        self._style_table(self.checkouts_table)
        l_overview.addWidget(self.checkouts_table)

        if HAS_MATPLOTLIB:
            self.checkouts_fig = Figure(figsize=(6, 3))
            self.checkouts_canvas = FigureCanvas(self.checkouts_fig)
            self.checkouts_fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.18)
            self._refresh_checkouts_chart()
            l_overview.addWidget(self.checkouts_canvas)

        sub_tabs.addTab(tab_overview, self._t("dialogs.stats_subtab_overview", "Übersicht"))

        tab_details = QWidget()
        l_details = QVBoxLayout(tab_details)
        l_details.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_checkouts_detail_desc",
                    "Verfügbarkeit, Queue-Längen und Problemzeiten pro Kasse.",
                )
            )
        )

        self.checkouts_detail_table = QTableWidget()
        self.checkouts_detail_table.setColumnCount(12)
        self.checkouts_detail_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_checkout_id", "ID"),
            self._t("dialogs.stats_checkout_type", "Typ"),
            self._t("dialogs.stats_queue_min", "Queue Min"),
            self._t("dialogs.stats_queue_avg", "Queue Ø"),
            self._t("dialogs.stats_queue_max", "Queue Max"),
            self._t("dialogs.stats_uptime", "Uptime %"),
            self._t("dialogs.stats_downtime", "Downtime (min)"),
            self._t("dialogs.stats_malfunction_time", "Störung (min)"),
            self._t("dialogs.stats_conflict_time", "Konflikt (min)"),
            self._t("dialogs.stats_malfunction_events", "Störungen"),
            self._t("dialogs.stats_conflict_events", "Konflikte"),
            self._t("dialogs.stats_handheld", "Handscanner"),
        ])
        self._style_table(self.checkouts_detail_table)
        l_details.addWidget(self.checkouts_detail_table)
        l_details.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_checkouts_hint",
                    "Hinweis: Die Zuordnung der IDs siehst du auf der Simulationsfläche.",
                )
            )
        )

        sub_tabs.addTab(tab_details, self._t("dialogs.stats_subtab_details", "Details"))

        l.addWidget(sub_tabs)
        l.addStretch()
        self._refresh_checkouts_table()
        self._refresh_checkouts_detail_table()
        return tab

    def _build_checkouts_detail_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_checkouts_detail_desc",
                    "Verfügbarkeit, Queue-Längen und Problemzeiten pro Kasse.",
                )
            )
        )

        self.checkouts_detail_table = QTableWidget()
        self.checkouts_detail_table.setColumnCount(12)
        self.checkouts_detail_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_checkout_id", "ID"),
            self._t("dialogs.stats_checkout_type", "Typ"),
            self._t("dialogs.stats_queue_min", "Queue Min"),
            self._t("dialogs.stats_queue_avg", "Queue Ø"),
            self._t("dialogs.stats_queue_max", "Queue Max"),
            self._t("dialogs.stats_uptime", "Uptime %"),
            self._t("dialogs.stats_downtime", "Downtime (min)"),
            self._t("dialogs.stats_malfunction_time", "Störung (min)"),
            self._t("dialogs.stats_conflict_time", "Konflikt (min)"),
            self._t("dialogs.stats_malfunction_events", "Störungen"),
            self._t("dialogs.stats_conflict_events", "Konflikte"),
            self._t("dialogs.stats_handheld", "Handscanner"),
        ])
        self._style_table(self.checkouts_detail_table)
        l.addWidget(self.checkouts_detail_table)
        l.addStretch()
        self._refresh_checkouts_detail_table()
        return tab

    def _build_advanced_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_advanced_desc",
                    "Zusätzliche Analysen wie Skill-Vergleich und Effizienz-Ratio.",
                )
            )
        )
        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_skill_ratio_info",
                    "Effizienz‑Ratio = Ø Scanzeit Azubi / Ø Scanzeit Pro (Azubi = 1.00x Basis).",
                )
            )
        )

        self.skill_table = QTableWidget()
        self.skill_table.setColumnCount(4)
        self.skill_table.setHorizontalHeaderLabels([
            self._t("dialogs.stats_skill", "Skill"),
            self._t("dialogs.stats_scan_avg", "Ø Scan (min)"),
            self._t("dialogs.stats_pay_avg", "Ø Bezahlen (min)"),
            self._t("dialogs.stats_efficiency_ratio", "Effizienz‑Ratio"),
        ])
        self._style_table(self.skill_table)
        l.addWidget(self.skill_table)

        l.addStretch()
        self._refresh_advanced_tab()
        return tab

    def _build_charts_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_charts_desc",
                    "Diagramme zur schnellen visuellen Einordnung der Ergebnisse.",
                )
            )
        )
        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_charts_desc_details",
                    "• Boxplot: Verteilung der Zeiten (Laden, Queue, Service)\n"
                    "• Pie: Zahlungsarten (Bar/Karte)\n"
                    "• Pie: Kundentypen (Normal/Eingeschränkt)\n"
                    "• Histogramm: Verteilung der Queue‑Zeiten",
                )
            )
        )

        if not HAS_MATPLOTLIB:
            l.addWidget(
                QLabel(
                    self._t(
                        "dialogs.stats_charts_missing",
                        "Matplotlib ist nicht installiert. Diagramme sind deaktiviert.",
                    )
                )
            )
            return tab

        self.charts_fig = Figure(figsize=(7, 6))
        self.charts_canvas = FigureCanvas(self.charts_fig)

        gs = self.charts_fig.add_gridspec(2, 2)
        self.ax_box = self.charts_fig.add_subplot(gs[0, 0])
        self.ax_pay = self.charts_fig.add_subplot(gs[0, 1])
        self.ax_cust = self.charts_fig.add_subplot(gs[1, 0])
        self.ax_hist = self.charts_fig.add_subplot(gs[1, 1])

        self._refresh_charts()
        l.addWidget(self.charts_canvas)
        return tab

    def _stats_list(self, stats, key):
        raw = stats.get("_raw", {})
        return raw.get(key, []) if isinstance(raw, dict) else []

    def _build_export_tab(self):
        tab = QWidget()
        l = QVBoxLayout(tab)

        l.addWidget(
            self._info_label(
                self._t(
                    "dialogs.stats_export_desc",
                    "Exportiere die Statistiken als JSON oder CSV für weitere Analysen.",
                )
            )
        )

        btn_json = QPushButton(self._t("dialogs.export_json", "Als JSON speichern"))
        btn_csv = QPushButton(self._t("dialogs.export_csv", "Als CSV speichern"))
        btn_json.clicked.connect(self._export_json)
        btn_csv.clicked.connect(self._export_csv)

        l.addWidget(btn_json)
        l.addWidget(btn_csv)
        l.addStretch()
        return tab

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("dialogs.export_json", "Als JSON speichern"),
            "stats_report.json",
            "JSON (*.json)",
        )
        if not path:
            return
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self._t("dialogs.export_csv", "Als CSV speichern"),
            "stats_report.csv",
            "CSV (*.csv)",
        )
        if not path:
            return
        import csv

        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["section", "key", "value"])

            global_stats = self.stats.get("global", {})
            for key, value in global_stats.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        writer.writerow(["global", f"{key}.{sub_key}", sub_val])
                else:
                    writer.writerow(["global", key, value])

            for cid, c_stats in self.stats.get("checkouts", {}).items():
                writer.writerow(["checkout", cid, ""])
                for key, value in c_stats.items():
                    if isinstance(value, dict):
                        for sub_key, sub_val in value.items():
                            writer.writerow([f"checkout.{cid}", f"{key}.{sub_key}", sub_val])
                    else:
                        writer.writerow([f"checkout.{cid}", key, value])

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

    def _style_table(self, table):
        table.setAlternatingRowColors(True)
        table.setStyleSheet(
            "QTableWidget { background-color: #e8f3ff; color: #102030; gridline-color: #b7d6ff; }"
            "QHeaderView::section { background-color: #cfe6ff; color: #102030; padding: 6px; border: 1px solid #b7d6ff; }"
            "QTableWidget::item { padding: 4px; }"
            "QTableWidget::item:alternate { background-color: #f5fbff; }"
        )
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSortIndicatorShown(True)
        table.setSortingEnabled(True)
        table.verticalHeader().setVisible(False)
        table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow
        )
        table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )

    def _begin_table_update(self, table):
        header = table.horizontalHeader()
        sort_col = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()
        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
        table.clearContents()
        return was_sorting, sort_col, sort_order

    def _end_table_update(self, table, sort_state=None):
        table.setSortingEnabled(True)
        if not sort_state:
            return
        was_sorting, sort_col, sort_order = sort_state
        if was_sorting and sort_col >= 0:
            table.sortItems(sort_col, sort_order)

    def _make_item(self, value, numeric=False):
        item = QTableWidgetItem(str(value))
        if numeric:
            try:
                item.setData(Qt.ItemDataRole.EditRole, float(value))
            except Exception:
                pass
        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        return item

    def _fit_table_height(self, table, max_rows=12):
        rows = table.rowCount()
        if rows <= 0:
            return
        header_h = table.horizontalHeader().height()
        row_h = table.verticalHeader().defaultSectionSize()
        visible_rows = rows if max_rows is None else min(rows, max_rows)
        total_h = header_h + (row_h * visible_rows) + 8
        table.setMinimumHeight(total_h)
        table.setMaximumHeight(total_h)

    def _refresh_overview_labels(self):
        global_stats = self.stats.get("global", {})
        times = global_stats.get("times", {})
        payment = global_stats.get("payment", {})

        self.lbl_overview_total_customers.setText(str(global_stats.get("total_customers_spawned", 0)))
        self.lbl_overview_total_served.setText(str(global_stats.get("total_customers_served", 0)))
        self.lbl_overview_total_items.setText(str(global_stats.get("total_items_processed", 0)))
        self.lbl_overview_avg_items.setText(f"{global_stats.get('avg_items_per_customer', 0.0):.2f}")
        self.lbl_overview_cash.setText(str(payment.get("cash_count", 0)))
        self.lbl_overview_card.setText(str(payment.get("card_count", 0)))

        self.lbl_overview_store_avg.setText(f"{times.get('store_stay_avg', 0.0) / 60.0:.1f}")
        self.lbl_overview_queue_avg.setText(f"{times.get('queue_wait_avg', 0.0) / 60.0:.1f}")
        self.lbl_overview_service_avg.setText(f"{times.get('service_time_avg', 0.0) / 60.0:.1f}")

        self.sat_bar.setValue(int(round(global_stats.get("satisfaction_score", 0.0))))
        self._refresh_satisfaction_pie()
        self._refresh_satisfaction_info()

    def _refresh_satisfaction_info(self):
        if not hasattr(self, "lbl_satisfaction_info"):
            return
        targets = self.stats.get("global", {}).get("satisfaction_targets", {})
        store_min = targets.get("store_min", 20.0)
        queue_min = targets.get("queue_min", 5.0)
        tpl = self._t(
            "dialogs.stats_satisfaction_desc",
            "Berechnung: Abzüge bei Ø‑Verweildauer > {store} min oder Ø‑Wartezeit > {queue} min (linear).",
        )
        self.lbl_satisfaction_info.setText(
            tpl.format(store=f"{store_min:.1f}", queue=f"{queue_min:.1f}")
        )

    def _refresh_satisfaction_pie(self):
        if not hasattr(self, "sat_pie_ax"):
            return
        self.sat_pie_ax.clear()
        global_stats = self.stats.get("global", {})
        split = global_stats.get("satisfaction_split", {})
        satisfied = split.get("satisfied", 0)
        unsatisfied = split.get("unsatisfied", 0)
        total = satisfied + unsatisfied
        if total > 0:
            self.sat_pie_ax.pie(
                [satisfied, unsatisfied],
                labels=[
                    self._t("dialogs.stats_satisfied", "Zufrieden"),
                    self._t("dialogs.stats_unsatisfied", "Unzufrieden"),
                ],
                autopct="%1.0f%%",
            )
        else:
            self._show_no_data(self.sat_pie_ax)
        self.sat_pie_ax.set_title(
            self._t(
                "dialogs.stats_satisfaction_pie_title",
                "Anteil zufriedener Kunden",
            )
        )
        if hasattr(self, "sat_pie_canvas"):
            self.sat_pie_canvas.draw_idle()

    def _refresh_tables_and_charts(self):
        self._refresh_overview_labels()
        self._refresh_customers_overview()
        self._refresh_customers_list_table()
        self._refresh_flow_table()
        self._refresh_payments_table()
        self._refresh_operations_tab()
        self._refresh_checkouts_table()
        self._refresh_checkouts_detail_table()
        self._refresh_advanced_tab()
        self._refresh_checkouts_chart()
        self._refresh_charts()

    def _refresh_customers_overview(self):
        if not hasattr(self, "lbl_cust_total"):
            return
        global_stats = self.stats.get("global", {})
        self.lbl_cust_total.setText(str(global_stats.get("total_customers_spawned", 0)))
        self.lbl_cust_normal.setText(str(global_stats.get("total_normal_customers", 0)))
        self.lbl_cust_disabled.setText(str(global_stats.get("total_disabled_customers", 0)))
        self.lbl_cust_handheld.setText(str(global_stats.get("total_handheld_customers", 0)))
        self._refresh_customers_chart()

    def _refresh_customers_chart(self):
        if not hasattr(self, "customers_fig"):
            return
        self.customers_fig.clear()
        ax = self.customers_fig.add_subplot(1, 1, 1)
        global_stats = self.stats.get("global", {})
        normal = global_stats.get("total_normal_customers", 0)
        disabled = global_stats.get("total_disabled_customers", 0)
        if normal + disabled > 0:
            ax.pie(
                [normal, disabled],
                labels=[
                    self._t("dialogs.stats_chart_normal", "Normal"),
                    self._t("dialogs.stats_chart_disabled", "Eingeschränkt"),
                ],
                autopct="%1.0f%%",
            )
        else:
            self._show_no_data(ax)
        ax.set_title(self._t("dialogs.stats_chart_customers_title", "Pie – Verteilung der Kundentypen"))
        if hasattr(self, "customers_canvas"):
            self.customers_canvas.draw_idle()

    def _refresh_customers_list_table(self):
        if not hasattr(self, "customers_list_table"):
            return
        sort_state = self._begin_table_update(self.customers_list_table)
        customers = self.stats.get("customers", {}).get("list", [])
        self.customers_list_table.setRowCount(len(customers))
        open_time = self.stats.get("global", {}).get("open_time", "00:00")
        for row, cust in enumerate(customers):
            entry_time = self._format_time_from_open(cust.get("entry_time_sec"), open_time)
            exit_time = self._format_time_from_open(cust.get("exit_time_sec"), open_time)
            store_min = (cust.get("store_stay_sec") or 0.0) / 60.0
            queue_min = (cust.get("queue_wait_sec") or 0.0) / 60.0
            service_min = (cust.get("service_time_sec") or 0.0) / 60.0
            payment_min = (cust.get("payment_time_sec") or 0.0) / 60.0
            self.customers_list_table.setItem(row, 0, self._make_item(cust.get("id", "-"), numeric=True))
            self.customers_list_table.setItem(
                row,
                1,
                self._make_item(
                    self._t("dialogs.stats_customer_type_disabled", "Eingeschränkt")
                    if cust.get("type") == "disabled"
                    else self._t("dialogs.stats_customer_type_normal", "Normal")
                ),
            )
            self.customers_list_table.setItem(
                row,
                2,
                self._make_item(
                    self._t("dialogs.stats_yes", "Ja")
                    if cust.get("handheld")
                    else self._t("dialogs.stats_no", "Nein")
                ),
            )
            self.customers_list_table.setItem(
                row,
                3,
                self._make_item(
                    self._t("dialogs.stats_chart_cash", "Bar")
                    if cust.get("payment_method") == "cash"
                    else self._t("dialogs.stats_chart_card", "Karte")
                ),
            )
            self.customers_list_table.setItem(row, 4, self._make_item(cust.get("items", 0), numeric=True))
            self.customers_list_table.setItem(row, 5, self._make_item(cust.get("checkout_id", "-"), numeric=True))
            self.customers_list_table.setItem(row, 6, self._make_item(entry_time))
            self.customers_list_table.setItem(row, 7, self._make_item(exit_time))
            self.customers_list_table.setItem(row, 8, self._make_item(f"{store_min:.2f}", numeric=True))
            self.customers_list_table.setItem(row, 9, self._make_item(f"{queue_min:.2f}", numeric=True))
            self.customers_list_table.setItem(row, 10, self._make_item(f"{service_min:.2f}", numeric=True))
            self.customers_list_table.setItem(row, 11, self._make_item(f"{payment_min:.2f}", numeric=True))
        self._fit_table_height(self.customers_list_table, max_rows=10)
        self._end_table_update(self.customers_list_table, sort_state)

    def _refresh_flow_table(self):
        if not hasattr(self, "flow_table"):
            return
        sort_state = self._begin_table_update(self.flow_table)
        times = self.stats.get("global", {}).get("times", {})
        rows = [
            (
                self._t("dialogs.stats_store_stay", "Verweildauer"),
                times.get("store_stay_min", 0.0) / 60.0,
                times.get("store_stay_avg", 0.0) / 60.0,
                times.get("store_stay_max", 0.0) / 60.0,
            ),
            (
                self._t("dialogs.stats_queue_wait", "Wartezeit"),
                times.get("queue_wait_min", 0.0) / 60.0,
                times.get("queue_wait_avg", 0.0) / 60.0,
                times.get("queue_wait_max", 0.0) / 60.0,
            ),
            (
                self._t("dialogs.stats_service_time", "Servicezeit"),
                times.get("service_time_min", 0.0) / 60.0,
                times.get("service_time_avg", 0.0) / 60.0,
                times.get("service_time_max", 0.0) / 60.0,
            ),
        ]
        self.flow_table.setRowCount(len(rows))
        for r, (label, v_min, v_avg, v_max) in enumerate(rows):
            self.flow_table.setItem(r, 0, self._make_item(label))
            self.flow_table.setItem(r, 1, self._make_item(f"{v_min:.2f}", numeric=True))
            self.flow_table.setItem(r, 2, self._make_item(f"{v_avg:.2f}", numeric=True))
            self.flow_table.setItem(r, 3, self._make_item(f"{v_max:.2f}", numeric=True))
        self._fit_table_height(self.flow_table)
        self._end_table_update(self.flow_table, sort_state)

    def _refresh_payments_table(self):
        if not hasattr(self, "payments_table"):
            return
        sort_state = self._begin_table_update(self.payments_table)
        pay = self.stats.get("global", {}).get("payment", {})
        cash = pay.get("cash_time", {})
        card = pay.get("card_time", {})
        rows = [
            (
                self._t("dialogs.stats_chart_cash", "Bar"),
                pay.get("cash_count", 0),
                cash.get("avg", 0.0) / 60.0,
                f"{cash.get('min', 0.0) / 60.0:.2f}/{cash.get('max', 0.0) / 60.0:.2f}",
            ),
            (
                self._t("dialogs.stats_chart_card", "Karte"),
                pay.get("card_count", 0),
                card.get("avg", 0.0) / 60.0,
                f"{card.get('min', 0.0) / 60.0:.2f}/{card.get('max', 0.0) / 60.0:.2f}",
            ),
        ]
        self.payments_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.payments_table.setItem(r, 0, self._make_item(row[0]))
            self.payments_table.setItem(r, 1, self._make_item(row[1], numeric=True))
            self.payments_table.setItem(r, 2, self._make_item(f"{row[2]:.2f}", numeric=True))
            self.payments_table.setItem(r, 3, self._make_item(row[3], numeric=False))
        self._fit_table_height(self.payments_table)
        self._end_table_update(self.payments_table, sort_state)

    def _refresh_checkouts_table(self):
        if not hasattr(self, "checkouts_table"):
            return
        sort_state = self._begin_table_update(self.checkouts_table)
        checkout_stats = self.stats.get("checkouts", {})
        self.checkouts_table.setRowCount(len(checkout_stats))
        for row, (cid, c_stats) in enumerate(sorted(checkout_stats.items(), key=lambda x: x[0])):
            queue_avg = c_stats.get("queue_wait", {}).get("avg", 0.0) / 60.0
            service_avg = c_stats.get("service_time", {}).get("avg", 0.0) / 60.0
            payment = c_stats.get("payment", {})
            pay_avg = payment.get("total_time", {}).get("avg", 0.0) / 60.0
            scan_avg = max(0.0, service_avg - pay_avg)

            self.checkouts_table.setItem(row, 0, self._make_item(str(cid), numeric=True))
            self.checkouts_table.setItem(row, 1, self._make_item(str(c_stats.get("skill", "-"))))
            self.checkouts_table.setItem(row, 2, self._make_item(str(c_stats.get("customers_served", 0)), numeric=True))
            self.checkouts_table.setItem(row, 3, self._make_item(str(c_stats.get("total_items", 0)), numeric=True))
            self.checkouts_table.setItem(row, 4, self._make_item(f"{queue_avg:.2f}", numeric=True))
            self.checkouts_table.setItem(row, 5, self._make_item(f"{service_avg:.2f}", numeric=True))
            self.checkouts_table.setItem(row, 6, self._make_item(f"{scan_avg:.2f}", numeric=True))
            self.checkouts_table.setItem(row, 7, self._make_item(f"{pay_avg:.2f}", numeric=True))
            self.checkouts_table.setItem(row, 8, self._make_item(str(payment.get("cash_count", 0)), numeric=True))
            self.checkouts_table.setItem(row, 9, self._make_item(str(payment.get("card_count", 0)), numeric=True))
        self._fit_table_height(self.checkouts_table)
        self._end_table_update(self.checkouts_table, sort_state)

    def _refresh_operations_tab(self):
        if not hasattr(self, "lbl_ops_open"):
            return
        global_stats = self.stats.get("global", {})
        peak = global_stats.get("peak", {})
        self.lbl_ops_open.setText(global_stats.get("open_time", "-"))
        self.lbl_ops_close.setText(global_stats.get("close_time", "-"))
        self.lbl_ops_scheduled.setText(
            self._format_duration(global_stats.get("scheduled_open_seconds", 0.0))
        )
        self.lbl_ops_actual.setText(
            self._format_duration(global_stats.get("actual_open_seconds", 0.0))
        )
        self.lbl_ops_overtime.setText(
            self._format_duration(global_stats.get("overtime_seconds", 0.0))
        )
        max_queue = peak.get("max_queue_len", 0)
        max_ids = peak.get("max_queue_checkouts", [])
        if max_queue > 0 and max_ids:
            ids_text = ", ".join(str(cid) for cid in max_ids)
            self.lbl_ops_max_queue.setText(f"{max_queue} (Kasse {ids_text})")
        else:
            self.lbl_ops_max_queue.setText(str(max_queue))
        max_queue_time = peak.get("max_queue_time_sec")
        if max_queue_time is not None:
            t = QTime.fromString(global_stats.get("open_time", "00:00"), "HH:mm")
            if t.isValid():
                t = t.addSecs(int(max_queue_time))
                self.lbl_ops_max_queue_time.setText(t.toString("HH:mm"))
            else:
                self.lbl_ops_max_queue_time.setText("-")
        else:
            self.lbl_ops_max_queue_time.setText("-")
        max_customers_time = peak.get("max_customers_time_sec")
        busiest = peak.get("busiest_hour")
        if max_customers_time is not None:
            t = QTime.fromString(global_stats.get("open_time", "00:00"), "HH:mm")
            if t.isValid():
                t = t.addSecs(int(max_customers_time))
                self.lbl_ops_busiest_hour.setText(t.toString("HH:mm"))
            else:
                self.lbl_ops_busiest_hour.setText("-")
        elif busiest is not None:
            t = QTime.fromString(global_stats.get("open_time", "00:00"), "HH:mm")
            if t.isValid():
                t = t.addSecs(int(busiest) * 3600)
                self.lbl_ops_busiest_hour.setText(t.toString("HH:mm"))
            else:
                self.lbl_ops_busiest_hour.setText(f"{busiest:02d}:00")
        else:
            self.lbl_ops_busiest_hour.setText("-")

        hourly = peak.get("avg_customers_by_hour", {})
        sort_state = self._begin_table_update(self.hourly_table)
        self.hourly_table.setRowCount(len(hourly))
        base_time = QTime.fromString(global_stats.get("open_time", "00:00"), "HH:mm")
        for row, (hour, avg_val) in enumerate(sorted(hourly.items())):
            label = f"{int(hour):02d}:00"
            if base_time.isValid():
                t = base_time.addSecs(int(hour) * 3600)
                label = t.toString("HH:mm")
            self.hourly_table.setItem(
                row, 0, self._make_item(label)
            )
            self.hourly_table.setItem(
                row, 1, self._make_item(f"{avg_val:.2f}", numeric=True)
            )
        self._fit_table_height(self.hourly_table, max_rows=24)
        self._end_table_update(self.hourly_table, sort_state)

    def _refresh_checkouts_detail_table(self):
        if not hasattr(self, "checkouts_detail_table"):
            return
        sort_state = self._begin_table_update(self.checkouts_detail_table)
        checkout_stats = self.stats.get("checkouts", {})
        self.checkouts_detail_table.setRowCount(len(checkout_stats))
        for row, (cid, c_stats) in enumerate(sorted(checkout_stats.items(), key=lambda x: x[0])):
            q = c_stats.get("queue_length", {})
            a = c_stats.get("availability", {})
            events = c_stats.get("events", {})
            self.checkouts_detail_table.setItem(row, 0, self._make_item(str(cid), numeric=True))
            self.checkouts_detail_table.setItem(row, 1, self._make_item(str(c_stats.get("type", "-"))))
            self.checkouts_detail_table.setItem(row, 2, self._make_item(f"{q.get('min', 0):.0f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 3, self._make_item(f"{q.get('avg', 0.0):.2f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 4, self._make_item(f"{q.get('max', 0):.0f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 5, self._make_item(f"{a.get('uptime_percent', 0.0):.2f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 6, self._make_item(f"{a.get('downtime_time_sec', 0.0) / 60.0:.2f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 7, self._make_item(f"{a.get('malfunction_time_sec', 0.0) / 60.0:.2f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 8, self._make_item(f"{a.get('conflict_time_sec', 0.0) / 60.0:.2f}", numeric=True))
            self.checkouts_detail_table.setItem(row, 9, self._make_item(str(events.get("malfunction_events", 0)), numeric=True))
            self.checkouts_detail_table.setItem(row, 10, self._make_item(str(events.get("conflict_events", 0)), numeric=True))
            self.checkouts_detail_table.setItem(row, 11, self._make_item(str(c_stats.get("handheld_customers", 0)), numeric=True))
        self._fit_table_height(self.checkouts_detail_table)
        self._end_table_update(self.checkouts_detail_table, sort_state)

    def _refresh_advanced_tab(self):
        if not hasattr(self, "skill_table"):
            return
        sort_state = self._begin_table_update(self.skill_table)
        skill = self.stats.get("advanced", {}).get("skill", {})
        ratio = skill.get("efficiency_ratio", 0.0)
        ratio_text = f"{ratio:.2f}x" if ratio > 0 else "-"
        rows = [
            (
                self._t("dialogs.stats_skill_newbie", "Azubi"),
                skill.get("newbie", {}).get("scan_time", {}).get("avg", 0.0) / 60.0,
                skill.get("newbie", {}).get("pay_time", {}).get("avg", 0.0) / 60.0,
                "1.00x",
            ),
            (
                self._t("dialogs.stats_skill_pro", "Pro"),
                skill.get("pro", {}).get("scan_time", {}).get("avg", 0.0) / 60.0,
                skill.get("pro", {}).get("pay_time", {}).get("avg", 0.0) / 60.0,
                ratio_text,
            ),
        ]
        self.skill_table.setRowCount(len(rows))
        for r, (label, scan_avg, pay_avg, ratio) in enumerate(rows):
            self.skill_table.setItem(r, 0, self._make_item(label))
            self.skill_table.setItem(r, 1, self._make_item(f"{scan_avg:.2f}", numeric=True))
            self.skill_table.setItem(r, 2, self._make_item(f"{pay_avg:.2f}", numeric=True))
            self.skill_table.setItem(r, 3, self._make_item(ratio))
        self._fit_table_height(self.skill_table)
        self._end_table_update(self.skill_table, sort_state)

    def _refresh_checkouts_chart(self):
        if not hasattr(self, "checkouts_fig"):
            return
        self.checkouts_fig.clear()
        ax = self.checkouts_fig.add_subplot(1, 1, 1)
        checkout_stats = self.stats.get("checkouts", {})
        labels = []
        values = []
        for cid, c_stats in checkout_stats.items():
            labels.append(str(cid))
            values.append(c_stats.get("service_time", {}).get("avg", 0.0) / 60.0)
        if values:
            ax.bar(labels, values)
        else:
            self._show_no_data(ax)
        ax.set_title(self._t("dialogs.stats_checkout_service_bar", "Ø Servicezeit je Kasse"))
        ax.set_xlabel(self._t("dialogs.stats_checkout_id", "ID"))
        ax.set_ylabel(self._t("dialogs.stats_minutes", "Min"))
        if hasattr(self, "checkouts_canvas"):
            self.checkouts_canvas.draw_idle()

    def _refresh_charts(self):
        if not hasattr(self, "charts_fig"):
            return
        self.ax_box.clear()
        self.ax_pay.clear()
        self.ax_cust.clear()
        self.ax_hist.clear()

        global_stats = self.stats.get("global", {})
        store_vals = self._stats_list(self.stats, "store_stay_times")
        queue_vals = self._stats_list(self.stats, "queue_wait_times")
        service_vals = self._stats_list(self.stats, "service_times")

        if store_vals or queue_vals or service_vals:
            self.ax_box.boxplot(
                [store_vals or [0], queue_vals or [0], service_vals or [0]],
                labels=[
                    self._t("dialogs.stats_chart_store", "Laden"),
                    self._t("dialogs.stats_chart_queue", "Queue"),
                    self._t("dialogs.stats_chart_service", "Service"),
                ],
            )
        else:
            self._show_no_data(self.ax_box)
        self.ax_box.set_title(
            self._t(
                "dialogs.stats_chart_times_title",
                "Boxplot – Verteilung der Aufenthalts-, Queue- und Servicezeiten",
            )
        )

        pay = global_stats.get("payment", {})
        cash = pay.get("cash_count", 0)
        card = pay.get("card_count", 0)
        if cash + card > 0:
            self.ax_pay.pie(
                [cash, card],
                labels=[
                    self._t("dialogs.stats_chart_cash", "Bar"),
                    self._t("dialogs.stats_chart_card", "Karte"),
                ],
                autopct="%1.0f%%",
            )
        else:
            self._show_no_data(self.ax_pay)
        self.ax_pay.set_title(
            self._t(
                "dialogs.stats_chart_payment_title",
                "Pie – Anteil der Zahlungsmethoden",
            )
        )

        normal = global_stats.get("total_normal_customers", 0)
        disabled = global_stats.get("total_disabled_customers", 0)
        if normal + disabled > 0:
            self.ax_cust.pie(
                [normal, disabled],
                labels=[
                    self._t("dialogs.stats_chart_normal", "Normal"),
                    self._t("dialogs.stats_chart_disabled", "Eingeschränkt"),
                ],
                autopct="%1.0f%%",
            )
        else:
            self._show_no_data(self.ax_cust)
        self.ax_cust.set_title(
            self._t(
                "dialogs.stats_chart_customers_title",
                "Pie – Verteilung der Kundentypen",
            )
        )

        if queue_vals:
            self.ax_hist.hist(queue_vals, bins=10)
        else:
            self._show_no_data(self.ax_hist)
        self.ax_hist.set_title(
            self._t(
                "dialogs.stats_chart_queue_hist",
                "Histogramm – Verteilung der Queue-Zeiten",
            )
        )
        self.ax_hist.set_xlabel(self._t("dialogs.stats_chart_minutes", "Minuten"))
        if hasattr(self, "charts_canvas"):
            self.charts_canvas.draw_idle()

    def _format_duration(self, seconds):
        total = int(round(seconds))
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h}:{m:02d}"

    def _format_time_from_open(self, seconds, open_time_str):
        if seconds is None:
            return "-"
        base = QTime.fromString(open_time_str or "00:00", "HH:mm")
        if base.isValid():
            return base.addSecs(int(seconds)).toString("HH:mm")
        return "-"

    def _show_no_data(self, ax):
        ax.text(
            0.5,
            0.5,
            self._t("dialogs.stats_no_data", "Keine Daten"),
            transform=ax.transAxes,
            ha="center",
            va="center",
        )
        ax.set_axis_off()


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
