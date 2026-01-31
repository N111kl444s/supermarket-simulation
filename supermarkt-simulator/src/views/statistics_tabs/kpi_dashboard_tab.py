"""
KPI Dashboard Tab - Overview with key performance indicators with subtabs.
Provides a high-level business dashboard with subtabs for KPI cards and trends.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
    QTextEdit,
    QFrame,
    QTabWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextOption
from views.components.kpi_card import KPICard

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    FigureCanvas = None
    Figure = None
    HAS_MATPLOTLIB = False


class KPIDashboardTab(QWidget):
    """
    Professional KPI Dashboard Tab with subtabs:
    - KPI Übersicht: 6 KPI Cards (larger)
    - Trends & Empfehlungen: Trend chart and recommendations
    """
    
    def __init__(self, translator=None, parent=None):
        super().__init__(parent)
        self.translator = translator
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI layout with subtabs."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Create subtab widget
        self.subtabs = QTabWidget()
        self.subtabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #F1F5F9;
                color: #475569;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 600;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1E293B;
            }
            QTabBar::tab:hover {
                background-color: #E2E8F0;
            }
        """)
        
        # Create subtabs
        self.overview_tab = self._create_overview_tab()
        self.trends_tab = self._create_trends_tab()
        
        self.subtabs.addTab(self.overview_tab, self._t("stats.subtab_overview", "KPI Übersicht"))
        self.subtabs.addTab(self.trends_tab, self._t("stats.subtab_trends", "Trends & Empfehlungen"))
        
        layout.addWidget(self.subtabs)
    
    def _create_overview_tab(self):
        """Create overview subtab with 6 KPI cards."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(self._t("stats.kpi_dashboard_header", "KPI Dashboard"))
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; padding: 8px 0px;")
        layout.addWidget(header)
        
        # KPI Cards Grid (2 rows  3 columns)
        grid = self._create_kpi_grid()
        layout.addLayout(grid, 1)  # stretch factor 1 to fill available space
        
        return tab
    
    def _create_trends_tab(self):
        """Create trends and recommendations subtab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header
        header = QLabel(self._t("stats.trends_recommendations", "Trends & Empfehlungen"))
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setStyleSheet("color: #1E293B; padding: 8px 0px;")
        layout.addWidget(header)
        
        # Trend Analysis Section
        if HAS_MATPLOTLIB:
            trend_section = self._create_trend_section()
            layout.addWidget(trend_section)
        
        # Recommendations Section
        recommendations = self._create_recommendations_section()
        layout.addWidget(recommendations)
        
        layout.addStretch()
        return tab
    
    def _create_kpi_grid(self):
        """Create 6 KPI cards in a 3x2 grid, logically grouped."""
        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setContentsMargins(0, 0, 0, 0)
        
        # Row 1: Customer Metrics
        self.kpi_customers = KPICard(
            title=self._t("stats.kpi_customers_title", "Kunden bedient"),
            value="0",
            unit="",
            status="neutral",
            show_progress=False,
        )
        grid.addWidget(self.kpi_customers, 0, 0)
        
        self.kpi_basket_size = KPICard(
            title=self._t("stats.kpi_basket_size_title", "Ø Warenkorbgröße"),
            value="0.0",
            unit=self._t("stats.unit_items", "Artikel"),
            status="neutral",
            show_progress=False,
        )
        grid.addWidget(self.kpi_basket_size, 0, 1)
        
        self.kpi_satisfaction = KPICard(
            title=self._t("stats.kpi_satisfaction_title", "Zufriedenheit"),
            value="0",
            unit="%",
            status="good",
            show_progress=True,
            progress_max=100,
        )
        grid.addWidget(self.kpi_satisfaction, 0, 2)
        
        # Row 2: Checkout & Operations Metrics (Durchsatz, Wartezeit, Überzeit)
        self.kpi_throughput = KPICard(
            title=self._t("stats.kpi_throughput_title", "Durchsatz"),
            value="0.0",
            unit=self._t("stats.customers_per_hour", "Kunden/h"),
            status="good",
            show_progress=False,
        )
        grid.addWidget(self.kpi_throughput, 1, 0)
        
        self.kpi_wait_time = KPICard(
            title=self._t("stats.kpi_wait_time_title", "Ø Wartezeit"),
            value="0.0",
            unit="min",
            status="good",
            show_progress=False,
        )
        grid.addWidget(self.kpi_wait_time, 1, 1)
        
        self.kpi_overtime = KPICard(
            title=self._t("stats.kpi_overtime_title", "Überzeit"),
            value="0",
            unit="min",
            status="good",
            show_progress=False,
        )
        grid.addWidget(self.kpi_overtime, 1, 2)
        
        # Make columns equal width and add row stretch for symmetry
        for col in range(3):
            grid.setColumnStretch(col, 1)
        for row in range(2):
            grid.setRowStretch(row, 1)
        
        return grid
    
    def _create_trend_section(self):
        """Create the trend analysis chart section."""
        gb = QGroupBox(self._t("stats.trend_analysis_title", "Trendanalyse"))
        gb.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1E293B;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(gb)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Create matplotlib figure
        self.trend_figure = Figure(figsize=(10, 4.5))
        self.trend_canvas = FigureCanvas(self.trend_figure)
        self.trend_ax = self.trend_figure.add_subplot(1, 1, 1)
        self.trend_figure.subplots_adjust(left=0.06, right=0.98, top=0.85, bottom=0.20)
        
        layout.addWidget(self.trend_canvas)
        
        # Peak info label
        self.lbl_peak_info = QLabel(self._t("stats.peak_info", "Peak: Noch keine Daten"))
        self.lbl_peak_info.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 500; padding: 4px;")
        layout.addWidget(self.lbl_peak_info)
        
        return gb
    
    def _create_recommendations_section(self):
        """Create the automated recommendations section."""
        gb = QGroupBox(self._t("stats.recommendations_title", "Handlungsempfehlungen"))
        gb.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                color: #1E293B;
                border: 2px solid #CBD5E1;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        
        layout = QVBoxLayout(gb)
        layout.setContentsMargins(12, 12, 12, 12)
        
        self.txt_recommendations = QTextEdit()
        self.txt_recommendations.setReadOnly(True)
        self.txt_recommendations.setStyleSheet("""
            QTextEdit {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 4px;
                color: #334155;
                font-size: 13px;
                font-weight: 500;
                padding: 8px;
            }
        """)
        self.txt_recommendations.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.txt_recommendations.setPlainText(
            self._t("stats.recommendations_loading", "Lade Empfehlungen...")
        )
        # Don't set fixed height - let it expand naturally
        layout.addWidget(self.txt_recommendations, 1)
        
        return gb
    
    def update_kpis(self, stats, settings=None):
        """Update all KPI cards with current statistics."""
        global_stats = stats.get("global", {})
        times = global_stats.get("times", {})
        
        # Check if we have any data
        customers_served = global_stats.get("total_customers_served", 0)
        
        # Get thresholds from settings or use defaults
        from config import DEFAULT_SETTINGS
        if settings is None:
            settings = DEFAULT_SETTINGS
        
        overtime_good = settings.get("kpi_overtime_good_max", 5.0)
        overtime_warning = settings.get("kpi_overtime_warning_max", 15.0)
        wait_good = settings.get("kpi_wait_time_good_max", 5.0)
        wait_warning = settings.get("kpi_wait_time_warning_max", 8.0)
        sat_good = settings.get("kpi_satisfaction_good_min", 75.0)
        sat_warning = settings.get("kpi_satisfaction_warning_min", 50.0)
        
        # If no data yet, show "Keine Daten"
        if customers_served == 0:
            no_data_text = self._t("stats.no_data_available", "Keine Daten")
            self.kpi_customers.update_value(value="–", status="neutral")
            self.kpi_customers.set_subtitle(no_data_text)
            
            self.kpi_satisfaction.update_value(value="–", status="neutral", progress_value=0)
            self.kpi_satisfaction.set_subtitle(no_data_text)
            
            self.kpi_basket_size.update_value(value="–", status="neutral")
            self.kpi_basket_size.set_subtitle(no_data_text)
            
            self.kpi_throughput.update_value(value="–", status="neutral")
            self.kpi_throughput.set_subtitle(no_data_text)
            
            self.kpi_wait_time.update_value(value="–", status="neutral", progress_value=0)
            self.kpi_wait_time.set_subtitle(no_data_text)
            
            self.kpi_overtime.update_value(value="–", status="neutral", progress_value=0)
            self.kpi_overtime.set_subtitle(no_data_text)
            return
        
        # 1. Customers Served
        customers_served = global_stats.get("total_customers_served", 0)
        customers_target = global_stats.get("target_customers", 50)
        customers_diff = customers_served - customers_target
        customers_status = "good" if customers_diff >= 0 else "warning"
        
        self.kpi_customers.update_value(value=str(customers_served), status=customers_status)
        self.kpi_customers.set_subtitle(
            f"{'✅' if customers_diff >= 0 else '⚠️'} {customers_diff:+d} {self._t('stats.vs_target', 'vs. Ziel')} ({customers_target})"
        )
        
        # 2. Satisfaction
        satisfaction = int(round(global_stats.get("satisfaction_score", 0.0)))
        sat_status = "good" if satisfaction >= sat_good else ("warning" if satisfaction >= sat_warning else "critical")
        
        self.kpi_satisfaction.update_value(
            value=str(satisfaction),
            status=sat_status,
            progress_value=satisfaction
        )
        sat_text = self._t("stats.good", "GUT") if satisfaction >= sat_good else (self._t("stats.acceptable", "AKZEPTABEL") if satisfaction >= sat_warning else self._t("stats.critical", "KRITISCH"))
        self.kpi_satisfaction.set_subtitle(f"{self._t('stats.status', 'Status')}: {sat_text}")
        
        # 3. Basket Size (Average items per customer)
        basket_size = global_stats.get("avg_items_per_customer", 0.0)
        total_items = global_stats.get("total_items_processed", 0)
        basket_status = "good" if basket_size >= 10 else ("warning" if basket_size >= 5 else "neutral")
        
        self.kpi_basket_size.update_value(value=f"{basket_size:.1f}", status=basket_status)
        self.kpi_basket_size.set_subtitle(f"{total_items} {self._t('stats.items_total', 'Artikel gesamt')}")
        
        # 4. Throughput (from stats - wie in Sidebar)
        actual_throughput = global_stats.get("throughput_per_hour", 0.0)
        
        # Dynamic threshold: target customers per planned hours
        scheduled_open_seconds = global_stats.get("scheduled_open_seconds", 28800.0)  # default 8h
        scheduled_open_hours = scheduled_open_seconds / 3600.0
        target_throughput = customers_target / max(scheduled_open_hours, 1.0)
        throughput_ratio = actual_throughput / target_throughput if target_throughput > 0 else 0.0
        
        throughput_status = "good" if throughput_ratio >= 0.9 else ("warning" if throughput_ratio >= 0.7 else "critical")
        
        self.kpi_throughput.update_value(value=f"{actual_throughput:.1f}", status=throughput_status)
        self.kpi_throughput.set_subtitle(f"{self._t('stats.target', 'Ziel')}: {target_throughput:.1f} {self._t('stats.customers_per_hour', 'Kunden/h')}")
        
        # 5. Wait Time
        wait_time = times.get("queue_wait_avg", 0.0) / 60.0
        wait_status = "good" if wait_time <= wait_good else ("warning" if wait_time <= wait_warning else "critical")
        
        self.kpi_wait_time.update_value(
            value=f"{wait_time:.1f}",
            status=wait_status,
            progress_value=min(wait_time, 10.0)
        )
        target_label = self._t("stats.target_label", "Ziel:")
        self.kpi_wait_time.set_subtitle(
            f"{target_label} ≤ {wait_good:.0f} min"
        )
        
        # 6. Overtime
        overtime_sec = global_stats.get("overtime_seconds", 0.0)
        overtime_min = overtime_sec / 60.0
        overtime_status = "good" if overtime_min <= overtime_good else ("warning" if overtime_min <= overtime_warning else "critical")
        
        self.kpi_overtime.update_value(value=f"{overtime_min:.0f}", status=overtime_status)
        overtime_text = self._t("stats.low", "Niedrig") if overtime_min <= overtime_good else (self._t("stats.moderate", "Moderat") if overtime_min <= overtime_warning else self._t("stats.high", "Hoch"))
        self.kpi_overtime.set_subtitle(f"{self._t('stats.status', 'Status')}: {overtime_text}")
    
    def update_trend_chart(self, stats):
        """Update the trend analysis chart."""
        if not HAS_MATPLOTLIB:
            return
        
        self.trend_ax.clear()
        
        global_stats = stats.get("global", {})
        peak = global_stats.get("peak", {})
        hourly_data = peak.get("avg_customers_by_hour", {})
        
        if not hourly_data:
            self.trend_ax.text(
                0.5, 0.5,
                self._t("stats.no_data", "Noch keine Daten verfügbar"),
                transform=self.trend_ax.transAxes,
                ha="center", va="center",
                fontsize=12, color="#64748B"
            )
            self.trend_ax.set_axis_off()
            self.trend_canvas.draw_idle()
            return
        
        hours = sorted(hourly_data.keys())
        customers = [hourly_data[h] for h in hours]
        
        self.trend_ax.plot(hours, customers, marker='o', linewidth=2.5, markersize=6,
                          color='#3B82F6', markerfacecolor='#60A5FA', markeredgecolor='#3B82F6')
        self.trend_ax.fill_between(hours, customers, alpha=0.2, color='#3B82F6')
        
        if customers:
            peak_idx = customers.index(max(customers))
            peak_hour = hours[peak_idx]
            peak_value = customers[peak_idx]
            self.trend_ax.scatter([peak_hour], [peak_value], color='#EF4444', s=120, zorder=5,
                                 marker='*', edgecolors='#991B1B', linewidths=1.5)
        
        self.trend_ax.set_title(
            self._t("stats.trend_chart_title", "Kunden im Laden über Zeit"),
            fontsize=13, fontweight='bold', color='#1E293B', pad=10
        )
        
        # Format x-axis with simulation time instead of just hour number
        open_time = global_stats.get("open_time", "08:00")
        time_labels = [self._format_hour(h, open_time) for h in hours]
        self.trend_ax.set_xticks(hours)
        self.trend_ax.set_xticklabels(time_labels, rotation=45, ha='right')
        
        self.trend_ax.set_xlabel(
            self._t("stats.trend_chart_xlabel_time", "Simulationszeit"),
            fontsize=11, color='#475569'
        )
        self.trend_ax.set_ylabel(
            self._t("stats.trend_chart_ylabel", "Anzahl Kunden"),
            fontsize=11, color='#475569'
        )
        self.trend_ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
        self.trend_ax.spines['top'].set_visible(False)
        self.trend_ax.spines['right'].set_visible(False)
        
        self.trend_canvas.draw_idle()
        
        if customers:
            peak_time = self._format_hour(peak_hour, global_stats.get("open_time", "08:00"))
            self.lbl_peak_info.setText(f"Peak: {peak_time} ({peak_value:.1f} Kunden)")
    
    def update_recommendations(self, stats, settings=None):
        """Generate and display automated recommendations."""
        global_stats = stats.get("global", {})
        times = global_stats.get("times", {})
        
        # Get thresholds from settings or use defaults
        from config import DEFAULT_SETTINGS
        if settings is None:
            settings = DEFAULT_SETTINGS
        
        overtime_good = settings.get("kpi_overtime_good_max", 5.0)
        overtime_warning = settings.get("kpi_overtime_warning_max", 15.0)
        wait_good = settings.get("kpi_wait_time_good_max", 5.0)
        wait_warning = settings.get("kpi_wait_time_warning_max", 8.0)
        sat_good = settings.get("kpi_satisfaction_good_min", 75.0)
        sat_warning = settings.get("kpi_satisfaction_warning_min", 50.0)
        
        recommendations = []
        
        satisfaction = global_stats.get("satisfaction_score", 0.0)
        if satisfaction >= sat_good:
            recommendations.append(f"✅ {self._t('stats.satisfaction_green', 'Zufriedenheit im grünen Bereich')} ({satisfaction:.0f}%)")
        elif satisfaction >= sat_warning:
            recommendations.append(f"⚠️ {self._t('stats.satisfaction_acceptable', 'Zufriedenheit akzeptabel')} ({satisfaction:.0f}%) - {self._t('stats.satisfaction_improvement', 'Verbesserungspotenzial vorhanden')}")
        else:
            recommendations.append(f"🚨 {self._t('stats.satisfaction_critical', 'KRITISCH: Zufriedenheit sehr niedrig')} ({satisfaction:.0f}%) - {self._t('stats.satisfaction_action_required', 'Sofortmaßnahmen erforderlich!')}")
        
        wait_time = times.get("queue_wait_avg", 0.0) / 60.0
        if wait_time <= wait_good:
            recommendations.append(f"✅ {self._t('stats.wait_times_optimal', 'Wartezeiten optimal')} (Ø {wait_time:.1f} min)")
        elif wait_time <= wait_warning:
            recommendations.append(f"⚠️ {self._t('stats.wait_times_elevated', 'Wartezeiten erhöht')} (Ø {wait_time:.1f} min) - {self._t('stats.wait_times_open_checkout', 'Weitere Kasse öffnen?')}")
        else:
            recommendations.append(f"🚨 {self._t('stats.wait_times_too_high', 'Wartezeiten zu hoch')} (Ø {wait_time:.1f} min) - {self._t('stats.wait_times_urgent', 'Dringend mehr Kassen öffnen!')}")
        
        overtime_min = global_stats.get("overtime_seconds", 0.0) / 60.0
        if overtime_min > overtime_warning:
            recommendations.append(f"🚨 {self._t('stats.overtime_high', 'Hohe Überzeit')}: {overtime_min:.0f} {self._t('stats.unit_minutes', 'Minuten')} - {self._t('stats.overtime_check_schedule', 'Kassenöffnung/Schließung prüfen')}")
        elif overtime_min > overtime_good:
            recommendations.append(f"⚠️ {self._t('stats.overtime_moderate', 'Moderate Überzeit')}: {overtime_min:.0f} {self._t('stats.unit_minutes', 'Minuten')} - {self._t('stats.overtime_optimize', 'Planung optimieren')}")
        
        # Dynamische Durchsatz-Berechnung basierend auf Zielkunden und geplanten Öffnungszeiten
        customers_served = global_stats.get("total_customers_served", 0)
        target_customers = global_stats.get("target_customers", 50)
        elapsed_hours = global_stats.get("elapsed_sim_hours", 1.0)
        
        # Berechne Ziel-Durchsatz wie im KPI Dashboard
        scheduled_open_seconds = global_stats.get("scheduled_open_seconds", 28800.0)  # default 8h
        scheduled_open_hours = scheduled_open_seconds / 3600.0
        target_throughput = target_customers / max(scheduled_open_hours, 1.0)
        
        if elapsed_hours > 0:
            actual_throughput = customers_served / elapsed_hours
            throughput_ratio = actual_throughput / target_throughput if target_throughput > 0 else 0
            
            customers_h = self._t("stats.customers_per_hour", "Kunden/h")
            target_text = self._t("stats.target", "Ziel")
            
            if throughput_ratio >= 1.0:
                recommendations.append(f"✅{self._t('stats.throughput_optimal', 'Durchsatz optimal')}: {actual_throughput:.1f} {customers_h} ({target_text}: {target_throughput:.1f} {customers_h})")
            elif throughput_ratio >= 0.8:
                recommendations.append(f"✅{self._t('stats.throughput_good', 'Durchsatz gut')}: {actual_throughput:.1f} {customers_h} ({target_text}: {target_throughput:.1f} {customers_h})")
            elif throughput_ratio >= 0.6:
                recommendations.append(f"⚠️{self._t('stats.throughput_low', 'Durchsatz niedrig')}: {actual_throughput:.1f} {customers_h} - {self._t('stats.throughput_check_efficiency', 'Effizienz prüfen')} ({target_text}: {target_throughput:.1f} {customers_h})")
            else:
                recommendations.append(f"🚨{self._t('stats.throughput_critical', 'Durchsatz kritisch')}: {actual_throughput:.1f} {customers_h} - {self._t('stats.throughput_optimize_processes', 'Prozesse optimieren!')} ({target_text}: {target_throughput:.1f} {customers_h})")
        
        peak = global_stats.get("peak", {})
        peak_hour = peak.get("busiest_hour")
        if peak_hour is not None:
            peak_time = self._format_hour(peak_hour, global_stats.get("open_time", "08:00"))
            recommendations.append(f"ℹ️ {self._t('stats.peak_at', 'Peak um')} {peak_time} - {self._t('stats.peak_more_checkouts', 'Ggf. mehr Kassen zur Stoßzeit?')}")
        
        checkouts_stats = stats.get("checkouts", {})
        malfunction_count = sum(
            c.get("events", {}).get("malfunction_events", 0)
            for c in checkouts_stats.values()
        )
        if malfunction_count > 5:
            recommendations.append(f"🚨 {malfunction_count} {self._t('stats.checkout_malfunctions', 'Kassenstörungen')} - {self._t('stats.maintenance_required', 'Wartung erforderlich!')}")
        elif malfunction_count > 0:
            recommendations.append(f"ℹ️ {malfunction_count} {self._t('stats.malfunctions_recorded', 'Kassenstörungen erfasst')}")
        
        if recommendations:
            self.txt_recommendations.setPlainText("\n".join(recommendations))
        else:
            self.txt_recommendations.setPlainText(
                self._t("stats.no_recommendations", "Noch keine Empfehlungen verfügbar.")
            )
    
    def _format_hour(self, hour, open_time_str):
        """Format hour as time string."""
        from PyQt6.QtCore import QTime
        base = QTime.fromString(open_time_str, "HH:mm")
        if base.isValid():
            t = base.addSecs(int(hour) * 3600)
            return t.toString("HH:mm")
        return f"{int(hour):02d}:00"
    
    def _t(self, key, fallback):
        """Translate a key or return fallback."""
        if not self.translator:
            return fallback
        return self.translator.get(key, fallback)
